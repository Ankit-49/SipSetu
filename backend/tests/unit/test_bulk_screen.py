"""Unit tests for async bulk resume screening (Phase 4.3).

Covers the shared per-file scorer, the synchronous fallback (no Celery
broker), the async enqueue + status polling flow, and ownership checks on
the status endpoint.
"""

import io
import uuid

import fitz

from config import settings
from models import BulkScreenJob
from routes_common import screen_resume_file
from tasks import bulk_screen_tasks as bst


def _make_pdf(text: str) -> bytes:
    """Build a tiny valid PDF containing ``text``."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


class TestScreenResumeFile:
    def test_scores_pdf_and_extracts_name(self):
        pdf = _make_pdf(
            "Software engineer with 5 years of experience in Python, React, SQL, and AWS."
        )
        result = screen_resume_file(
            pdf,
            "jane_doe_resume.pdf",
            ["python", "react", "sql", "aws"],
            "Software Engineer",
            "Software Engineer python react sql aws",
            4.0,
            "3-5",
        )
        assert result["candidate_name"] == "Jane Doe"
        assert result["skills_score"] == 100.0
        assert result["match_score"] > 0
        assert "python" in result["matched_skills"]
        assert result["raw_text"]
        assert result.get("error") is None

    def test_unreadable_pdf_returns_error(self):
        result = screen_resume_file(
            b"not a pdf", "broken.pdf", ["python"], "Job", "Job python", None, None
        )
        assert result["error"]

    def test_non_pdf_returns_error(self):
        result = screen_resume_file(
            b"hello", "notes.txt", ["python"], "Job", "Job python", None, None
        )
        assert result["error"] == "Only PDF files are supported"


class TestBulkScreenApi:
    def _multipart(self, pdf, filename="alice_smith.pdf"):
        return {
            "custom_title": "Backend Engineer",
            "custom_skills": "python,react,sql,aws",
            "custom_description": "Backend engineer with python react sql aws",
            "files": [(io.BytesIO(pdf), filename)],
        }

    def test_sync_fallback_returns_results_inline(
        self, client, db_session, test_recruiter, recruiter_auth_headers
    ):
        """No broker configured -> job processed synchronously, results inline."""
        resp = client.post(
            "/api/recruiters/bulk-screen",
            data=self._multipart(
                _make_pdf("Senior full-stack engineer, 6 years, Python React SQL AWS Docker")
            ),
            content_type="multipart/form-data",
            headers=recruiter_auth_headers,
        )
        assert resp.status_code == 200
        payload = resp.get_json()
        assert payload["status"] == "completed"
        assert payload["total_files"] == 1
        assert payload["job_id"]
        assert payload["results"][0]["candidate_name"] == "Alice Smith"

        # The job row persists so the status endpoint can serve it too.
        job = BulkScreenJob.query.get(uuid.UUID(payload["job_id"]))
        assert job and job.status == "completed"

    def test_async_enqueue_then_status_endpoint(
        self, client, db_session, test_recruiter, recruiter_auth_headers, monkeypatch
    ):
        """Broker configured -> 202 with job_id; worker completes it; status polls."""
        monkeypatch.setattr(settings, "CELERY_BROKER_URL", "redis://localhost:6379/0")
        captured = {}
        monkeypatch.setattr(
            bst.process_bulk_screen_job, "delay", lambda job_id: captured.update(job_id=job_id)
        )

        resp = client.post(
            "/api/recruiters/bulk-screen",
            data=self._multipart(
                _make_pdf("Engineer, 4 years, Python and SQL and AWS and React")
            ),
            content_type="multipart/form-data",
            headers=recruiter_auth_headers,
        )
        assert resp.status_code == 202
        payload = resp.get_json()
        assert payload["status"] == "queued"
        assert payload["total_files"] == 1
        assert captured["job_id"] == payload["job_id"]

        # Simulate the worker processing the queued job.
        result = bst.run_bulk_screen_job(payload["job_id"])
        assert result["status"] == "completed"

        status = client.get(
            f"/api/recruiters/bulk-screen/{payload['job_id']}",
            headers=recruiter_auth_headers,
        )
        assert status.status_code == 200
        data = status.get_json()
        assert data["status"] == "completed"
        assert data["progress"] == 100
        assert data["results"][0]["candidate_name"] == "Alice Smith"

    def test_broker_down_falls_back_to_sync(
        self, client, db_session, test_recruiter, recruiter_auth_headers, monkeypatch
    ):
        """Broker configured but enqueue fails -> inline processing, 200 with results."""
        monkeypatch.setattr(settings, "CELERY_BROKER_URL", "redis://localhost:6379/0")

        def boom(*args, **kwargs):
            raise RuntimeError("broker unreachable")

        monkeypatch.setattr(bst.process_bulk_screen_job, "delay", boom)
        resp = client.post(
            "/api/recruiters/bulk-screen",
            data=self._multipart(_make_pdf("Engineer, 4 years, Python and SQL")),
            content_type="multipart/form-data",
            headers=recruiter_auth_headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "completed"

    def test_status_endpoint_requires_owner(
        self,
        client,
        db_session,
        test_recruiter,
        auth_headers,
        recruiter_auth_headers,
    ):
        """Another user cannot read someone else's bulk screen job."""
        job = BulkScreenJob(recruiter_id=test_recruiter.user_id, status="queued", total_files=1)
        db_session.add(job)
        db_session.commit()

        forbidden = client.get(f"/api/recruiters/bulk-screen/{job.job_id}", headers=auth_headers)
        assert forbidden.status_code == 403

        ok = client.get(
            f"/api/recruiters/bulk-screen/{job.job_id}", headers=recruiter_auth_headers
        )
        assert ok.status_code == 200

    def test_status_endpoint_404_for_invalid_uuid(self, client, recruiter_auth_headers):
        resp = client.get(
            "/api/recruiters/bulk-screen/not-a-uuid", headers=recruiter_auth_headers
        )
        assert resp.status_code == 404

    def test_missing_files_rejected(self, client, recruiter_auth_headers):
        resp = client.post(
            "/api/recruiters/bulk-screen",
            data={"custom_title": "Job", "custom_skills": "python"},
            content_type="multipart/form-data",
            headers=recruiter_auth_headers,
        )
        assert resp.status_code == 400
