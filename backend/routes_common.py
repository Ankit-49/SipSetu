from __future__ import annotations

import re

from models import db, Job, JobApplication, Ranking, Resume, Skill

EXPERIENCE_LEVEL_TO_YEARS = {
    "fresher": 0.0,
    "1-3": 2.0,
    "3-5": 4.0,
    "5+": 5.0,
}


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


def extract_skills_from_text(text):
    if not text:
        return []

    text_lower = text.lower()
    common_skills = [
        'python', 'javascript', 'typescript', 'java', 'c++', 'c#', 'rust', 'php', 'ruby',
        'react', 'angular', 'vue', 'svelte', 'node.js', 'express', 'django', 'flask', 'fastapi',
        'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'graphql', 'rest api',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git', 'github', 'gitlab',
        'html', 'css', 'tailwind', 'bootstrap', 'sass', 'webpack', 'vite',
        'machine learning', 'deep learning', 'nlp', 'computer vision', 'tensorflow', 'pytorch',
        'design', 'figma', 'ui', 'ux', 'product', 'agile', 'scrum', 'jira',
        'communication', 'leadership', 'teamwork', 'problem solving', 'critical thinking'
    ]

    found_skills = []
    for skill in common_skills:
        if skill in text_lower:
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
    union = len(resume_set.union(job_set))
    if union == 0:
        return 0.0

    return round((intersection / union) * 100, 2)


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


def calculate_ranking_score(resume, job):
    try:
        from ranking_ml import predict_ranking_score

        return predict_ranking_score(resume, job)
    except Exception:
        resume_skills = [s.skill_name for s in resume.skills]
        job_skills = [s.skill_name for s in job.skills]
        skills_score = calculate_match_score(resume_skills, job_skills)
        experience_years = extract_experience_years(resume.raw_text or "")
        target_experience_years = experience_level_to_years(job.experience_level)
        experience_score = calculate_experience_score(experience_years, target_experience_years)

        if skills_score == 100.0 and experience_score >= 100.0:
            return 100.0

        combined_score = (skills_score * 0.88) + (experience_score * 0.10)
        return min(round(combined_score, 2), 99.99)


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
        "created_at": posted_at,
        "skills": [s.skill_name for s in job.skills],
    }
