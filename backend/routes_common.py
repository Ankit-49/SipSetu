from __future__ import annotations

import os
import re

from sqlalchemy import func

from models import Job, JobApplication, Ranking, Resume, db

EXPERIENCE_LEVEL_TO_YEARS = {
    "fresher": 0.0,
    "1-3": 2.0,
    "3-5": 4.0,
    "5+": 5.0,
}


def set_job_search_vector(job):
    """Maintain ``Job.search_vector`` for Postgres full-text search.

    Computed by the database with ``to_tsvector`` so the value matches the
    migration-005 backfill exactly. No-op on SQLite (dev/tests), where the
    search path falls back to ILIKE.
    """
    if db.engine.dialect.name != 'postgresql':
        job.search_vector = None
        return
    job.search_vector = func.to_tsvector(
        'english',
        func.coalesce(job.title, '')
        + ' ' + func.coalesce(job.description, '')
        + ' ' + func.coalesce(job.location, '')
        + ' ' + func.coalesce(job.job_type, ''),
    )


def format_candidate_preview(ranking):
    return {
        "ranking_id": str(ranking.ranking_id),
        "job_id": str(ranking.job.job_id),
        "job_title": ranking.job.title,
        "applicant_id": str(ranking.resume.applicant_id),
        "applicant_name": ranking.resume.applicant.name or ranking.resume.applicant.email,
        "applicant_email": ranking.resume.applicant.email,
        "applicant_location": ranking.resume.applicant.location or "",
        "matching_score": ranking.matching_score,
        "resume_skills": [s.skill_name for s in ranking.resume.skills],
    }


# Seed list of commonly occurring skills. This is NOT an exhaustive
# allow-list: extract_skills_from_text() also matches every skill already
# recorded in the database (posted by a recruiter or provided by an
# applicant), so a brand-new skill becomes recognizable the moment it is
# required/posted anywhere in the system — it no longer needs to be
# predetermined to be detected.
PREDEFINED_SKILLS = [
    # Languages
    'python', 'javascript', 'typescript', 'java', 'c++', 'c#', 'golang',
    'rust', 'php', 'ruby', 'kotlin', 'swift', 'scala', 'matlab',
    # Web / backend / frontend
    'react', 'angular', 'vue', 'svelte', 'next.js', 'node.js', 'express',
    'django', 'flask', 'fastapi', 'spring boot', 'graphql', 'rest api',
    'html', 'css', 'tailwind', 'bootstrap', 'sass', 'webpack', 'vite',
    'figma', 'ui', 'ux',
    # Data / databases
    'sql', 'sqlite', 'postgresql', 'mysql', 'mongodb', 'redis',
    'elasticsearch', 'cassandra', 'dynamodb', 'snowflake', 'bigquery',
    'kafka', 'airflow',
    'spark', 'hadoop', 'pandas', 'numpy', 'scikit-learn',
    'machine learning', 'deep learning', 'nlp', 'computer vision',
    'tensorflow', 'pytorch',
    # Cloud / DevOps
    'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'terraform',
    'ansible', 'prometheus', 'grafana', 'linux', 'git', 'github', 'gitlab',
    'ci/cd',
    # Business / soft skills
    'excel', 'tableau', 'power bi', 'looker', 'design', 'product', 'agile',
    'scrum', 'jira', 'communication', 'leadership', 'teamwork',
    'problem solving', 'critical thinking',
]

# DB-recorded skills shorter than this are too ambiguous to auto-detect in
# free text ("go", "r", "c" appear constantly in prose), so only curated
# seed entries may be shorter.
_MIN_AUTO_DETECT_LENGTH = 3


# Used to find every occurrence of the word in a case-insensitive way while
# avoiding partial matches (e.g. 'sql' inside 'sqlite', 'java' inside
# 'javascript'). Common word suffixes are tolerated so 'design' still matches
# 'designer'.
_SKILL_TOKEN_RE_TEMPLATE = r"(?<![a-z0-9]){escaped}(?:s|ing|ed|er)?(?![a-z0-9])"


def _db_known_skills():
    """Return every skill name already recorded in the database.

    Returns [] when no Flask app context is active (pure unit tests), so
    extraction stays usable without a database.
    """
    try:
        from flask import has_app_context

        if not has_app_context():
            return []
        from models import Skill

        return [s.skill_name for s in Skill.query.all()]
    except Exception:
        return []


