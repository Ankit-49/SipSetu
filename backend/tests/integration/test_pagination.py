"""Integration tests for Phase 4.2: {data, meta} envelope + cursor pagination.

The new envelope and cursor pagination apply to the canonical /api/v1 prefix;
the legacy /api prefix keeps its historical response shapes.
"""

from datetime import datetime, timedelta

from models import Job, Notification


def _make_jobs(db_session, test_recruiter, n=5):
    base = datetime.utcnow() - timedelta(days=10)
    jobs = []
    for i in range(n):
        job = Job(
            recruiter_id=test_recruiter.user_id,
            title=f"Cursor Job {i:02d}",
            description=f"desc {i}",
            location="Remote",
            job_type="full-time",
            experience_level="3-5",
            salary_min=50000,
            salary_max=90000,
            created_at=base + timedelta(minutes=i),
        )
        db_session.add(job)
        jobs.append(job)
    db_session.flush()
    return jobs


class TestJobsEnvelope:
    def test_v1_jobs_returns_envelope(self, client, test_job):
        response = client.get("/api/v1/jobs")
        assert response.status_code == 200
        body = response.get_json()
        assert isinstance(body["data"], list)
        assert len(body["data"]) >= 1
        pagination = body["meta"]["pagination"]
        assert "total" in pagination
        assert "limit" in pagination
        assert "has_more" in pagination
        assert "next_cursor" in pagination
        assert body["data"][0]["job_id"]

    def test_legacy_jobs_shape_unchanged(self, client, test_job):
        response = client.get("/api/jobs")
        assert response.status_code == 200
        body = response.get_json()
        assert "jobs" in body
        assert "page" in body
        assert "per_page" in body
        assert "pages" in body
        assert "total" in body

    def test_v1_jobs_respects_limit(self, client, test_job):
        response = client.get("/api/v1/jobs?limit=1")
        body = response.get_json()
        assert len(body["data"]) <= 1
        assert body["meta"]["pagination"]["limit"] == 1

    def test_v1_jobs_cursor_roundtrip(self, client, db_session, test_recruiter):
        _make_jobs(db_session, test_recruiter, n=5)
        seen_ids = []
        cursor = None
        pages = 0
        while True:
            url = "/api/v1/jobs?limit=2"
            if cursor:
                url += f"&cursor={cursor}"
            response = client.get(url)
            assert response.status_code == 200
            body = response.get_json()
            page_ids = [j["job_id"] for j in body["data"]]
            # No overlap between pages
            assert not set(page_ids) & set(seen_ids)
            seen_ids.extend(page_ids)
            pagination = body["meta"]["pagination"]
            pages += 1
            if not pagination["has_more"]:
                assert pagination["next_cursor"] is None
                break
            assert pagination["next_cursor"]
            cursor = pagination["next_cursor"]
            assert pages < 10, "cursor pagination did not terminate"
        assert len(seen_ids) >= 5
        assert pages >= 3

    def test_v1_jobs_sort_title(self, client, db_session, test_recruiter):
        _make_jobs(db_session, test_recruiter, n=3)
        response = client.get("/api/v1/jobs?sort=title&limit=100")
        body = response.get_json()
        titles = [j["title"] for j in body["data"] if j["title"].startswith("Cursor Job")]
        assert titles == sorted(titles)

    def test_v1_jobs_sort_desc_created_at_default(self, client, db_session, test_recruiter):
        _make_jobs(db_session, test_recruiter, n=3)
        response = client.get("/api/v1/jobs?limit=100")
        body = response.get_json()
        cursor_jobs = [j for j in body["data"] if j["title"].startswith("Cursor Job")]
        created = [j["created_at"] for j in cursor_jobs]
        assert created == sorted(created, reverse=True)


