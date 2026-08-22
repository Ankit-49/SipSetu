"""Unit tests for Phase 5 routes.

Covers:
  5.1 — LLM resume parsing (parse, get parsed)
  5.2 — Recruiter feedback (submit feedback, feedback summary)
  5.3 — Notifications (unread count)
  5.4 — Admin dashboard (stats, users, suspend, jobs, delete, audit logs)
"""

from __future__ import annotations

import json
from unittest.mock import patch
from uuid import uuid4

import pytest
from werkzeug.security import generate_password_hash

from models import (
    Applicant,
    AuditLog,
    Job,
    JobApplication,
    Notification,
    Ranking,
    RankingFeedback,
    Recruiter,
    Resume,
    Skill,
    User,
    db,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

ADMIN_EMAIL = "admin@example.com"


@pytest.fixture(autouse=True)
def _set_admin_emails(monkeypatch):
    """Ensure the admin email is configured for all Phase 5 tests."""
    monkeypatch.setattr("config.settings.ADMIN_EMAILS", ADMIN_EMAIL)


@pytest.fixture()
def admin_user(db_session):
    """Create an admin user whose email is in ADMIN_EMAILS."""
    admin = Applicant(
        user_id=uuid4(),
        email=ADMIN_EMAIL,
        name="Admin User",
        password_hash=generate_password_hash("admin123"),
        role="applicant",
        email_verified=True,
    )
    db_session.add(admin)
    db_session.commit()
    yield admin
    db_session.delete(admin)
    db_session.commit()


@pytest.fixture()
def admin_headers(admin_user):
    from auth_middleware import create_token
    token = create_token(str(admin_user.user_id), admin_user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def ranking(db_session, test_job, test_resume):
    """Create a ranking linking the test job and resume."""
    r = Ranking(
        ranking_id=uuid4(),
        job_id=test_job.job_id,
        resume_id=test_resume.resume_id,
        matching_score=85.0,
        candidate_rank=1,
    )
    db_session.add(r)
    db_session.commit()
    return r


@pytest.fixture()
def notification(db_session, test_user):
    """Create an unread notification for the test user."""
    n = Notification(
        notification_id=uuid4(),
        user_id=test_user.user_id,
        title="Test",
        message="You have an update",
        type="info",
        is_read=False,
    )
    db_session.add(n)
    db_session.commit()
    return n


# ===========================================================================
# 5.1 — LLM Resume Parsing
# ===========================================================================


class TestParseResume:
    """POST /resumes/<id>/parse"""

    def test_parse_resume_success(self, client, auth_headers, test_resume):
        """Parsing returns structured sections with regex fallback."""
        resp = client.post(
            f"/api/resumes/{test_resume.resume_id}/parse",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "sections" in data
        assert "confidence" in data
        assert data["extraction_method"] == "regex"  # No LLM key in test env
        assert isinstance(data["sections"], dict)

    def test_parse_resume_not_found(self, client, auth_headers):
        resp = client.post(
            f"/api/resumes/{uuid4()}/parse",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_parse_resume_wrong_owner(self, client, auth_headers, test_resume, db_session):
        """Users cannot parse resumes they don't own."""
        other = Applicant(
            user_id=uuid4(),
            email="other@example.com",
            name="Other",
            password_hash=generate_password_hash("pw"),
            role="applicant",
        )
        db_session.add(other)
        db_session.commit()

        from auth_middleware import create_token
        token = create_token(str(other.user_id), other.role)
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.post(
            f"/api/resumes/{test_resume.resume_id}/parse",
            headers=headers,
        )
        assert resp.status_code == 403

    def test_parse_resume_no_auth(self, client, test_resume):
        resp = client.post(f"/api/resumes/{test_resume.resume_id}/parse")
        assert resp.status_code == 401

    def test_parse_resume_persists_sections(self, client, auth_headers, test_resume):
        """After parsing, the parsed_sections are stored on the resume."""
        client.post(
            f"/api/resumes/{test_resume.resume_id}/parse",
            headers=auth_headers,
        )
        from models import Resume as ResumeModel
        updated = ResumeModel.query.get(test_resume.resume_id)
        assert updated.parsed_sections is not None
        assert updated.parse_confidence is not None
        assert updated.parse_method == "regex"


class TestGetParsedSections:
    """GET /resumes/<id>/parsed"""

    def test_get_parsed_returns_cached(self, client, auth_headers, test_resume):
        """Getting parsed sections returns previously parsed data."""
        # First parse
        client.post(
            f"/api/resumes/{test_resume.resume_id}/parse",
            headers=auth_headers,
        )
        # Then retrieve
        resp = client.get(
            f"/api/resumes/{test_resume.resume_id}/parsed",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "sections" in data
        assert isinstance(data["sections"], dict)

    def test_get_parsed_empty_when_not_parsed(self, client, auth_headers, test_resume):
        """If resume hasn't been parsed yet, sections is empty."""
        resp = client.get(
            f"/api/resumes/{test_resume.resume_id}/parsed",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["sections"] == {}

    def test_get_parsed_not_found(self, client, auth_headers):
        resp = client.get(
            f"/api/resumes/{uuid4()}/parsed",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_get_parsed_wrong_owner(self, client, auth_headers, test_resume, db_session):
        other = Applicant(
            user_id=uuid4(),
            email="other2@example.com",
            name="Other",
            password_hash=generate_password_hash("pw"),
            role="applicant",
        )
        db_session.add(other)
        db_session.commit()

        from auth_middleware import create_token
        token = create_token(str(other.user_id), other.role)
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.get(
            f"/api/resumes/{test_resume.resume_id}/parsed",
            headers=headers,
        )
        assert resp.status_code == 403


# ===========================================================================
# 5.2 — Recruiter Feedback Loop
# ===========================================================================


class TestSubmitRankingFeedback:
    """POST /rankings/<id>/feedback"""

    def test_submit_feedback_higher(self, client, recruiter_auth_headers, ranking):
        resp = client.post(
            f"/api/rankings/{ranking.ranking_id}/feedback",
            headers=recruiter_auth_headers,
            json={"direction": "higher", "note": "Great candidate"},
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["direction"] == "higher"
        assert data["message"] == "Feedback recorded"

    def test_submit_feedback_lower(self, client, recruiter_auth_headers, ranking):
        resp = client.post(
            f"/api/rankings/{ranking.ranking_id}/feedback",
            headers=recruiter_auth_headers,
            json={"direction": "lower"},
            content_type="application/json",
        )
        assert resp.status_code == 200

    def test_submit_feedback_correct(self, client, recruiter_auth_headers, ranking):
        resp = client.post(
            f"/api/rankings/{ranking.ranking_id}/feedback",
            headers=recruiter_auth_headers,
            json={"direction": "correct"},
            content_type="application/json",
        )
        assert resp.status_code == 200

    def test_submit_feedback_invalid_direction(self, client, recruiter_auth_headers, ranking):
        resp = client.post(
            f"/api/rankings/{ranking.ranking_id}/feedback",
            headers=recruiter_auth_headers,
            json={"direction": "invalid"},
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_submit_feedback_upsert(self, client, recruiter_auth_headers, ranking):
        """Submitting feedback twice updates (upserts) the existing entry."""
        client.post(
            f"/api/rankings/{ranking.ranking_id}/feedback",
            headers=recruiter_auth_headers,
            json={"direction": "higher"},
            content_type="application/json",
        )
        resp = client.post(
            f"/api/rankings/{ranking.ranking_id}/feedback",
            headers=recruiter_auth_headers,
            json={"direction": "lower"},
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["direction"] == "lower"

    def test_submit_feedback_ranking_not_found(self, client, recruiter_auth_headers):
        resp = client.post(
            f"/api/rankings/{uuid4()}/feedback",
            headers=recruiter_auth_headers,
            json={"direction": "higher"},
            content_type="application/json",
        )
        assert resp.status_code == 404

    def test_submit_feedback_creates_audit_log(self, client, recruiter_auth_headers, ranking):
        client.post(
            f"/api/rankings/{ranking.ranking_id}/feedback",
            headers=recruiter_auth_headers,
            json={"direction": "correct"},
            content_type="application/json",
        )
        from auth_middleware import create_token
        from config import settings
        log = AuditLog.query.filter_by(action="ranking_feedback").first()
        assert log is not None


class TestFeedbackSummary:
    """GET /jobs/<id>/feedback-summary"""

    def test_feedback_summary_empty(self, client, recruiter_auth_headers, test_job):
        resp = client.get(
            f"/api/jobs/{test_job.job_id}/feedback-summary",
            headers=recruiter_auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["summary"]["total"] == 0
        assert data["feedbacks"] == []

    def test_feedback_summary_with_data(
        self, client, recruiter_auth_headers, ranking
    ):
        # Submit feedback first
        client.post(
            f"/api/rankings/{ranking.ranking_id}/feedback",
            headers=recruiter_auth_headers,
            json={"direction": "higher", "note": "Strong profile"},
            content_type="application/json",
        )
        resp = client.get(
            f"/api/jobs/{ranking.job_id}/feedback-summary",
            headers=recruiter_auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["summary"]["higher"] == 1
        assert data["summary"]["total"] == 1
        assert len(data["feedbacks"]) == 1
        assert data["feedbacks"][0]["direction"] == "higher"

    def test_feedback_summary_job_not_found(self, client, recruiter_auth_headers):
        resp = client.get(
            f"/api/jobs/{uuid4()}/feedback-summary",
            headers=recruiter_auth_headers,
        )
        assert resp.status_code == 404

    def test_feedback_summary_wrong_recruiter(
        self, client, auth_headers, test_job
    ):
        """Applicant cannot access another recruiter's feedback summary."""
        resp = client.get(
            f"/api/jobs/{test_job.job_id}/feedback-summary",
            headers=auth_headers,
        )
        assert resp.status_code == 403


# ===========================================================================
# 5.3 — Notifications (Unread Count)
# ===========================================================================


class TestUnreadCount:
    """GET /notifications/<user_id>/unread-count"""

    def test_unread_count_returns_number(self, client, auth_headers, notification):
        resp = client.get(
            f"/api/notifications/{notification.user_id}/unread-count",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["unread_count"] >= 1

    def test_unread_count_zero(self, client, auth_headers, test_user):
        resp = client.get(
            f"/api/notifications/{test_user.user_id}/unread-count",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["unread_count"] == 0

    def test_unread_count_wrong_user(self, client, auth_headers, test_user):
        """Users cannot query another user's unread count."""
        other_id = uuid4()
        resp = client.get(
            f"/api/notifications/{other_id}/unread-count",
            headers=auth_headers,
        )
        assert resp.status_code == 403

    def test_unread_count_no_auth(self, client):
        resp = client.get(f"/api/notifications/{uuid4()}/unread-count")
        assert resp.status_code == 401


# ===========================================================================
# 5.4 — Admin Dashboard
# ===========================================================================


class TestAdminStats:
    """GET /admin/stats"""

    def test_admin_stats_returns_data(self, client, admin_headers):
        resp = client.get("/api/admin/stats", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "users" in data
        assert "jobs" in data
        assert "applications" in data
        assert "system" in data
        assert data["system"]["database"] == "ok"

    def test_admin_stats_counts(self, client, admin_headers, test_user, test_job, test_resume):
        resp = client.get("/api/admin/stats", headers=admin_headers)
        data = resp.get_json()
        assert data["users"]["total"] >= 1
        assert data["jobs"]["total"] >= 1
        assert data["resumes"]["total"] >= 1

    def test_admin_stats_non_admin(self, client, auth_headers):
        resp = client.get("/api/admin/stats", headers=auth_headers)
        assert resp.status_code == 403

    def test_admin_stats_no_auth(self, client):
        resp = client.get("/api/admin/stats")
        assert resp.status_code == 401


class TestAdminListUsers:
    """GET /admin/users"""

    def test_list_users(self, client, admin_headers, test_user, test_recruiter):
        resp = client.get("/api/admin/users", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] >= 2
        assert len(data["users"]) >= 2

    def test_list_users_search(self, client, admin_headers, test_user):
        resp = client.get(
            "/api/admin/users",
            headers=admin_headers,
            query_string={"search": "test"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] >= 1

    def test_list_users_filter_role(self, client, admin_headers, test_user, test_recruiter):
        resp = client.get(
            "/api/admin/users",
            headers=admin_headers,
            query_string={"role": "recruiter"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] >= 1
        for u in data["users"]:
            assert u["role"] == "recruiter"

    def test_list_users_non_admin(self, client, auth_headers):
        resp = client.get("/api/admin/users", headers=auth_headers)
        assert resp.status_code == 403


class TestAdminSuspendUser:
    """PATCH /admin/users/<id>/suspend"""

    def test_suspend_user(self, client, admin_headers, test_user):
        resp = client.patch(
            f"/api/admin/users/{test_user.user_id}/suspend",
            headers=admin_headers,
            json={"suspend": True},
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["email_verified"] is False

    def test_unsuspend_user(self, client, admin_headers, test_user):
        # Suspend first
        client.patch(
            f"/api/admin/users/{test_user.user_id}/suspend",
            headers=admin_headers,
            json={"suspend": True},
            content_type="application/json",
        )
        # Then unsuspend
        resp = client.patch(
            f"/api/admin/users/{test_user.user_id}/suspend",
            headers=admin_headers,
            json={"suspend": False},
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["email_verified"] is True

    def test_suspend_creates_audit_log(self, client, admin_headers, test_user):
        client.patch(
            f"/api/admin/users/{test_user.user_id}/suspend",
            headers=admin_headers,
            json={"suspend": True},
            content_type="application/json",
        )
        log = AuditLog.query.filter_by(action="user_suspend").first()
        assert log is not None

    def test_suspend_user_not_found(self, client, admin_headers):
        resp = client.patch(
            f"/api/admin/users/{uuid4()}/suspend",
            headers=admin_headers,
            json={"suspend": True},
            content_type="application/json",
        )
        assert resp.status_code == 404

    def test_suspend_non_admin(self, client, auth_headers, test_user):
        resp = client.patch(
            f"/api/admin/users/{test_user.user_id}/suspend",
            headers=auth_headers,
            json={"suspend": True},
            content_type="application/json",
        )
        assert resp.status_code == 403


class TestAdminListJobs:
    """GET /admin/jobs"""

    def test_list_jobs(self, client, admin_headers, test_job):
        resp = client.get("/api/admin/jobs", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] >= 1
        job = data["jobs"][0]
        assert "title" in job
        assert "recruiter_name" in job
        assert "application_count" in job

    def test_list_jobs_search(self, client, admin_headers, test_job):
        resp = client.get(
            "/api/admin/jobs",
            headers=admin_headers,
            query_string={"search": "Software"},
        )
        assert resp.status_code == 200
        assert resp.get_json()["total"] >= 1

    def test_list_jobs_non_admin(self, client, auth_headers):
        resp = client.get("/api/admin/jobs", headers=auth_headers)
        assert resp.status_code == 403


class TestAdminDeleteJob:
    """DELETE /admin/jobs/<id>"""

    def test_delete_job(self, client, admin_headers, db_session, test_recruiter):
        """Admin can delete any job."""
        job = Job(
            job_id=uuid4(),
            recruiter_id=test_recruiter.user_id,
            title="To Be Deleted",
            description="Temporary job",
        )
        db_session.add(job)
        db_session.commit()

        resp = client.delete(
            f"/api/admin/jobs/{job.job_id}",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert "deleted" in resp.get_json()["message"].lower()

    def test_delete_job_creates_audit_log(self, client, admin_headers, db_session, test_recruiter):
        job = Job(
            job_id=uuid4(),
            recruiter_id=test_recruiter.user_id,
            title="Audit Test Job",
            description="Will be deleted",
        )
        db_session.add(job)
        db_session.commit()
        job_id = str(job.job_id)

        client.delete(f"/api/admin/jobs/{job_id}", headers=admin_headers)
        log = AuditLog.query.filter_by(action="admin_delete_job").first()
        assert log is not None
        assert log.target_id == job_id

    def test_delete_job_notifies_recruiter(
        self, client, admin_headers, db_session, test_recruiter
    ):
        job = Job(
            job_id=uuid4(),
            recruiter_id=test_recruiter.user_id,
            title="Notify Test Job",
            description="Delete me",
        )
        db_session.add(job)
        db_session.commit()

        client.delete(f"/api/admin/jobs/{job.job_id}", headers=admin_headers)
        notif = Notification.query.filter_by(
            user_id=test_recruiter.user_id,
            title="Job Removed by Admin",
        ).first()
        assert notif is not None

    def test_delete_job_not_found(self, client, admin_headers):
        resp = client.delete(
            f"/api/admin/jobs/{uuid4()}",
            headers=admin_headers,
        )
        assert resp.status_code == 404

    def test_delete_job_non_admin(self, client, auth_headers, test_job):
        resp = client.delete(
            f"/api/admin/jobs/{test_job.job_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestAdminAuditLogs:
    """GET /admin/audit-logs"""

    def test_audit_logs_empty(self, client, admin_headers):
        resp = client.get("/api/admin/audit-logs", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "logs" in data
        assert "total" in data

    def test_audit_logs_with_data(self, client, admin_headers, test_user, admin_user):
        """After a suspend action, the audit log should appear."""
        client.patch(
            f"/api/admin/users/{test_user.user_id}/suspend",
            headers=admin_headers,
            json={"suspend": True},
            content_type="application/json",
        )
        resp = client.get("/api/admin/audit-logs", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] >= 1

    def test_audit_logs_filter_by_action(self, client, admin_headers, test_user):
        client.patch(
            f"/api/admin/users/{test_user.user_id}/suspend",
            headers=admin_headers,
            json={"suspend": True},
            content_type="application/json",
        )
        resp = client.get(
            "/api/admin/audit-logs",
            headers=admin_headers,
            query_string={"action": "user_suspend"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] >= 1
        for log in data["logs"]:
            assert log["action"] == "user_suspend"

    def test_audit_logs_non_admin(self, client, auth_headers):
        resp = client.get("/api/admin/audit-logs", headers=auth_headers)
        assert resp.status_code == 403