def _text_contains_skill(text_lower, skill):
    """Case-insensitive containment with word-boundary awareness."""
    if " " in skill:
        # Phrases fall back to plain substring matching (handles plurals like
        # "rest apis" and "machine learning models").
        return skill in text_lower
    pattern = _SKILL_TOKEN_RE_TEMPLATE.format(escaped=re.escape(skill))
    return re.search(pattern, text_lower) is not None


def extract_skills_from_text(text, extra_skills=None):
    """Return the skills mentioned in ``text`` (lowercase, de-duplicated).

    Matches against the curated seed list PLUS any skills already recorded
    in the database, so a skill that was posted/required once (e.g.
    "terraform") is recognized in every later resume, PDF, or job
    description even though it was never in the predetermined list.
    ``extra_skills`` adds caller-known skills to the candidate set.
    """
    if not text:
        return []

    text_lower = text.lower()

    candidates = list(PREDEFINED_SKILLS)
    seen = set(candidates)

    for skill in extra_skills or []:
        name = str(skill).strip().lower()
        if name and name not in seen:
            candidates.append(name)
            seen.add(name)

    for skill in _db_known_skills():
        if skill not in seen:
            candidates.append(skill)
            seen.add(skill)

    found_skills = []
    for skill in candidates:
        if not skill:
            continue
        # The curated seed may contain short entries (ui, ux, c++, c#); DB
        # skills that short are too ambiguous for free-text auto-detection.
        if skill not in PREDEFINED_SKILLS and len(skill) < _MIN_AUTO_DETECT_LENGTH:
            continue
        if _text_contains_skill(text_lower, skill):
            found_skills.append(skill)

    return found_skills


def calculate_match_score(resume_skills_list, job_skills_list):
    if not job_skills_list or not resume_skills_list:
        return 0.0

    resume_set = set(s.lower() for s in resume_skills_list)
    job_set = set(s.lower() for s in job_skills_list)

    if not job_set:
        return 0.0

    intersection = len(resume_set.intersection(job_set))
    return round((intersection / len(job_set)) * 100, 2)


def extract_experience_years(text):
    if not text:
        return None

    patterns = [
        r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?|yr\.?)\s*(?:of\s*)?(?:experience|exp\.?)",
        r"(?:experience|exp\.?)\s*(?:of\s*)?(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?|yr\.?)",
        
    ]

    detected_years = []
    for pattern in patterns:
        for match in re.findall(pattern, text, flags=re.IGNORECASE):
            try:
                detected_years.append(float(match))
            except ValueError:
                continue

    return round(max(detected_years), 1) if detected_years else None


def experience_level_to_years(experience_level):
    if not experience_level:
        return None
    return EXPERIENCE_LEVEL_TO_YEARS.get(str(experience_level).strip().lower())


def calculate_experience_score(candidate_years, target_years):
    if candidate_years is None:
        return 0.0

    if target_years is None:
        return min(candidate_years * 12.0, 100.0)

    if target_years <= 0:
        return 100.0 if candidate_years <= 1 else max(0.0, 100.0 - ((candidate_years - 1) * 12.0))

    if candidate_years >= target_years:
        return 100.0

    return round(max(0.0, (candidate_years / target_years) * 100.0), 2)


def heuristic_breakdown(resume, job):
    """Return the three sub-scores that compose the deterministic heuristic.

    Skills coverage (70%), experience fit (15%), text-content similarity
    (15%). Used both by ``calculate_heuristic_score`` and by the ML
    explanation endpoint to explain scores when no model exists.
    """
    resume_skills = [s.skill_name for s in resume.skills]
    job_skills = [s.skill_name for s in job.skills]

    if not job_skills or not resume_skills:
        return {"skills_score": 0.0, "experience_score": 0.0, "content_score": 0.0}

    skills_score = calculate_match_score(resume_skills, job_skills)

    experience_years = extract_experience_years(resume.raw_text or "")
    target_experience_years = experience_level_to_years(job.experience_level)
    experience_score = calculate_experience_score(experience_years, target_experience_years)

    content_score = 0.0
    resume_text = (resume.raw_text or "").strip() or " ".join(resume_skills)
    job_text = " ".join(filter(None, [job.title or "", job.description or "", " ".join(job_skills)]))
    if resume_text and job_text:
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            matrix = TfidfVectorizer().fit_transform([resume_text, job_text]).toarray()
            content_score = float(cosine_similarity(matrix[0:1], matrix[1:2])[0, 0]) * 100
        except ValueError:
            pass

    return {
        "skills_score": round(skills_score, 2),
        "experience_score": round(experience_score, 2),
        "content_score": round(content_score, 2),
    }


