"""Unit tests for scoring and ranking functions."""

from uuid import uuid4

from models import Job, Recruiter, Resume, Skill
from routes_common import (
    calculate_experience_score,
    calculate_heuristic_score,
    calculate_match_score,
    experience_level_to_years,
    extract_experience_years,
    extract_skills_from_text,
    heuristic_breakdown,
)


class TestSkillExtraction:
    """Tests for skill extraction from text."""

    def test_extract_known_skills(self):
        text = "I know Python, React, and SQL very well."
        skills = extract_skills_from_text(text)
        assert "python" in skills
        assert "react" in skills
        assert "sql" in skills

    def test_extract_no_skills(self):
        text = "I like cats and dogs."
        skills = extract_skills_from_text(text)
        assert len(skills) == 0

    def test_extract_empty_text(self):
        skills = extract_skills_from_text("")
        assert len(skills) == 0

    def test_extract_none_text(self):
        skills = extract_skills_from_text(None)
        assert len(skills) == 0

    def test_case_insensitive(self):
        text = "PYTHON and JavaScript"
        skills = extract_skills_from_text(text)
        assert "python" in skills
        assert "javascript" in skills

    def test_word_boundary_matching(self):
        # 'java' must not match inside 'javascript', 'sql' not inside 'sqlite'.
        skills = extract_skills_from_text("JavaScript and SQLite experience")
        assert "java" not in skills
        assert "sql" not in skills
        assert "javascript" in skills
        assert "sqlite" in skills

    def test_extract_extra_skills_parameter(self):
        skills = extract_skills_from_text(
            "We use kubernetes for orchestration",
            extra_skills=["kubernetes", "helm"],
        )
        assert "kubernetes" in skills
        assert "helm" not in skills  # helm is not mentioned in the text

    def test_db_known_skills_recognized(self, app):
        # A skill that was never in the predefined list becomes recognizable
        # once it is recorded in the database (e.g. a recruiter posts a job
        # requiring it).
        with app.app_context():
            from models import Skill, db

            db.session.add(Skill(skill_name="terraform"))
            db.session.commit()

            skills = extract_skills_from_text(
                "5 years of terraform infrastructure experience"
            )
            assert "terraform" in skills


class TestMatchScore:
    """Tests for skill match scoring."""

    def test_perfect_match(self):
        resume_skills = ["python", "react", "sql"]
        job_skills = ["python", "react", "sql"]
        score = calculate_match_score(resume_skills, job_skills)
        assert score == 100.0

    def test_partial_match(self):
        resume_skills = ["python", "react"]
        job_skills = ["python", "react", "sql"]
        score = calculate_match_score(resume_skills, job_skills)
        assert score == 66.67

    def test_no_match(self):
        resume_skills = ["java", "c++"]
        job_skills = ["python", "react", "sql"]
        score = calculate_match_score(resume_skills, job_skills)
        assert score == 0.0

    def test_empty_job_skills(self):
        resume_skills = ["python"]
        job_skills = []
        score = calculate_match_score(resume_skills, job_skills)
        assert score == 0.0

    def test_empty_resume_skills(self):
        resume_skills = []
        job_skills = ["python"]
        score = calculate_match_score(resume_skills, job_skills)
        assert score == 0.0

    def test_case_insensitive_match(self):
        resume_skills = ["PYTHON", "React"]
        job_skills = ["python", "react"]
        score = calculate_match_score(resume_skills, job_skills)
        assert score == 100.0


class TestExperienceScoring:
    """Tests for experience scoring."""

    def test_experience_level_to_years(self):
        assert experience_level_to_years("fresher") == 0.0
        assert experience_level_to_years("1-3") == 2.0
        assert experience_level_to_years("3-5") == 4.0
        assert experience_level_to_years("5+") == 5.0
        assert experience_level_to_years("unknown") is None
        assert experience_level_to_years(None) is None

    def test_extract_experience_years(self):
        text = "5 years of experience in software development"
        years = extract_experience_years(text)
        assert years == 5.0

    def test_extract_experience_variations(self):
        text = "3.5 years exp. in Python"
        years = extract_experience_years(text)
        assert years == 3.5

    def test_extract_no_experience(self):
        text = "I am a fresher looking for opportunities"
        years = extract_experience_years(text)
        assert years is None

    def test_calculate_experience_score_exact_match(self):
        score = calculate_experience_score(4.0, 4.0)
        assert score == 100.0

    def test_calculate_experience_score_more_experience(self):
        score = calculate_experience_score(5.0, 3.0)
        assert score == 100.0

    def test_calculate_experience_score_less_experience(self):
        score = calculate_experience_score(2.0, 4.0)
        assert score == 50.0

    def test_calculate_experience_score_fresher(self):
        score = calculate_experience_score(0.0, 0.0)
        assert score == 100.0

    def test_calculate_experience_score_no_target(self):
        score = calculate_experience_score(5.0, None)
        assert score == 60.0  # 5 * 12 = 60, capped at 100

    def test_calculate_experience_score_no_candidate(self):
        score = calculate_experience_score(None, 4.0)
        assert score == 0.0


