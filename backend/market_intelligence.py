"""Market intelligence service (Phase 6.2).

Provides aggregate labour-market data derived from the platform's own
job and application data:

1. **Skill demand trends** — which skills are most required, how demand
   changes over time (weekly/monthly), and emerging vs declining skills.

2. **Salary benchmarks** — median / p25 / p75 salary ranges by skill,
   job type, experience level, and location.

3. **Competitive landscape** — applicant-to-job ratios, average match
   scores per skill, and hiring velocity.

All data is derived from the ``jobs``, ``skills``, ``job_skills``,
``rankings``, and ``job_applications`` tables — no external data sources
required.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any

import numpy as np
from sqlalchemy import func

from models import Job, JobApplication, Ranking, Skill, db, job_skills

# ---------------------------------------------------------------------------
# Skill demand
# ---------------------------------------------------------------------------

def skill_demand_summary(top_n: int = 20) -> list[dict[str, Any]]:
    """Top skills by number of job postings requiring them.

    Returns a list sorted by demand count descending, each containing:
    - skill_name, demand_count, percentage_of_jobs
    """
    total_jobs = Job.query.count()
    if total_jobs == 0:
        return []

    skill_counts = (
        db.session.query(
            Skill.skill_name,
            func.count(job_skills.c.job_id).label("demand_count"),
        )
        .join(job_skills, Skill.skill_id == job_skills.c.skill_id)
        .group_by(Skill.skill_name)
        .order_by(func.count(job_skills.c.job_id).desc())
        .limit(top_n)
        .all()
    )

    return [
        {
            "skill_name": row.skill_name,
            "demand_count": row.demand_count,
            "percentage_of_jobs": round(
                (row.demand_count / total_jobs) * 100.0, 1
            ),
        }
        for row in skill_counts
    ]


def skill_demand_trends(
    skill_name: str | None = None,
    weeks: int = 12,
) -> dict[str, Any]:
    """Weekly demand trends for skills over the last *weeks* weeks.

    If ``skill_name`` is provided, returns trend data for that single
    skill.  Otherwise returns trends for the top 10 skills by total demand.
    """
    cutoff = datetime.utcnow() - timedelta(weeks=weeks)

    # Determine which skills to track
    if skill_name:
        tracked = [skill_name.lower()]
    else:
        top_skills = (
            db.session.query(Skill.skill_name)
            .join(job_skills, Skill.skill_id == job_skills.c.skill_id)
            .join(Job, Job.job_id == job_skills.c.job_id)
            .filter(Job.created_at >= cutoff)
            .group_by(Skill.skill_name)
            .order_by(func.count().desc())
            .limit(10)
            .all()
        )
        tracked = [row.skill_name for row in top_skills]

    if not tracked:
        return {"weeks": weeks, "skills": {}, "labels": []}

    # Build weekly buckets
    labels: list[str] = []
    buckets: dict[str, list[int]] = {s: [] for s in tracked}

    for week_offset in range(weeks - 1, -1, -1):
        week_start = cutoff + timedelta(weeks=week_offset)
        week_end = week_start + timedelta(weeks=1)
        labels.append(week_start.strftime("%Y-%m-%d"))

        # Count job postings per tracked skill in this week
        week_counts: dict[str, int] = {}
        rows = (
            db.session.query(Skill.skill_name, func.count(job_skills.c.job_id))
            .join(job_skills, Skill.skill_id == job_skills.c.skill_id)
            .join(Job, Job.job_id == job_skills.c.job_id)
            .filter(
                Job.created_at >= week_start,
                Job.created_at < week_end,
                Skill.skill_name.in_(tracked),
            )
            .group_by(Skill.skill_name)
            .all()
        )
        for name, count in rows:
            week_counts[name] = count

        for s in tracked:
            buckets[s].append(week_counts.get(s, 0))

    return {
        "weeks": weeks,
        "labels": labels,
        "skills": buckets,
    }


# ---------------------------------------------------------------------------
# Salary benchmarks
# ---------------------------------------------------------------------------

def salary_benchmarks(
    skill_name: str | None = None,
    job_type: str | None = None,
    location: str | None = None,
    experience_level: str | None = None,
) -> dict[str, Any]:
    """Aggregate salary data from job postings.

    Returns p25, median (p50), p75, and count for the filtered set.
    If ``skill_name`` is given, only jobs requiring that skill are included.
    """
    query = Job.query.filter(Job.salary_min.isnot(None), Job.salary_max.isnot(None))

    if skill_name:
        skill = Skill.query.filter_by(skill_name=skill_name.lower()).first()
        if skill:
            query = query.filter(Job.skills.any(Skill.skill_id == skill.skill_id))
        else:
            return {"count": 0, "p25": None, "median": None, "p75": None}

    if job_type:
        query = query.filter(Job.job_type == job_type)
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    if experience_level:
        query = query.filter(Job.experience_level == experience_level)

    jobs = query.all()
    if not jobs:
        return {"count": 0, "p25": None, "median": None, "p75": None}

    # Use midpoint of salary range for each job
    salaries = [(float(j.salary_min) + float(j.salary_max)) / 2.0 for j in jobs]
    arr = np.array(salaries)

    return {
        "count": len(salaries),
        "p25": round(float(np.percentile(arr, 25)), 0),
        "median": round(float(np.percentile(arr, 50)), 0),
        "p75": round(float(np.percentile(arr, 75)), 0),
        "min": round(float(arr.min()), 0),
        "max": round(float(arr.max()), 0),
        "average": round(float(arr.mean()), 0),
    }


def salary_benchmarks_by_skill(top_n: int = 15) -> list[dict[str, Any]]:
    """Salary benchmarks for the top-N most in-demand skills.

    Returns a list sorted by median salary descending.
    """
    top_skills = skill_demand_summary(top_n=top_n)
    results: list[dict[str, Any]] = []

    for skill_info in top_skills:
        bench = salary_benchmarks(skill_name=skill_info["skill_name"])
        if bench["count"] > 0:
            results.append({
                "skill_name": skill_info["skill_name"],
                "demand_count": skill_info["demand_count"],
                **bench,
            })

    results.sort(key=lambda x: x["median"], reverse=True)
    return results


# ---------------------------------------------------------------------------
# Competitive landscape
# ---------------------------------------------------------------------------

def hiring_velocity(weeks: int = 12) -> dict[str, Any]:
    """Jobs posted per week and applications received per week."""
    cutoff = datetime.utcnow() - timedelta(weeks=weeks)
    labels: list[str] = []
    jobs_per_week: list[int] = []
    apps_per_week: list[int] = []

    for week_offset in range(weeks - 1, -1, -1):
        week_start = cutoff + timedelta(weeks=week_offset)
        week_end = week_start + timedelta(weeks=1)
        labels.append(week_start.strftime("%Y-%m-%d"))

        job_count = Job.query.filter(
            Job.created_at >= week_start, Job.created_at < week_end
        ).count()
        app_count = JobApplication.query.filter(
            JobApplication.applied_at >= week_start,
            JobApplication.applied_at < week_end,
        ).count()

        jobs_per_week.append(job_count)
        apps_per_week.append(app_count)

    return {
        "weeks": weeks,
        "labels": labels,
        "jobs_per_week": jobs_per_week,
        "applications_per_week": apps_per_week,
    }


def applicant_to_job_ratio() -> dict[str, Any]:
    """Overall and per-job-type applicant-to-job ratios."""
    total_jobs = Job.query.count()
    total_apps = JobApplication.query.count()

    overall = round(total_apps / max(total_jobs, 1), 1)

    # Per job type
    type_rows = (
        db.session.query(
            Job.job_type,
            func.count(Job.job_id).label("jobs"),
            func.count(JobApplication.application_id).label("apps"),
        )
        .outerjoin(JobApplication, Job.job_id == JobApplication.job_id)
        .group_by(Job.job_type)
        .all()
    )

    by_type = {}
    for row in type_rows:
        jtype = row.job_type or "unspecified"
        by_type[jtype] = {
            "jobs": row.jobs,
            "applications": row.apps,
            "ratio": round(row.apps / max(row.jobs, 1), 1),
        }

    return {
        "overall": overall,
        "total_jobs": total_jobs,
        "total_applications": total_apps,
        "by_job_type": by_type,
    }


def skill_competitiveness(top_n: int = 15) -> list[dict[str, Any]]:
    """For each top skill, show average match score and application count.

    A skill with high demand AND low average match score is underserved —
    candidates lack the skill.  A skill with high demand AND high average
    match score is competitive.
    """
    top_skills = skill_demand_summary(top_n=top_n)
    results: list[dict[str, Any]] = []

    for skill_info in top_skills:
        skill = Skill.query.filter_by(skill_name=skill_info["skill_name"]).first()
        if not skill:
            continue

        # Find jobs requiring this skill
        job_ids = [
            jid for (jid,) in db.session.query(job_skills.c.job_id)
            .filter(job_skills.c.skill_id == skill.skill_id)
            .all()
        ]

        if not job_ids:
            continue

        # Average ranking score for candidates of those jobs
        avg_score = db.session.query(func.avg(Ranking.matching_score)).filter(
            Ranking.job_id.in_(job_ids)
        ).scalar()

        # Application count for those jobs
        app_count = JobApplication.query.filter(
            JobApplication.job_id.in_(job_ids)
        ).count()

        results.append({
            "skill_name": skill_info["skill_name"],
            "demand_count": skill_info["demand_count"],
            "avg_match_score": round(float(avg_score or 0), 1),
            "total_applications": app_count,
            "applications_per_job": round(
                app_count / max(len(job_ids), 1), 1
            ),
        })

    return results