def calculate_heuristic_score(resume, job):
    """Coverage-based match score between a resume and a job (0-100).

    Deterministic heuristic: skill coverage (70%) + experience fit (15%)
    + text-content similarity (15%), matching the bulk-screening formula.
    This is the safety anchor for the ML ranking model and the fallback
    when no trained model exists.
    """
    breakdown = heuristic_breakdown(resume, job)
    skills_score = breakdown["skills_score"]
    experience_score = breakdown["experience_score"]
    content_score = breakdown["content_score"]

    if skills_score == 100.0 and experience_score >= 100.0 and content_score >= 99.0:
        return 100.0

    combined = (skills_score * 0.70) + (experience_score * 0.15) + (content_score * 0.15)
    return min(round(combined, 2), 99.99)


def calculate_ranking_score(resume, job):
    """Score a resume against a job, preferring the trained ML model.

    Uses the deterministic heuristic as the safety anchor (the model
    blends with it internally and falls back to it entirely when no
    trained model exists or inference fails).
    """
    try:
        from ranking_ml import predict_ranking_score

        return predict_ranking_score(resume, job)
    except Exception:
        return calculate_heuristic_score(resume, job)


def create_rankings_for_job(job_id):
    """Create/refresh rankings for a job — only applicants who applied are scored."""
    job = Job.query.get(job_id)
    if not job:
        return

    applications = JobApplication.query.filter_by(job_id=job_id).all()

    # Build the set of (resume_id, applicant_id) tuples that legitimately belong
    # to this job. Use the applicant's most recent resume so a re-upload doesn't
    # leave stale rows behind.
    legitimate: set[tuple[str, str]] = set()
    for application in applications:
        resume = (
            Resume.query.filter_by(applicant_id=application.applicant_id)
            .order_by(Resume.uploaded_at.desc())
            .first()
        )
        if not resume:
            continue
        legitimate.add((str(resume.resume_id), str(application.applicant_id)))
        score = calculate_ranking_score(resume, job)
        existing_ranking = Ranking.query.filter_by(job_id=job_id, resume_id=resume.resume_id).first()
        if existing_ranking:
            existing_ranking.matching_score = score
        else:
            db.session.add(Ranking(job_id=job_id, resume_id=resume.resume_id, matching_score=score))

    # Wipe stale rankings for this job. An applicant can only appear for a job
    # they applied to, so any (resume, job) row that isn't in the legitimate
    # set must be removed (covers: un-applied applicants, deleted applications,
    # orphans from old resume_ids).
    Ranking.query.filter(Ranking.job_id == job_id).all()
    all_rankings = Ranking.query.filter(Ranking.job_id == job_id).all()
    for r in all_rankings:
        if (str(r.resume_id), str(r.resume.applicant_id)) not in legitimate:
            db.session.delete(r)

    db.session.commit()


def create_rankings_for_resume_after_delete(applicant_id):
    """Remove all rankings for an applicant whose last resume was deleted."""
    applicant_resume_ids = [
        str(r.resume_id)
        for r in Resume.query.filter_by(applicant_id=applicant_id).all()
    ]
    if not applicant_resume_ids:
        return
    stale = Ranking.query.filter(Ranking.resume_id.in_(applicant_resume_ids)).all()
    for r in stale:
        db.session.delete(r)
    db.session.commit()


def create_rankings_for_resume(resume_id, applicant_id):
    """Create/refresh rankings for a resume — only jobs the applicant applied to are scored."""
    resume = Resume.query.get(resume_id)
    if not resume:
        return

    applications = JobApplication.query.filter_by(applicant_id=applicant_id).all()
    applied_job_ids: set[str] = set()
    for application in applications:
        job = Job.query.get(application.job_id)
        if not job:
            continue
        applied_job_ids.add(str(job.job_id))
        score = calculate_ranking_score(resume, job)
        existing_ranking = Ranking.query.filter_by(job_id=job.job_id, resume_id=resume_id).first()
        if existing_ranking:
            existing_ranking.matching_score = score
        else:
            db.session.add(Ranking(job_id=job.job_id, resume_id=resume_id, matching_score=score))

    # Remove rankings for jobs this applicant did NOT apply to, but only when
    # the ranking uses one of THIS applicant's resume_ids. This keeps other
    # applicants' rankings intact while pruning our own stale ones.
    applicant_resume_ids = [
        str(r.resume_id)
        for r in Resume.query.filter_by(applicant_id=applicant_id).all()
    ]
    if applicant_resume_ids:
        stale = (
            Ranking.query
            .filter(Ranking.resume_id.in_(applicant_resume_ids))
            .filter(~Ranking.job_id.in_(applied_job_ids))
            .all()
        )
        for r in stale:
            db.session.delete(r)

    db.session.commit()