class TestEnvelopeOnOtherLists:
    def test_v1_notifications_envelope(self, client, auth_headers, db_session, test_user):
        db_session.add(Notification(
            user_id=test_user.user_id,
            title="Hello",
            message="World",
            type="info",
        ))
        db_session.commit()
        response = client.get(
            f"/api/v1/notifications/{test_user.user_id}", headers=auth_headers
        )
        assert response.status_code == 200
        body = response.get_json()
        assert isinstance(body["data"], list)
        assert body["meta"]["pagination"]["total"] >= 1
        assert body["data"][0]["title"] == "Hello"

    def test_legacy_notifications_bare_array(self, client, auth_headers, db_session, test_user):
        db_session.add(Notification(
            user_id=test_user.user_id,
            title="Legacy",
            message="Array",
            type="info",
        ))
        db_session.commit()
        response = client.get(
            f"/api/notifications/{test_user.user_id}", headers=auth_headers
        )
        assert response.status_code == 200
        body = response.get_json()
        assert isinstance(body, list)

    def test_v1_applications_envelope(self, client, auth_headers, test_user, test_job, test_resume):
        client.post(f"/api/jobs/{test_job.job_id}/apply", headers=auth_headers)
        response = client.get(f"/api/v1/applicants/{test_user.user_id}/applications", headers=auth_headers)
        assert response.status_code == 200
        body = response.get_json()
        assert isinstance(body["data"], list)
        assert body["meta"]["applicant_id"] == str(test_user.user_id)

    def test_v1_matched_jobs_envelope(self, client, auth_headers, test_user, test_job, test_resume):
        response = client.get(f"/api/v1/applicants/{test_user.user_id}/matched-jobs", headers=auth_headers)
        assert response.status_code == 200
        body = response.get_json()
        assert isinstance(body["data"], list)
        assert body["meta"]["resume_id"] == str(test_resume.resume_id)
        assert "pagination" in body["meta"]

    def test_v1_saved_jobs_envelope(self, client, auth_headers, test_user, test_job):
        client.post(f"/api/jobs/{test_job.job_id}/save", headers=auth_headers)
        response = client.get(f"/api/v1/applicants/{test_user.user_id}/saved-jobs", headers=auth_headers)
        assert response.status_code == 200
        body = response.get_json()
        assert isinstance(body["data"], list)
        assert len(body["data"]) >= 1

    def test_v1_saved_job_ids_envelope(self, client, auth_headers, test_user, test_job):
        client.post(f"/api/jobs/{test_job.job_id}/save", headers=auth_headers)
        response = client.get(f"/api/v1/applicants/{test_user.user_id}/saved-job-ids", headers=auth_headers)
        assert response.status_code == 200
        body = response.get_json()
        assert isinstance(body["data"], list)
        assert str(test_job.job_id) in body["data"]

    def test_v1_resumes_envelope(self, client, auth_headers, test_user, test_resume):
        response = client.get("/api/v1/resumes", headers=auth_headers)
        assert response.status_code == 200
        body = response.get_json()
        assert isinstance(body["data"], list)
        assert body["meta"]["pagination"]["total"] >= 1

    def test_v1_interviews_envelope(self, client, auth_headers, test_user):
        response = client.get(f"/api/v1/interviews/{test_user.user_id}", headers=auth_headers)
        assert response.status_code == 200
        body = response.get_json()
        assert isinstance(body["data"], list)


class TestCandidatesEnvelope:
    def test_v1_recruiter_candidates_envelope(self, client, recruiter_auth_headers,
                                              test_recruiter, test_job, test_resume):
        # Apply to create a ranking, then fetch candidates on v1.
        from flask import current_app
        from models import JobApplication, db
        with current_app.app_context():
            application = JobApplication(
                job_id=test_job.job_id,
                applicant_id=test_resume.applicant_id,
            )
            db.session.add(application)
            db.session.commit()

        response = client.get(
            f"/api/v1/recruiters/{test_recruiter.user_id}/candidates",
            headers=recruiter_auth_headers,
        )
        assert response.status_code == 200
        body = response.get_json()
        assert isinstance(body["data"], list)
        assert isinstance(body["meta"]["jobs"], list)
        assert body["meta"]["recruiter_id"] == str(test_recruiter.user_id)
        assert "pagination" in body["meta"]

    def test_legacy_recruiter_candidates_shape(self, client, recruiter_auth_headers,
                                              test_recruiter, test_job, test_resume):
        response = client.get(
            f"/api/recruiters/{test_recruiter.user_id}/candidates",
            headers=recruiter_auth_headers,
        )
        assert response.status_code == 200
        body = response.get_json()
        assert "candidates" in body
        assert "jobs" in body
        assert "page" in body

    def test_v1_job_candidates_envelope(self, client, recruiter_auth_headers,
                                        test_recruiter, test_job, test_resume):
        from flask import current_app
        from models import JobApplication, db
        with current_app.app_context():
            application = JobApplication(
                job_id=test_job.job_id,
                applicant_id=test_resume.applicant_id,
            )
            db.session.add(application)
            db.session.commit()

        response = client.get(
            f"/api/v1/jobs/{test_job.job_id}/candidates",
            headers=recruiter_auth_headers,
        )
        assert response.status_code == 200
        body = response.get_json()
        assert isinstance(body["data"], list)
        assert body["meta"]["job_id"] == str(test_job.job_id)
