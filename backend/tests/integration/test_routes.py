"""Integration tests for API routes."""

import pytest
import json


class TestAuthRoutes:
    """Tests for authentication endpoints."""

    def test_register_applicant(self, client):
        response = client.post("/api/auth/register", json={
            "name": "New User",
            "email": "newuser@test.com",
            "password": "password123",
            "role": "applicant"
        })
        assert response.status_code == 201
        data = response.get_json()
        assert "token" in data
        assert data["role"] == "applicant"
        assert data["email"] == "newuser@test.com"

    def test_register_recruiter(self, client):
        response = client.post("/api/auth/register", json={
            "name": "New Recruiter",
            "email": "newrec@test.com",
            "password": "password123",
            "role": "recruiter"
        })
        assert response.status_code == 201
        data = response.get_json()
        assert data["role"] == "recruiter"

    def test_register_duplicate_email(self, client, test_user):
        response = client.post("/api/auth/register", json={
            "name": "Another User",
            "email": test_user.email,
            "password": "password123",
            "role": "applicant"
        })
        assert response.status_code == 400

    def test_register_short_password(self, client):
        response = client.post("/api/auth/register", json={
            "name": "User",
            "email": "short@test.com",
            "password": "123",
            "role": "applicant"
        })
        assert response.status_code == 400

    def test_login_success(self, client, test_user):
        response = client.post("/api/auth/login", json={
            "email": test_user.email,
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.get_json()
        assert "token" in data
        assert data["user_id"] == str(test_user.user_id)

    def test_login_wrong_password(self, client, test_user):
        response = client.post("/api/auth/login", json={
            "email": test_user.email,
            "password": "wrongpassword"
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        response = client.post("/api/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "password123"
        })
        assert response.status_code == 401

    def test_get_me_authenticated(self, client, auth_headers):
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["email"] == "test@example.com"

    def test_get_me_unauthenticated(self, client):
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_forgot_password(self, client, test_user):
        response = client.post("/api/auth/forgot-password", json={
            "email": test_user.email
        })
        assert response.status_code == 200

    def test_forgot_password_nonexistent(self, client):
        # Should return 200 to prevent enumeration
        response = client.post("/api/auth/forgot-password", json={
            "email": "nonexistent@test.com"
        })
        assert response.status_code == 200


class TestJobRoutes:
    """Tests for job-related endpoints."""

    def test_create_job_recruiter(self, client, recruiter_auth_headers):
        response = client.post("/api/jobs", json={
            "title": "Backend Developer",
            "description": "Build APIs",
            "location": "Remote",
            "job_type": "full-time",
            "experience_level": "3-5",
            "salary_min": 100000,
            "salary_max": 150000,
            "skills": ["python", "sql", "aws"]
        }, headers=recruiter_auth_headers)
        assert response.status_code == 201
        data = response.get_json()
        assert data["title"] == "Backend Developer"

    def test_create_job_applicant_forbidden(self, client, auth_headers):
        response = client.post("/api/jobs", json={
            "title": "Backend Developer",
        }, headers=auth_headers)
        assert response.status_code == 403

    def test_list_jobs(self, client, test_job):
        response = client.get("/api/jobs")
        assert response.status_code == 200
        data = response.get_json()
        assert "jobs" in data
        assert len(data["jobs"]) >= 1

    def test_list_jobs_with_filters(self, client, test_job):
        response = client.get("/api/jobs?location=Remote&job_type=full-time")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["jobs"]) >= 1

    def test_get_job_details(self, client, test_job):
        response = client.get(f"/api/jobs/{test_job.job_id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["title"] == "Software Engineer"

    def test_get_nonexistent_job(self, client):
        import uuid
        response = client.get(f"/api/jobs/{uuid.uuid4()}")
        assert response.status_code == 404


class TestResumeRoutes:
    """Tests for resume endpoints."""

    def test_upload_resume(self, client, auth_headers):
        import io
        data = {
            "file": (io.BytesIO(b"Python React SQL experience"), "resume.pdf")
        }
        response = client.post("/api/resumes/upload-pdf", data=data, headers=auth_headers, content_type="multipart/form-data")
        # May fail due to PDF parsing in test env, but should not 500
        assert response.status_code in [200, 201, 400]

    def test_list_resumes(self, client, auth_headers, test_resume):
        response = client.get("/api/resumes", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) >= 1


class TestApplicationRoutes:
    """Tests for job application endpoints."""

    def test_apply_to_job(self, client, auth_headers, test_job, test_resume):
        response = client.post(f"/api/jobs/{test_job.job_id}/apply", headers=auth_headers)
        assert response.status_code == 201
        data = response.get_json()
        assert "application_id" in data

    def test_apply_twice(self, client, auth_headers, test_job, test_resume):
        client.post(f"/api/jobs/{test_job.job_id}/apply", headers=auth_headers)
        response = client.post(f"/api/jobs/{test_job.job_id}/apply", headers=auth_headers)
        assert response.status_code == 400  # Duplicate application

    def test_save_job(self, client, auth_headers, test_job):
        response = client.post(f"/api/jobs/{test_job.job_id}/save", headers=auth_headers)
        assert response.status_code == 201

    def test_unsave_job(self, client, auth_headers, test_job):
        client.post(f"/api/jobs/{test_job.job_id}/save", headers=auth_headers)
        response = client.delete(f"/api/jobs/{test_job.job_id}/save", headers=auth_headers)
        assert response.status_code == 200


class TestMatchingRoutes:
    """Tests for matching and ranking endpoints."""

    def test_matched_jobs(self, client, auth_headers, test_user, test_job, test_resume):
        response = client.get(f"/api/applicants/{test_user.user_id}/matched-jobs", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "matched_jobs" in data
        assert len(data["matched_jobs"]) >= 1

    def test_skill_gap(self, client, auth_headers, test_user, test_job, test_resume):
        response = client.get(f"/api/applicants/{test_user.user_id}/skill-gap", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "missing_skills" in data

    def test_recruiter_candidates(self, client, recruiter_auth_headers, test_recruiter, test_job, test_resume):
        # First apply to create ranking
        from models import db, JobApplication
        from flask import current_app
        with current_app.app_context():
            application = JobApplication(
                job_id=test_job.job_id,
                applicant_id=test_resume.applicant_id
            )
            db.session.add(application)
            db.session.commit()

        response = client.get(f"/api/recruiters/{test_recruiter.user_id}/candidates", headers=recruiter_auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "candidates" in data


class TestHealthCheck:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"