def screen_resume_file(
    file_bytes: bytes,
    filename: str,
    job_skills_list: list,
    job_title: str = "",
    job_desc: str = "",
    target_experience_years: float | None = None,
    job_experience_level: str | None = None,
):
    """Score a single resume PDF against a target profile (0-100).

    Shared by the bulk-screen endpoint's synchronous fallback and the
    Celery worker task (Phase 4.3), so both produce identical per-file
    results: skills coverage (70%), experience fit (15%), TF-IDF content
    similarity (15%), plus an optional ML explanation.
    """
    import fitz

    if not filename.lower().endswith(".pdf"):
        return {
            "filename": filename, "candidate_name": filename,
            "match_score": 0.0, "error": "Only PDF files are supported",
        }

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = "".join(page.get_text() for page in doc).strip()
        doc.close()
    except Exception as e:
        return {
            "filename": filename, "candidate_name": filename,
            "match_score": 0.0, "error": f"Error parsing PDF: {e!s}",
        }

    if not text:
        return {
            "filename": filename, "candidate_name": filename,
            "match_score": 0.0, "error": "The PDF file has no readable text",
        }

    base_name, _ = os.path.splitext(filename)
    cleaned_name = base_name.replace("_", " ").replace("-", " ")
    words = cleaned_name.split()
    cleaned_words = [
        w for w in words if w.lower()
        not in {"resume", "cv", "final", "pdf", "job", "application",
                "2026", "2025", "2024", "updated"}
    ]
    candidate_name = " ".join(cleaned_words).title() if cleaned_words else cleaned_name.title()

    resume_skills = extract_skills_from_text(text)
    skills_score = calculate_match_score(resume_skills, job_skills_list)
    experience_years = extract_experience_years(text)
    experience_score = calculate_experience_score(experience_years, target_experience_years)

    content_score = 0.0
    if job_desc and text:
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            v = TfidfVectorizer(stop_words="english")
            tfidf = v.fit_transform([job_desc, text])
            content_score = float(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]) * 100
        except Exception:
            pass

    combined = 100.0 if (skills_score == 100.0 and experience_score >= 100.0) else \
        min(round((skills_score * 0.70) + (experience_score * 0.15) + (content_score * 0.15), 2), 99.99)

    # Per-candidate "why this score" explanation (best-effort; the UI falls
    # back to the heuristic sub-scores when no model is trained).
    explanation = None
    try:
        from ranking_ml import explain_bulk_resume

        explanation = explain_bulk_resume(
            raw_text=text,
            resume_skills=resume_skills,
            job_title=job_title,
            job_skills=job_skills_list,
            job_description=job_desc,
            job_experience_level=job_experience_level,
        )
    except Exception:
        pass

    return {
        "filename": filename, "candidate_name": candidate_name,
        "match_score": combined, "skills_score": round(skills_score, 2),
        "experience_years": experience_years, "experience_score": round(experience_score, 2),
        "content_score": round(content_score, 2), "extracted_skills": resume_skills,
        "matched_skills": list(set(resume_skills) & set(job_skills_list)),
        "missing_skills": list(set(job_skills_list) - set(resume_skills)),
        "text_snippet": text[:250] + "..." if len(text) > 250 else text,
        "raw_text": text,
        "explanation": explanation,
    }


def bulk_screen_job_dir(job_id) -> str:
    """Temp directory holding the uploaded PDFs for a bulk screening job.

    Shared by the API route (writes the files) and the Celery worker task
    (reads them back), so they must agree on the location.
    """
    from config import settings

    return os.path.join(settings.BULK_SCREEN_TMP_DIR, str(job_id))


def format_job(job):
    salary = None
    if job.salary_min and job.salary_max:
        salary = f"Rs.{int(job.salary_min)}-{int(job.salary_max)} LPA"
    elif job.salary_min:
        salary = f"Rs.{int(job.salary_min)}+ LPA"

    posted_at = job.created_at.isoformat() if job.created_at else None

    return {
        "job_id": str(job.job_id),
        "title": job.title,
        "description": job.description or "",
        "location": job.location or "",
        "job_type": job.job_type or "",
        "experience_level": job.experience_level or "",
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "salary": salary,
        "recruiter_id": str(job.recruiter_id),
        "recruiter_name": job.recruiter.name or "",
        "recruiter_company": job.recruiter.company or "",
        "recruiter_profile_image": job.recruiter.profile_image or "",
        "created_at": posted_at,
        "skills": [s.skill_name for s in job.skills],
    }
