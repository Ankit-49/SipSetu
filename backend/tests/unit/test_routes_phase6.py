"""Unit tests for Phase 6.2 routes — semantic search & market intelligence.

Covers:
  - Semantic search (similar resumes/jobs, reindex)
  - Market intelligence (skill demand, salary benchmarks, velocity, ratios)
  - Diversity analysis
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from werkzeug.security import generate_password_hash

from auth_middleware import create_token
from models import (
    Applicant,
    Job,
    JobApplication,
    Ranking,
    Recruiter,
    Resume,
    Skill,
    db,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

PHASE6_USER_EMAIL = "phase6_recruiter@example.com"
PHASE6_APPLICANT_EMAIL = "phase6_applicant@example.com"


@pytest.fixture(autouse=True)
def _clean(app):
    """Clean test data before and after each test."""
    with app.app_context():
        _delete_all()
        yield
        _delete_all()


def _delete_all():
    Ranking.query.delete(synchronize_session=False)
    JobApplication.query.delete(synchronize_session=False)
    Resume.query.delete(synchronize_session=False)
    Job.query.delete(synchronize_session=False)
    Skill.query.delete(synchronize_session=False)
    for email in [PHASE6_USER_EMAIL, PHASE6_APPLICANT_EMAIL]:
        user = db.session.execute(
            db.text("SELECT user_id FROM users WHERE email = :email"),
            {"email": email},
        ).scalar()
        if user:
            db.session.execute(
                db.text("DELETE FROM users WHERE user_id = :uid"),
                {"uid": user},
            )
    db.session.commit()


@pytest.fixture()
def recruiter_user(app):
    with app.app_context():
        uid = uuid4()
        r = Recruiter(
            user_id=uid,
            email=PHASE6_USER_EMAIL,
            name="Phase6 Recruiter",
            password_hash=generate_password_hash("password123"),
            role="recruiter",
            email_verified=True,
            company="TechCorp",
        )
        db.session.add(r)
        db.session.commit()
        return type("User", (), {"user_id": uid, "role": "recruiter"})()


@pytest.fixture()
def recruiter_headers(recruiter_user, app):
    with app.app_context():
        token = create_token(str(recruiter_user.user_id), recruiter_user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def applicant_user(app):
    with app.app_context():
        uid = uuid4()
        a = Applicant(
            user_id=uid,
            email=PHASE6_APPLICANT_EMAIL,
            name="Phase6 Applicant",
            password_hash=generate_password_hash("password123"),
            role="applicant",
            email_verified=True,
        )
        db.session.add(a)
        db.session.commit()
        return type("User", (), {"user_id": uid, "role": "applicant"})()


@pytest.fixture()
def applicant_headers(applicant_user, app):
    with app.app_context():
        token = create_token(str(applicant_user.user_id), applicant_user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def test_data(app, recruiter_user, applicant_user):
    """Create a rich dataset: skills, jobs, resumes, rankings, applications."""
    with app.app_context():
        skills_data = ["python", "react", "sql", "aws", "docker", "java", "go", "ml", "javascript"]
        skills = {}
        for name in skills_data:
            s = Skill(skill_id=uuid4(), skill_name=name)
            db.session.add(s)
            skills[name] = s

        # Create 3 jobs
        jobs = []
        for i, (title, job_skills_list) in enumerate([
            ("Python Engineer", ["python", "sql", "aws"]),
            ("React Developer", ["react", "javascript", "sql"]),
            ("ML Engineer", ["python", "ml", "docker"]),
        ]):
            j = Job(
                recruiter_id=recruiter_user.user_id,
                title=title,
                description=f"We need a {title}",
                location="Remote" if i % 2 == 0 else "New York",
                job_type="full-time",
                experience_level="3-5",
                salary_min=80000 + i * 10000,
                salary_max=120000 + i * 10000,
            )
            for sn in job_skills_list:
                j.skills.append(skills[sn])
            db.session.add(j)
            jobs.append(j)

        # Create 2 resumes
        resumes = []
        for i, (text, resume_skills_list) in enumerate([
            ("Experienced python engineer with react and sql skills", ["python", "react", "sql"]),
            ("ML specialist with docker and python expertise", ["python", "ml", "docker"]),
        ]):
            r = Resume(
                applicant_id=applicant_user.user_id,
                raw_text=text,
            )
            for sn in resume_skills_list:
                r.skills.append(skills[sn])
            db.session.add(r)
            resumes.append(r)

        db.session.flush()

        # Create rankings
        for job in jobs:
            for resume in resumes:
                ranking = Ranking(
                    job_id=job.job_id,
                    resume_id=resume.resume_id,
                    matching_score=70.0,
                    candidate_rank=1,
                )
                db.session.add(ranking)

        # Create some applications
        for job in jobs[:2]:
            app = JobApplication(
                job_id=job.job_id,
                applicant_id=applicant_user.user_id,
                status="shortlisted",
            )
            db.session.add(app)

        db.session.commit()

        # Return IDs (strings) — ORM objects become detached outside app context
        job_ids = [str(j.job_id) for j in jobs]
        resume_ids = [str(r.resume_id) for r in resumes]
        return type("TestData", (), {
            "job_ids": job_ids,
            "resume_ids": resume_ids,
        })()


# ---------------------------------------------------------------------------
# Semantic search
# ---------------------------------------------------------------------------


class TestSemanticSearch:
    def test_similar_resumes(self, client, recruiter_headers, test_data):
        job_id = test_data.job_ids[0]
        resp = client.get(
            f"/api/v1/search/similar-resumes/{job_id}",
            headers=recruiter_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["job_id"] == job_id
        assert isinstance(data["results"], list)

    def test_similar_resumes_not_found(self, client, recruiter_headers):
        resp = client.get(
            f"/api/v1/search/similar-resumes/{uuid4()}",
            headers=recruiter_headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["total"] == 0

    def test_similar_jobs(self, client, recruiter_headers, test_data):
        resume_id = test_data.resume_ids[0]
        resp = client.get(
            f"/api/v1/search/similar-jobs/{resume_id}",
            headers=recruiter_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["resume_id"] == resume_id
        assert isinstance(data["results"], list)

    def test_similar_jobs_not_found(self, client, recruiter_headers):
        resp = client.get(
            f"/api/v1/search/similar-jobs/{uuid4()}",
            headers=recruiter_headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["total"] == 0

    def test_reindex_embedding(self, client, recruiter_headers, test_data):
        job_id = test_data.job_ids[0]
        resp = client.post(
            f"/api/v1/search/similar-resumes/{job_id}",
            headers=recruiter_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["job_id"] == job_id
        assert data["resumes_reindexed"] >= 0

    def test_reindex_not_owner(self, client, applicant_headers, test_data):
        job_id = test_data.job_ids[0]
        resp = client.post(
            f"/api/v1/search/similar-resumes/{job_id}",
            headers=applicant_headers,
        )
        assert resp.status_code == 403

    def test_reindex_not_found(self, client, recruiter_headers):
        resp = client.post(
            f"/api/v1/search/similar-resumes/{uuid4()}",
            headers=recruiter_headers,
        )
        assert resp.status_code == 404

    def test_no_auth(self, client, test_data):
        job_id = test_data.job_ids[0]
        resp = client.get(f"/api/v1/search/similar-resumes/{job_id}")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Market intelligence — skill demand
# ---------------------------------------------------------------------------


class TestSkillDemand:
    def test_skill_demand_summary(self, client, recruiter_headers, test_data):
        resp = client.get(
            "/api/v1/market/skill-demand",
            headers=recruiter_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "skills" in data
        assert data["total"] > 0
        # python should be top skill (appears in 2 of 3 jobs)
        names = [s["skill_name"] for s in data["skills"]]
        assert "python" in names

    def test_skill_demand_custom_top_n(self, client, recruiter_headers, test_data):
        resp = client.get(
            "/api/v1/market/skill-demand?top_n=3",
            headers=recruiter_headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["total"] <= 3

    def test_skill_trends(self, client, recruiter_headers, test_data):
        resp = client.get(
            "/api/v1/market/skill-trends?weeks=4",
            headers=recruiter_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["weeks"] == 4
        assert "labels" in data
        assert "skills" in data

    def test_skill_trends_specific_skill(self, client, recruiter_headers, test_data):
        resp = client.get(
            "/api/v1/market/skill-trends?skill=python&weeks=8",
            headers=recruiter_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "python" in data["skills"]


# ---------------------------------------------------------------------------
# Market intelligence — salary benchmarks
# ---------------------------------------------------------------------------


class TestSalaryBenchmarks:
    def test_salary_benchmarks(self, client, recruiter_headers, test_data):
        resp = client.get(
            "/api/v1/market/salary-benchmarks",
            headers=recruiter_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] == 3
        assert data["median"] is not None
        assert data["p25"] <= data["median"] <= data["p75"]

    def test_salary_benchmarks_by_skill(self, client, recruiter_headers, test_data):
        resp = client.get(
            "/api/v1/market/salary-by-skill",
            headers=recruiter_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "skills" in data
        for skill in data["skills"]:
            assert "median" in skill
            assert "demand_count" in skill

    def test_salary_by_job_type(self, client, recruiter_headers, test_data):
        resp = client.get(
            "/api/v1/market/salary-benchmarks?job_type=full-time",
            headers=recruiter_headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["count"] == 3

    def test_salary_empty_filter(self, client, recruiter_headers, test_data):
        resp = client.get(
            "/api/v1/market/salary-benchmarks?location=Tokyo",
            headers=recruiter_headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["count"] == 0


# ---------------------------------------------------------------------------
# Market intelligence — velocity & ratios
# ---------------------------------------------------------------------------


class TestHiringVelocity:
    def test_hiring_velocity(self, client, recruiter_headers, test_data):
        resp = client.get(
            "/api/v1/market/hiring-velocity?weeks=4",
            headers=recruiter_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["weeks"] == 4
        assert len(data["labels"]) == 4
        assert len(data["jobs_per_week"]) == 4

    def test_applicant_ratio(self, client, recruiter_headers, test_data):
        resp = client.get(
            "/api/v1/market/applicant-ratio",
            headers=recruiter_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "overall" in data
        assert "by_job_type" in data
        assert data["total_jobs"] == 3


# ---------------------------------------------------------------------------
# Competitiveness
# ---------------------------------------------------------------------------


class TestSkillCompetitiveness:
    def test_skill_competitiveness(self, client, recruiter_headers, test_data):
        resp = client.get(
            "/api/v1/market/skill-competitiveness?top_n=5",
            headers=recruiter_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "skills" in data
        for skill in data["skills"]:
            assert "avg_match_score" in skill
            assert "total_applications" in skill


# ---------------------------------------------------------------------------
# Diversity analysis
# ---------------------------------------------------------------------------


class TestDiversityAnalysis:
    def test_diversity_skills(self, client, recruiter_headers):
        resp = client.get(
            "/api/v1/market/diversity-skills",
            headers=recruiter_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "taxonomy" in data
        assert "engineering" in data["taxonomy"]
        assert "data_science" in data["taxonomy"]

    def test_job_diversity_analysis(self, client, recruiter_headers, test_data):
        job_id = test_data.job_ids[0]
        resp = client.get(
            f"/api/v1/jobs/{job_id}/diversity-analysis",
            headers=recruiter_headers,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "total_candidates" in data
        assert "diversity_score" in data
        assert "discipline_distribution" in data

    def test_job_diversity_not_found(self, client, recruiter_headers):
        resp = client.get(
            f"/api/v1/jobs/{uuid4()}/diversity-analysis",
            headers=recruiter_headers,
        )
        assert resp.status_code == 404
