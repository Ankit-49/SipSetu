"""Unit tests for scoring and ranking functions."""

import pytest
from routes_common import (
    calculate_match_score,
    calculate_experience_score,
    experience_level_to_years,
    extract_experience_years,
    extract_skills_from_text,
    heuristic_breakdown,
    calculate_heuristic_score,
)
from models import Resume, Job, Skill


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
            from models import db

            # Create skills
            skills = []
            for name in ["python", "react", "sql"]:
                skill = Skill(skill_name=name)
                db.session.add(skill)
                skills.append(skill)
            db.session.commit()

            # Create job with skills
            job = Job(title="Developer", description="Python React SQL")
            job.skills = skills
            db.session.add(job)
            db.session.commit()

            # Create resume with matching skills
            resume = Resume(raw_text="Python React SQL expert", skills=skills)
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
            from models import db

            skills = [Skill(skill_name=n) for n in ["python", "react"]]
            for s in skills:
                db.session.add(s)
            db.session.commit()

            job = Job(title="Dev", description="Python React", skills=skills[:1])
            resume = Resume(raw_text="Python developer", skills=skills[:1])

            db.session.add_all([job, resume])
            db.session.commit()

            score = calculate_heuristic_score(resume, job)
            assert 0.0 <= score <= 99.99

    def test_heuristic_score_perfect(self, app):
        with app.app_context():
            from models import db

            skill = Skill(skill_name="python")
            db.session.add(skill)
            db.session.commit()

            job = Job(title="Python Dev", description="Python", skills=[skill], experience_level="fresher")
            resume = Resume(raw_text="5 years python experience", skills=[skill])

            db.session.add_all([job, resume])
            db.session.commit()

            score = calculate_heuristic_score(resume, job)
            # With all skills matched, minimum score is 70% (skills weight)
            assert score >= 70.0