class TestHeuristicBreakdown:
    """Tests for heuristic score breakdown."""

    def test_heuristic_breakdown_perfect_match(self, app):
        with app.app_context():
            from werkzeug.security import generate_password_hash

            from models import Applicant, Recruiter, db

            # Create recruiter (requires User fields)
            recruiter = Recruiter(
                user_id=uuid4(),
                email="recruiter@test.com",
                name="Test Recruiter",
                password_hash=generate_password_hash("password123"),
                role="recruiter",
                company="Test Corp",
                job_title="HR"
            )
            db.session.add(recruiter)
            db.session.flush()

            # Create applicant for resume
            applicant = Applicant(
                user_id=uuid4(),
                email="applicant@test.com",
                name="Test Applicant",
                password_hash=generate_password_hash("password123"),
                role="applicant"
            )
            db.session.add(applicant)
            db.session.flush()

            # Unique skill names so the test is independent of any other test
            # that already committed the same literal skill names (the app
            # fixture's DB is shared across the whole pytest run).
            skills = []
            for name in [f"python_{uuid4()}", f"react_{uuid4()}", f"sql_{uuid4()}"]:
                skill = Skill(skill_name=name)
                db.session.add(skill)
                skills.append(skill)
            db.session.commit()

            # Create job with skills
            job = Job(title="Developer", description="Python React SQL", recruiter_id=recruiter.user_id)
            job.skills = skills
            db.session.add(job)
            db.session.commit()

            # Create resume with matching skills
            resume = Resume(raw_text="Python React SQL expert", skills=skills, applicant_id=applicant.user_id)
            db.session.add(resume)
            db.session.commit()

            breakdown = heuristic_breakdown(resume, job)
            assert breakdown["skills_score"] == 100.0
            assert breakdown["experience_score"] >= 0.0
            assert breakdown["content_score"] >= 0.0


class TestHeuristicScore:
    """Tests for final heuristic score calculation."""

    def test_heuristic_score_range(self, app):
        with app.app_context():
            from werkzeug.security import generate_password_hash

            from models import Applicant, Recruiter, db

            recruiter = Recruiter(
                user_id=uuid4(),
                email=f"recruiter_{uuid4()}@test.com",
                name="Test Recruiter",
                password_hash=generate_password_hash("password123"),
                role="recruiter",
                company="Test Corp",
                job_title="HR"
            )
            db.session.add(recruiter)
            db.session.flush()

            applicant = Applicant(
                user_id=uuid4(),
                email=f"applicant_{uuid4()}@test.com",
                name="Test Applicant",
                password_hash=generate_password_hash("password123"),
                role="applicant"
            )
            db.session.add(applicant)
            db.session.flush()

            skills = [Skill(skill_name=f"python_{uuid4()}"), Skill(skill_name=f"react_{uuid4()}")]
            for s in skills:
                db.session.add(s)
            db.session.commit()

            job = Job(title="Dev", description="Python React", skills=skills[:1], recruiter_id=recruiter.user_id)
            resume = Resume(raw_text="Python developer", skills=skills[:1], applicant_id=applicant.user_id)

            db.session.add_all([job, resume])
            db.session.commit()

            score = calculate_heuristic_score(resume, job)
            assert 0.0 <= score <= 99.99

    def test_heuristic_score_perfect(self, app):
        with app.app_context():
            from werkzeug.security import generate_password_hash

            from models import Applicant, Recruiter, db

            recruiter = Recruiter(
                user_id=uuid4(),
                email=f"recruiter_{uuid4()}@test.com",
                name="Test Recruiter",
                password_hash=generate_password_hash("password123"),
                role="recruiter",
                company="Test Corp",
                job_title="HR"
            )
            db.session.add(recruiter)
            db.session.flush()

            applicant = Applicant(
                user_id=uuid4(),
                email=f"applicant_{uuid4()}@test.com",
                name="Test Applicant",
                password_hash=generate_password_hash("password123"),
                role="applicant"
            )
            db.session.add(applicant)
            db.session.flush()

            skill = Skill(skill_name=f"python_{uuid4()}")
            db.session.add(skill)
            db.session.commit()

            job = Job(title="Python Dev", description="Python", skills=[skill], experience_level="fresher", recruiter_id=recruiter.user_id)
            resume = Resume(raw_text="5 years python experience", skills=[skill], applicant_id=applicant.user_id)

            db.session.add_all([job, resume])
            db.session.commit()

            score = calculate_heuristic_score(resume, job)
            # With all skills matched, minimum score is 70% (skills weight)
            assert score >= 70.0