"""Pytest configuration and shared fixtures for SipSetu tests."""

import os
import sys
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from models import db, User, Applicant, Recruiter, Job, Resume, Skill, JobApplication, Ranking
from werkzeug.security import generate_password_hash


@pytest.fixture(scope="session")
def app():
    """Create application for testing."""
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["JWT_SECRET_KEY"] = "test-secret-key"
    os.environ["FRONTEND_URL"] = "http://localhost:5173"

    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture(scope="function")
def db_session(app):
    """Create database session for testing."""
    with app.app_context():
        yield db.session
        db.session.rollback()


@pytest.fixture
def test_user(db_session):
    """Create a test applicant user."""
    user = User(
        user_id=uuid4(),
        email="test@example.com",
        name="Test User",
        password_hash=generate_password_hash("password123"),
        role="applicant",
        email_verified=True,
    )
    db_session.add(user)

    applicant = Applicant(user_id=user.user_id)
    db_session.add(applicant)
    db_session.commit()
    return user


@pytest.fixture
def test_recruiter(db_session):
    """Create a test recruiter user."""
    user = User(
        user_id=uuid4(),
        email="recruiter@example.com",
        name="Test Recruiter",
        password_hash=generate_password_hash("password123"),
        role="recruiter",
        email_verified=True,
    )
    db_session.add(user)

    recruiter = Recruiter(user_id=user.user_id, company="Test Corp", job_title="HR Manager")
    db_session.add(recruiter)
    db_session.commit()
    return user


@pytest.fixture
def test_job(db_session, test_recruiter):
    """Create a test job."""
    from models import Recruiter
    recruiter = Recruiter.query.get(test_recruiter.user_id)

    job = Job(
        job_id=uuid4(),
        recruiter_id=recruiter.user_id,
        title="Software Engineer",
        description="We need a great engineer",
        location="Remote",
        job_type="full-time",
        experience_level="3-5",
        salary_min=100000,
        salary_max=150000,
    )
    db_session.add(job)

    # Add skills
    skills = ["python", "react", "sql", "aws"]
    for skill_name in skills:
        skill = Skill.query.filter_by(skill_name=skill_name).first()
        if not skill:
            skill = Skill(skill_id=uuid4(), skill_name=skill_name)
            db_session.add(skill)
        job.skills.append(skill)

    db_session.commit()
    return job


@pytest.fixture
def test_resume(db_session, test_user):
    """Create a test resume."""
    from models import Applicant
    applicant = Applicant.query.get(test_user.user_id)

    resume = Resume(
        resume_id=uuid4(),
        applicant_id=applicant.user_id,
        raw_text="Experienced software engineer with Python, React, SQL, and AWS skills.",
        file_path="/uploads/test_resume.pdf",
    )
    db_session.add(resume)

    # Add skills
    skills = ["python", "react", "sql", "aws", "docker"]
    for skill_name in skills:
        skill = Skill.query.filter_by(skill_name=skill_name).first()
        if not skill:
            skill = Skill(skill_id=uuid4(), skill_name=skill_name)
            db_session.add(skill)
        resume.skills.append(skill)

    db_session.commit()
    return resume


@pytest.fixture
def auth_headers(test_user):
    """Create authorization headers with JWT token."""
    from auth_middleware import create_token
    token = create_token(str(test_user.user_id), test_user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def recruiter_auth_headers(test_recruiter):
    """Create authorization headers for recruiter."""
    from auth_middleware import create_token
    token = create_token(str(test_recruiter.user_id), test_recruiter.role)
    return {"Authorization": f"Bearer {token}"}