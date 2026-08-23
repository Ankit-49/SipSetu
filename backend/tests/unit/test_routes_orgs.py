"""Unit tests for organization management routes (Phase 6.1).

Covers:
  - Organization CRUD (create, list, get, update, delete)
  - Member management (add, list, update role, remove)
  - Organization-scoped jobs (list, create)
  - Team dashboard stats

These tests use their own fixtures that bypass the shared ``db_session``
fixture to avoid SQLite UUID rollback issues when the API route commits
data directly.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from werkzeug.security import generate_password_hash

from auth_middleware import create_token
from models import (
    Applicant,
    AuditLog,
    BulkScreenJob,
    Job,
    Notification,
    Organization,
    OrganizationMember,
    Ranking,
    RankingFeedback,
    Recruiter,
    Resume,
    Skill,
    User,
    db,
)

# ---------------------------------------------------------------------------
# Fixtures — these use ``app`` directly, not ``db_session``, to avoid
# the conftest rollback issue with SQLite UUID columns.
# ---------------------------------------------------------------------------

RECRUITER_EMAIL = "org_recruiter@example.com"
SECOND_EMAIL = "org_recruiter2@example.com"
APPLICANT_EMAIL = "org_applicant@example.com"


@pytest.fixture(autouse=True)
def _clean(app):
    """Ensure every test starts and ends with a clean org/user slate."""
    with app.app_context():
        _delete_all()
        yield
        _delete_all()


def _delete_all():
    """Remove all org-related rows to keep tests isolated."""
    AuditLog.query.delete(synchronize_session=False)
    RankingFeedback.query.delete(synchronize_session=False)
    Ranking.query.delete(synchronize_session=False)
    Notification.query.delete(synchronize_session=False)
    BulkScreenJob.query.delete(synchronize_session=False)
    Resume.query.delete(synchronize_session=False)
    OrganizationMember.query.delete(synchronize_session=False)
    Job.query.update({"organization_id": None}, synchronize_session=False)
    Organization.query.delete(synchronize_session=False)
    Skill.query.delete(synchronize_session=False)
    # Polymorphic delete: Recruiter/Applicant inherit from User,
    # so we must delete via the base class to avoid multi-table DELETE errors on SQLite
    for email in [RECRUITER_EMAIL, SECOND_EMAIL, APPLICANT_EMAIL]:
        user = User.query.filter_by(email=email).first()
        if user:
            db.session.delete(user)
    db.session.commit()


@pytest.fixture()
def test_recruiter_user(app):
    """Create a test recruiter (not from conftest — avoids db_session issues)."""
    with app.app_context():
        uid = uuid4()
        r = Recruiter(
            user_id=uid,
            email=RECRUITER_EMAIL,
            name="Test Recruiter",
            password_hash=generate_password_hash("password123"),
            role="recruiter",
            email_verified=True,
            company="Test Corp",
        )
        db.session.add(r)
        db.session.commit()
        # Store values before session expires the object
        return type("RecruiterData", (), {"user_id": uid, "role": "recruiter", "email": RECRUITER_EMAIL})()


@pytest.fixture()
def org_recruiter_headers(test_recruiter_user, app):
    with app.app_context():
        token = create_token(str(test_recruiter_user.user_id), test_recruiter_user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def second_recruiter_user(app):
    with app.app_context():
        uid = uuid4()
        r = Recruiter(
            user_id=uid,
            email=SECOND_EMAIL,
            name="Second Recruiter",
            password_hash=generate_password_hash("password123"),
            role="recruiter",
            email_verified=True,
            company="Other Corp",
        )
        db.session.add(r)
        db.session.commit()
        return type("RecruiterData", (), {"user_id": uid, "role": "recruiter", "email": SECOND_EMAIL})()


@pytest.fixture()
def second_recruiter_headers(second_recruiter_user, app):
    with app.app_context():
        token = create_token(str(second_recruiter_user.user_id), second_recruiter_user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def test_applicant_user(app):
    with app.app_context():
        uid = uuid4()
        a = Applicant(
            user_id=uid,
            email=APPLICANT_EMAIL,
            name="Test Applicant",
            password_hash=generate_password_hash("password123"),
            role="applicant",
            email_verified=True,
        )
        db.session.add(a)
        db.session.commit()
        return type("UserData", (), {"user_id": uid, "role": "applicant", "email": APPLICANT_EMAIL})()


@pytest.fixture()
def applicant_headers(test_applicant_user, app):
    with app.app_context():
        token = create_token(str(test_applicant_user.user_id), test_applicant_user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def test_org(app, test_recruiter_user):
    """Create a test organization with the recruiter as owner."""
    with app.app_context():
        org_id = uuid4()
        org = Organization(
            org_id=org_id,
            name="Test Org",
            slug="test-org",
            description="A test organization",
            industry="Technology",
            size="11-50",
        )
        db.session.add(org)
        db.session.flush()

        membership = OrganizationMember(
            membership_id=uuid4(),
            org_id=org_id,
            user_id=test_recruiter_user.user_id,
            role="owner",
            invited_by=test_recruiter_user.user_id,
        )
        db.session.add(membership)
        db.session.commit()
        return type("OrgData", (), {"org_id": org_id, "name": "Test Org", "slug": "test-org"})()


# ---------------------------------------------------------------------------
# Organization CRUD
# ---------------------------------------------------------------------------


class TestCreateOrganization:
    def test_create_org_success(self, client, org_recruiter_headers):
        resp = client.post(
            "/api/v1/organizations",
            json={"name": "Acme Corp", "slug": "acme", "industry": "Tech"},
            headers=org_recruiter_headers,
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["name"] == "Acme Corp"
        assert data["slug"] == "acme"
        assert data["org_id"]
        # Verify membership was created
        with client.application.app_context():
            count = OrganizationMember.query.filter_by(org_id=data["org_id"]).count()
            assert count == 1

    def test_create_org_missing_name(self, client, org_recruiter_headers):
        resp = client.post(
            "/api/v1/organizations",
            json={},
            headers=org_recruiter_headers,
        )
        assert resp.status_code == 400

    def test_create_org_duplicate_slug(self, client, org_recruiter_headers, test_org):
        resp = client.post(
            "/api/v1/organizations",
            json={"name": "Another", "slug": "test-org"},
            headers=org_recruiter_headers,
        )
        assert resp.status_code == 409

    def test_create_org_applicant_forbidden(self, client, applicant_headers):
        resp = client.post(
            "/api/v1/organizations",
            json={"name": "Bad Org", "slug": "bad"},
            headers=applicant_headers,
        )
        assert resp.status_code == 403

    def test_create_org_no_auth(self, client):
        resp = client.post("/api/v1/organizations", json={"name": "X"})
        assert resp.status_code == 401


class TestListOrganizations:
    def test_list_orgs(self, client, org_recruiter_headers, test_org):
        resp = client.get("/api/v1/organizations", headers=org_recruiter_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] >= 1
        slugs = [o["slug"] for o in data["organizations"]]
        assert "test-org" in slugs

    def test_list_orgs_empty(self, client, org_recruiter_headers):
        resp = client.get("/api/v1/organizations", headers=org_recruiter_headers)
        assert resp.status_code == 200
        assert resp.get_json()["total"] == 0


class TestGetOrganization:
    def test_get_org(self, client, org_recruiter_headers, test_org):
        resp = client.get(
            f"/api/v1/organizations/{test_org.org_id}", headers=org_recruiter_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["name"] == "Test Org"
        assert data["your_role"] == "owner"

    def test_get_org_not_member(self, client, second_recruiter_headers, test_org):
        resp = client.get(
            f"/api/v1/organizations/{test_org.org_id}", headers=second_recruiter_headers
        )
        assert resp.status_code == 403

    def test_get_org_not_found(self, client, org_recruiter_headers):
        resp = client.get(
            f"/api/v1/organizations/{uuid4()}", headers=org_recruiter_headers
        )
        assert resp.status_code == 404


class TestUpdateOrganization:
    def test_update_org(self, client, org_recruiter_headers, test_org):
        resp = client.put(
            f"/api/v1/organizations/{test_org.org_id}",
            json={"name": "Updated Org", "description": "New desc"},
            headers=org_recruiter_headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["name"] == "Updated Org"

    def test_update_org_non_admin(self, client, second_recruiter_headers, test_org, second_recruiter_user, app):
        with app.app_context():
            db.session.add(OrganizationMember(
                membership_id=uuid4(),
                org_id=test_org.org_id,
                user_id=second_recruiter_user.user_id,
                role="viewer",
            ))
            db.session.commit()

        resp = client.put(
            f"/api/v1/organizations/{test_org.org_id}",
            json={"name": "Hacked"},
            headers=second_recruiter_headers,
        )
        assert resp.status_code == 403

    def test_update_org_not_found(self, client, org_recruiter_headers):
        resp = client.put(
            f"/api/v1/organizations/{uuid4()}",
            json={"name": "X"},
            headers=org_recruiter_headers,
        )
        assert resp.status_code == 404


class TestDeleteOrganization:
    def test_delete_org_owner(self, client, org_recruiter_headers, test_org, app):
        resp = client.delete(
            f"/api/v1/organizations/{test_org.org_id}", headers=org_recruiter_headers
        )
        assert resp.status_code == 200
        with app.app_context():
            assert Organization.query.get(test_org.org_id) is None

    def test_delete_org_non_owner(self, client, second_recruiter_headers, test_org, second_recruiter_user, app):
        with app.app_context():
            db.session.add(OrganizationMember(
                membership_id=uuid4(),
                org_id=test_org.org_id,
                user_id=second_recruiter_user.user_id,
                role="admin",
            ))
            db.session.commit()

        resp = client.delete(
            f"/api/v1/organizations/{test_org.org_id}",
            headers=second_recruiter_headers,
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Member management
# ---------------------------------------------------------------------------


class TestListMembers:
    def test_list_members(self, client, org_recruiter_headers, test_org):
        resp = client.get(
            f"/api/v1/organizations/{test_org.org_id}/members", headers=org_recruiter_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] >= 1
        roles = [m["role"] for m in data["members"]]
        assert "owner" in roles


class TestAddMember:
    def test_add_member(self, client, org_recruiter_headers, test_org, second_recruiter_user):
        resp = client.post(
            f"/api/v1/organizations/{test_org.org_id}/members",
            json={"user_id": str(second_recruiter_user.user_id), "role": "admin"},
            headers=org_recruiter_headers,
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["role"] == "admin"
        assert data["email"] == SECOND_EMAIL

    def test_add_member_invalid_role(self, client, org_recruiter_headers, test_org, second_recruiter_user):
        resp = client.post(
            f"/api/v1/organizations/{test_org.org_id}/members",
            json={"user_id": str(second_recruiter_user.user_id), "role": "superadmin"},
            headers=org_recruiter_headers,
        )
        assert resp.status_code == 400

    def test_add_member_duplicate(self, client, org_recruiter_headers, test_org, second_recruiter_user, app):
        with app.app_context():
            db.session.add(OrganizationMember(
                membership_id=uuid4(),
                org_id=test_org.org_id,
                user_id=second_recruiter_user.user_id,
                role="viewer",
            ))
            db.session.commit()

        resp = client.post(
            f"/api/v1/organizations/{test_org.org_id}/members",
            json={"user_id": str(second_recruiter_user.user_id), "role": "admin"},
            headers=org_recruiter_headers,
        )
        assert resp.status_code == 409

    def test_add_member_applicant_rejected(self, client, org_recruiter_headers, test_org, test_applicant_user):
        resp = client.post(
            f"/api/v1/organizations/{test_org.org_id}/members",
            json={"user_id": str(test_applicant_user.user_id), "role": "viewer"},
            headers=org_recruiter_headers,
        )
        assert resp.status_code == 400

    def test_add_member_missing_user_id(self, client, org_recruiter_headers, test_org):
        resp = client.post(
            f"/api/v1/organizations/{test_org.org_id}/members",
            json={"role": "viewer"},
            headers=org_recruiter_headers,
        )
        assert resp.status_code == 400


class TestRemoveMember:
    def test_remove_member(self, client, org_recruiter_headers, test_org, second_recruiter_user, app):
        with app.app_context():
            m = OrganizationMember(
                membership_id=uuid4(),
                org_id=test_org.org_id,
                user_id=second_recruiter_user.user_id,
                role="viewer",
            )
            db.session.add(m)
            db.session.commit()
            mid = str(m.membership_id)

        resp = client.delete(
            f"/api/v1/organizations/{test_org.org_id}/members/{mid}",
            headers=org_recruiter_headers,
        )
        assert resp.status_code == 200
        with app.app_context():
            assert db.session.get(OrganizationMember, m.membership_id) is None


class TestUpdateMemberRole:
    def test_update_role(self, client, org_recruiter_headers, test_org, second_recruiter_user, app):
        with app.app_context():
            m = OrganizationMember(
                membership_id=uuid4(),
                org_id=test_org.org_id,
                user_id=second_recruiter_user.user_id,
                role="viewer",
            )
            db.session.add(m)
            db.session.commit()
            mid = str(m.membership_id)

        resp = client.put(
            f"/api/v1/organizations/{test_org.org_id}/members/{mid}",
            json={"role": "hiring_manager"},
            headers=org_recruiter_headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["role"] == "hiring_manager"

    def test_update_role_invalid(self, client, org_recruiter_headers, test_org, second_recruiter_user, app):
        with app.app_context():
            m = OrganizationMember(
                membership_id=uuid4(),
                org_id=test_org.org_id,
                user_id=second_recruiter_user.user_id,
                role="viewer",
            )
            db.session.add(m)
            db.session.commit()
            mid = str(m.membership_id)

        resp = client.put(
            f"/api/v1/organizations/{test_org.org_id}/members/{mid}",
            json={"role": "superadmin"},
            headers=org_recruiter_headers,
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Org-scoped jobs
# ---------------------------------------------------------------------------


class TestOrgJobs:
    def test_list_org_jobs_empty(self, client, org_recruiter_headers, test_org):
        resp = client.get(
            f"/api/v1/organizations/{test_org.org_id}/jobs", headers=org_recruiter_headers
        )
        assert resp.status_code == 200
        assert resp.get_json()["total"] == 0

    def test_create_org_job(self, client, org_recruiter_headers, test_org):
        resp = client.post(
            f"/api/v1/organizations/{test_org.org_id}/jobs",
            json={
                "title": "Org Engineer",
                "skills": ["python", "react"],
                "job_type": "full-time",
            },
            headers=org_recruiter_headers,
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["title"] == "Org Engineer"
        assert data["organization_id"] == str(test_org.org_id)

        # Verify job appears in org jobs list
        resp2 = client.get(
            f"/api/v1/organizations/{test_org.org_id}/jobs", headers=org_recruiter_headers
        )
        assert resp2.get_json()["total"] >= 1

    def test_create_org_job_viewer_forbidden(self, client, test_org, second_recruiter_user, app):
        """Viewer role cannot post jobs."""
        with app.app_context():
            db.session.add(OrganizationMember(
                membership_id=uuid4(),
                org_id=test_org.org_id,
                user_id=second_recruiter_user.user_id,
                role="viewer",
            ))
            db.session.commit()

        token = create_token(str(second_recruiter_user.user_id), second_recruiter_user.role)
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.post(
            f"/api/v1/organizations/{test_org.org_id}/jobs",
            json={"title": "Should Fail"},
            headers=headers,
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Team dashboard
# ---------------------------------------------------------------------------


class TestOrgDashboard:
    def test_dashboard_stats(self, client, org_recruiter_headers, test_org):
        resp = client.get(
            f"/api/v1/organizations/{test_org.org_id}/dashboard", headers=org_recruiter_headers
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total_members"] >= 1
        assert data["total_jobs"] >= 0
        assert "total_applications" in data
        assert "avg_match_score" in data

    def test_dashboard_non_member(self, client, second_recruiter_headers, test_org):
        resp = client.get(
            f"/api/v1/organizations/{test_org.org_id}/dashboard",
            headers=second_recruiter_headers,
        )
        assert resp.status_code == 403
