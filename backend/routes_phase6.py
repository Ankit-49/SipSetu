"""Phase 6.2 — Advanced Matching routes.

Provides:
  - Semantic search (resume↔job similarity via TF-IDF / pgvector)
  - Market intelligence (skill demand trends, salary benchmarks, competitiveness)
  - Diversity-aware ranking signals
"""

from __future__ import annotations

import json

from flask import Blueprint, g, jsonify, request

from auth_middleware import require_auth
from models import Job, Resume, Skill, db

phase6 = Blueprint('phase6', __name__)


# ---------------------------------------------------------------------------
# Semantic search
# ---------------------------------------------------------------------------

@phase6.route('/search/similar-resumes/<job_id>', methods=['GET'])
@require_auth
def search_similar_resumes(job_id):
    """Find resumes most semantically similar to a job posting.

    Uses TF-IDF cosine similarity (or pgvector when enabled).
    Query params: ?limit=10
    """
    from semantic_search import similar_resumes

    limit = request.args.get('limit', 10, type=int)
    limit = min(limit, 50)

    results = similar_resumes(job_id, limit=limit)
    return jsonify({
        "job_id": job_id,
        "results": results,
        "total": len(results),
    }), 200


@phase6.route('/search/similar-jobs/<resume_id>', methods=['GET'])
@require_auth
def search_similar_jobs(resume_id):
    """Find jobs most semantically similar to a resume.

    Query params: ?limit=10
    """
    from semantic_search import similar_jobs

    limit = request.args.get('limit', 10, type=int)
    limit = min(limit, 50)

    results = similar_jobs(resume_id, limit=limit)
    return jsonify({
        "resume_id": resume_id,
        "results": results,
        "total": len(results),
    }), 200


@phase6.route('/search/similar-resumes/<job_id>', methods=['POST'])
@require_auth
def reindex_job_embedding(job_id):
    """Recompute the embedding for a job and all its ranked resumes.

    Triggered when a job's description or skills change significantly.
    """
    from semantic_search import update_embedding

    job = Job.query.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    if str(job.recruiter_id) != g.current_user_id:
        return jsonify({"error": "Only the job owner can reindex"}), 403

    update_embedding(job)

    # Also reindex all resumes that have rankings for this job
    from models import Ranking
    resume_ids = set(
        r.resume_id for r in Ranking.query.filter_by(job_id=job_id).all()
    )
    reindexed = 0
    for rid in resume_ids:
        resume = Resume.query.get(rid)
        if resume:
            update_embedding(resume)
            reindexed += 1

    return jsonify({
        "message": "Embeddings reindexed",
        "job_id": job_id,
        "resumes_reindexed": reindexed,
    }), 200


# ---------------------------------------------------------------------------
# Market intelligence
# ---------------------------------------------------------------------------

@phase6.route('/market/skill-demand', methods=['GET'])
@require_auth
def market_skill_demand():
    """Top skills by demand across all job postings.

    Query params: ?top_n=20
    """
    from market_intelligence import skill_demand_summary

    top_n = request.args.get('top_n', 20, type=int)
    results = skill_demand_summary(top_n=min(top_n, 50))
    return jsonify({"skills": results, "total": len(results)}), 200


@phase6.route('/market/skill-trends', methods=['GET'])
@require_auth
def market_skill_trends():
    """Weekly demand trends for skills.

    Query params: ?skill=python&weeks=12
    """
    from market_intelligence import skill_demand_trends

    skill = request.args.get('skill')
    weeks = request.args.get('weeks', 12, type=int)
    weeks = min(weeks, 52)

    data = skill_demand_trends(skill_name=skill, weeks=weeks)
    return jsonify(data), 200


@phase6.route('/market/salary-benchmarks', methods=['GET'])
@require_auth
def market_salary_benchmarks():
    """Salary benchmarks with optional filters.

    Query params: ?skill=python&job_type=full-time&location=Remote&experience_level=3-5
    """
    from market_intelligence import salary_benchmarks

    skill = request.args.get('skill')
    job_type = request.args.get('job_type')
    location = request.args.get('location')
    experience_level = request.args.get('experience_level')

    data = salary_benchmarks(
        skill_name=skill,
        job_type=job_type,
        location=location,
        experience_level=experience_level,
    )
    return jsonify(data), 200


@phase6.route('/market/salary-by-skill', methods=['GET'])
@require_auth
def market_salary_by_skill():
    """Salary benchmarks for the top-N most in-demand skills.

    Query params: ?top_n=15
    """
    from market_intelligence import salary_benchmarks_by_skill

    top_n = request.args.get('top_n', 15, type=int)
    results = salary_benchmarks_by_skill(top_n=min(top_n, 30))
    return jsonify({"skills": results, "total": len(results)}), 200


@phase6.route('/market/hiring-velocity', methods=['GET'])
@require_auth
def market_hiring_velocity():
    """Jobs posted and applications received per week.

    Query params: ?weeks=12
    """
    from market_intelligence import hiring_velocity

    weeks = request.args.get('weeks', 12, type=int)
    weeks = min(weeks, 52)
    data = hiring_velocity(weeks=weeks)
    return jsonify(data), 200


@phase6.route('/market/applicant-ratio', methods=['GET'])
@require_auth
def market_applicant_ratio():
    """Applicant-to-job ratios overall and by job type."""
    from market_intelligence import applicant_to_job_ratio

    data = applicant_to_job_ratio()
    return jsonify(data), 200


@phase6.route('/market/skill-competitiveness', methods=['GET'])
@require_auth
def market_skill_competitiveness():
    """Competitiveness metrics per skill — demand, avg score, apps per job.

    Query params: ?top_n=15
    """
    from market_intelligence import skill_competitiveness

    top_n = request.args.get('top_n', 15, type=int)
    results = skill_competitiveness(top_n=min(top_n, 30))
    return jsonify({"skills": results, "total": len(results)}), 200


# ---------------------------------------------------------------------------
# Diversity-aware ranking
# ---------------------------------------------------------------------------

DIVERSITY_SKILL_TAXONOMY = {
    "engineering": [
        "python", "java", "javascript", "typescript", "go", "rust", "c++",
        "sql", "aws", "docker", "kubernetes", "react", "node.js",
    ],
    "data_science": [
        "python", "r", "sql", "tensorflow", "pytorch", "pandas", "numpy",
        "machine learning", "deep learning", "statistics", "spark",
    ],
    "design": [
        "figma", "sketch", "adobe xd", "photoshop", "illustrator",
        "ux design", "ui design", "user research", "prototyping",
    ],
    "marketing": [
        "seo", "sem", "google analytics", "content marketing", "social media",
        "email marketing", "copywriting", "hubspot", "salesforce",
    ],
    "product": [
        "product management", "agile", "scrum", "jira", "roadmapping",
        "user stories", "a/b testing", "analytics", "sql",
    ],
}


@phase6.route('/market/diversity-skills', methods=['GET'])
@require_auth
def market_diversity_skills():
    """Return the skill taxonomy used for diversity-aware ranking.

    Shows which skills belong to which discipline, helping recruiters
    assess skill diversity across a candidate pool.
    """
    taxonomy = {}
    for discipline, skills in DIVERSITY_SKILL_TAXONOMY.items():
        taxonomy[discipline] = {
            "skills": skills,
            "count": len(skills),
        }
    return jsonify({"taxonomy": taxonomy, "disciplines": list(taxonomy.keys())}), 200


@phase6.route('/jobs/<job_id>/diversity-analysis', methods=['GET'])
@require_auth
def job_diversity_analysis(job_id):
    """Analyse skill diversity of candidates for a job.

    Shows discipline distribution, average skill breadth, and
    whether the candidate pool is concentrated or diverse.
    """
    from models import Ranking

    job = Job.query.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    # Build reverse map: skill → discipline
    skill_to_discipline: dict[str, str] = {}
    for disc, skills in DIVERSITY_SKILL_TAXONOMY.items():
        for s in skills:
            skill_to_discipline[s.lower()] = disc

    # Get all ranked resumes for this job
    rankings = Ranking.query.filter_by(job_id=job_id).all()
    if not rankings:
        return jsonify({
            "job_id": job_id,
            "total_candidates": 0,
            "discipline_distribution": {},
            "avg_skill_breadth": 0,
        }), 200

    discipline_counts: dict[str, int] = {}
    total_skills = 0
    unique_disciplines: dict[str, set[str]] = {}

    for ranking in rankings:
        resume = Resume.query.get(ranking.resume_id)
        if not resume:
            continue
        candidate_disciplines: set[str] = set()
        for skill in resume.skills:
            disc = skill_to_discipline.get(skill.skill_name.lower())
            if disc:
                candidate_disciplines.add(disc)
                discipline_counts[disc] = discipline_counts.get(disc, 0) + 1
        total_skills += len(resume.skills)
        uid = str(resume.applicant_id)
        unique_disciplines[uid] = candidate_disciplines

    n_candidates = len(rankings)
    avg_breadth = round(total_skills / max(n_candidates, 1), 1)

    # Shannon entropy for diversity score
    import math
    total_mentions = max(sum(discipline_counts.values()), 1)
    entropy = 0.0
    for count in discipline_counts.values():
        p = count / total_mentions
        if p > 0:
            entropy -= p * math.log2(p)

    max_entropy = math.log2(max(len(DIVERSITY_SKILL_TAXONOMY), 1))
    diversity_score = round((entropy / max(max_entropy, 1e-9)) * 100.0, 1)

    return jsonify({
        "job_id": job_id,
        "total_candidates": n_candidates,
        "avg_skill_breadth": avg_breadth,
        "discipline_distribution": discipline_counts,
        "diversity_score": diversity_score,
    }), 200
