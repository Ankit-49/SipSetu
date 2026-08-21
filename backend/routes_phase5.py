"""Phase 5 routes: LLM resume parsing, recruiter feedback, admin dashboard.

Registered as a separate blueprint in app.py to keep routes.py manageable.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, g, jsonify, request
from sqlalchemy import func

from auth_middleware import require_auth, require_role
from config import settings
from models import (
    Applicant,
    AuditLog,
    BulkScreenJob,
    Job,
    JobApplication,
    Notification,
    Ranking,
    RankingFeedback,
    Recruiter,
    Resume,
    Skill,
    User,
    db,
)
from pagination import build_envelope, parse_limit
from rate_limiter import rate_limit

logger = logging.getLogger(__name__)

phase5 = Blueprint('phase5', __name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _log_audit(action: str, target_type: str | None = None,
               target_id: str | None = None, details: str | None = None):
    """Write an immutable audit log entry."""
    try:
        entry = AuditLog(
            actor_id=g.get("current_user_id"),
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
            ip_address=request.remote_addr,
        )
        db.session.add(entry)
    except Exception as e:
        logger.warning(f"Audit log write failed: {e}")


def _admin_required(f):
    """Restrict to admin users (email in ADMIN_EMAILS env var)."""
    @wraps(f)
    @require_auth
    def wrapper(*args, **kwargs):
        user = User.query.get(g.current_user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        admin_emails = [e.strip().lower() for e in settings.ADMIN_EMAILS.split(",") if e.strip()]
        if user.email.lower() not in admin_emails:
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return wrapper


# ============ 5.1 LLM RESUME PARSING ============


@phase5.route('/resumes/<resume_id>/parse', methods=['POST'])
@require_auth
def parse_resume_sections(resume_id):
    """Parse a resume into structured sections using LLM or regex fallback.

    Returns structured JSON with skills, experience, education, projects,
    certifications, and a confidence score.
    """
    resume = Resume.query.get(resume_id)
    if not resume:
        return jsonify({"error": "Resume not found"}), 404
    if str(resume.applicant_id) != g.current_user_id:
        return jsonify({"error": "You can only parse your own resumes"}), 403

    from llm_parser import parse_resume

    result = parse_resume(resume.raw_text or "")

    # Persist the parsed data on the resume
    resume.parsed_sections = json.dumps(result["sections"])
    resume.parse_confidence = result["confidence"]
    resume.parse_method = result["extraction_method"]
    db.session.commit()

    return jsonify({
        "resume_id": str(resume.resume_id),
        "sections": result["sections"],
        "confidence": result["confidence"],
        "extraction_method": result["extraction_method"],
    }), 200


@phase5.route('/resumes/<resume_id>/parsed', methods=['GET'])
@require_auth
def get_parsed_sections(resume_id):
    """Return previously parsed resume sections (cached)."""
    resume = Resume.query.get(resume_id)
    if not resume:
        return jsonify({"error": "Resume not found"}), 404
    if str(resume.applicant_id) != g.current_user_id:
        return jsonify({"error": "You can only access your own resumes"}), 403

    sections = {}
    if resume.parsed_sections:
        try:
            sections = json.loads(resume.parsed_sections)
        except (json.JSONDecodeError, TypeError):
            sections = {}

    return jsonify({
        "resume_id": str(resume.resume_id),
        "sections": sections,
        "confidence": resume.parse_confidence,
        "extraction_method": resume.parse_method,
    }), 200


# ============ 5.2 RECRUITER FEEDBACK LOOP ============


@phase5.route('/rankings/<ranking_id>/feedback', methods=['POST'])
@require_role('recruiter')
def submit_ranking_feedback(ranking_id):
    """Submit explicit feedback on a candidate's ranking.

    Body: {"direction": "higher" | "lower" | "correct", "note": "optional"}
    """
    ranking = Ranking.query.get(ranking_id)
    if not ranking:
        return jsonify({"error": "Ranking not found"}), 404

    job = Job.query.get(ranking.job_id)
    if not job or str(job.recruiter_id) != g.current_user_id:
        return jsonify({"error": "You can only provide feedback for your own jobs"}), 403

    data = request.get_json(silent=True) or {}
    direction = data.get("direction", "").strip().lower()
    note = data.get("note", "")

    if direction not in ("higher", "lower", "correct"):
        return jsonify({"error": "direction must be 'higher', 'lower', or 'correct'"}), 400

    # Upsert: one feedback per (ranking, recruiter)
    existing = RankingFeedback.query.filter_by(
        ranking_id=ranking_id, recruiter_id=g.current_user_id,
    ).first()

    if existing:
        existing.direction = direction
        existing.note = note or existing.note
        existing.created_at = datetime.utcnow()
    else:
        fb = RankingFeedback(
            ranking_id=ranking_id,
            recruiter_id=g.current_user_id,
            direction=direction,
            note=note,
        )
        db.session.add(fb)

    _log_audit("ranking_feedback", "ranking", str(ranking_id),
               json.dumps({"direction": direction, "note": note}))
    db.session.commit()

    return jsonify({
        "message": "Feedback recorded",
        "ranking_id": str(ranking_id),
        "direction": direction,
    }), 200


@phase5.route('/jobs/<job_id>/feedback-summary', methods=['GET'])
@require_role('recruiter')
def feedback_summary(job_id):
    """Return aggregated feedback for all rankings of a given job."""
    job = Job.query.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    if str(job.recruiter_id) != g.current_user_id:
        return jsonify({"error": "Access denied"}), 403

    feedbacks = (
        RankingFeedback.query
        .join(Ranking, Ranking.ranking_id == RankingFeedback.ranking_id)
        .filter(Ranking.job_id == job_id)
        .all()
    )

    summary = {"higher": 0, "lower": 0, "correct": 0, "total": len(feedbacks)}
    items = []
    for fb in feedbacks:
        summary[fb.direction] = summary.get(fb.direction, 0) + 1
        items.append({
            "feedback_id": str(fb.feedback_id),
            "ranking_id": str(fb.ranking_id),
            "direction": fb.direction,
            "note": fb.note,
            "created_at": fb.created_at.isoformat() if fb.created_at else None,
        })

    return jsonify({
        "job_id": job_id,
        "summary": summary,
        "feedbacks": items,
    }), 200


# ============ 5.3 ENHANCED NOTIFICATIONS ============


@phase5.route('/notifications/<user_id>/unread-count', methods=['GET'])
@require_auth
def unread_count(user_id):
    """Return the count of unread notifications (for badge/real-time updates)."""
    if g.current_user_id != user_id:
        return jsonify({"error": "Access denied"}), 403

    count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
    return jsonify({"unread_count": count}), 200


# ============ 5.4 ADMIN DASHBOARD ============


@phase5.route('/admin/stats', methods=['GET'])
@_admin_required
def admin_stats():
    """Platform-wide statistics for the admin dashboard."""
    total_users = User.query.count()
    total_applicants = Applicant.query.count()
    total_recruiters = Recruiter.query.count()
    total_jobs = Job.query.count()
    total_applications = JobApplication.query.count()
    total_resumes = Resume.query.count()

    # Applications by status
    status_counts = dict(
        db.session.query(JobApplication.status, func.count(JobApplication.application_id))
        .group_by(JobApplication.status).all()
    )

    # Jobs posted per week (last 8 weeks)
    eight_weeks_ago = datetime.utcnow() - timedelta(weeks=8)
    weekly_jobs = dict(
        db.session.query(
            func.strftime('%Y-%W', Job.created_at),
            func.count(Job.job_id),
        )
        .filter(Job.created_at >= eight_weeks_ago)
        .group_by(func.strftime('%Y-%W', Job.created_at))
        .order_by(func.strftime('%Y-%W', Job.created_at))
        .all()
    )

    # Registrations per week (last 8 weeks)
    weekly_registrations = dict(
        db.session.query(
            func.strftime('%Y-%W', User.created_at),
            func.count(User.user_id),
        )
        .filter(User.created_at >= eight_weeks_ago)
        .group_by(func.strftime('%Y-%W', User.created_at))
        .order_by(func.strftime('%Y-%W', User.created_at))
        .all()
    )

    # Recent activity (last 20 audit log entries)
    recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(20).all()

    # System health
    db_ok = True
    try:
        db.session.execute(db.text("SELECT 1"))
    except Exception:
        db_ok = False

    return jsonify({
        "users": {
            "total": total_users,
            "applicants": total_applicants,
            "recruiters": total_recruiters,
        },
        "jobs": {"total": total_jobs},
        "applications": {
            "total": total_applications,
            "by_status": status_counts,
        },
        "resumes": {"total": total_resumes},
        "weekly_jobs": weekly_jobs,
        "weekly_registrations": weekly_registrations,
        "recent_audit": [
            {
                "log_id": str(log.log_id),
                "actor_id": str(log.actor_id) if log.actor_id else None,
                "action": log.action,
                "target_type": log.target_type,
                "target_id": log.target_id,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in recent_logs
        ],
        "system": {
            "database": "ok" if db_ok else "error",
        },
    }), 200


@phase5.route('/admin/users', methods=['GET'])
@_admin_required
def admin_list_users():
    """List all users with pagination and search."""
    search = (request.args.get("search") or "").strip().lower()
    role_filter = (request.args.get("role") or "").strip().lower()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    query = User.query
    if search:
        query = query.filter(
            (User.email.ilike(f"%{search}%"))
            | (User.name.ilike(f"%{search}%"))
        )
    if role_filter in ("applicant", "recruiter"):
        query = query.filter(User.role == role_filter)

    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False,
    )

    users = []
    for u in pagination.items:
        users.append({
            "user_id": str(u.user_id),
            "email": u.email,
            "name": u.name,
            "role": u.role,
            "email_verified": u.email_verified,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        })

    return jsonify({
        "users": users,
        "total": pagination.total,
        "page": page,
        "per_page": per_page,
        "pages": pagination.pages,
    }), 200


@phase5.route('/admin/users/<user_id>/suspend', methods=['PATCH'])
@_admin_required
def admin_suspend_user(user_id):
    """Suspend or unsuspend a user (sets email_verified = False as soft suspension)."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(silent=True) or {}
    suspend = data.get("suspend", True)

    user.email_verified = not suspend
    _log_audit("user_suspend" if suspend else "user_unsuspend",
               "user", user_id, json.dumps({"suspended": suspend}))
    db.session.commit()

    return jsonify({
        "message": f"User {'suspended' if suspend else 'unsuspended'}",
        "user_id": user_id,
        "email_verified": user.email_verified,
    }), 200


@phase5.route('/admin/jobs', methods=['GET'])
@_admin_required
def admin_list_jobs():
    """List all jobs with recruiter info for moderation."""
    search = (request.args.get("search") or "").strip().lower()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    query = Job.query
    if search:
        query = query.filter(Job.title.ilike(f"%{search}%"))

    pagination = query.order_by(Job.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False,
    )

    jobs = []
    for j in pagination.items:
        jobs.append({
            "job_id": str(j.job_id),
            "title": j.title,
            "recruiter_name": j.recruiter.name or j.recruiter.email,
            "recruiter_id": str(j.recruiter_id),
            "location": j.location or "",
            "job_type": j.job_type or "",
            "created_at": j.created_at.isoformat() if j.created_at else None,
            "application_count": JobApplication.query.filter_by(job_id=j.job_id).count(),
        })

    return jsonify({
        "jobs": jobs,
        "total": pagination.total,
        "page": page,
        "per_page": per_page,
        "pages": pagination.pages,
    }), 200


@phase5.route('/admin/jobs/<job_id>', methods=['DELETE'])
@_admin_required
def admin_delete_job(job_id):
    """Admin: delete a job posting (moderation)."""
    job = Job.query.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    _log_audit("admin_delete_job", "job", job_id,
               json.dumps({"title": job.title, "recruiter_id": str(job.recruiter_id)}))

    # Notify the recruiter
    db.session.add(Notification(
        user_id=job.recruiter_id,
        title="Job Removed by Admin",
        message=f"Your job posting '{job.title}' has been removed by an administrator.",
        type="warning",
    ))

    db.session.delete(job)
    db.session.commit()

    return jsonify({"message": "Job deleted by admin", "job_id": job_id}), 200


@phase5.route('/admin/audit-logs', methods=['GET'])
@_admin_required
def admin_audit_logs():
    """List audit logs with pagination."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    action_filter = (request.args.get("action") or "").strip()

    query = AuditLog.query
    if action_filter:
        query = query.filter(AuditLog.action == action_filter)

    pagination = query.order_by(AuditLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False,
    )

    logs = []
    for log in pagination.items:
        logs.append({
            "log_id": str(log.log_id),
            "actor_id": str(log.actor_id) if log.actor_id else None,
            "action": log.action,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        })

    return jsonify({
        "logs": logs,
        "total": pagination.total,
        "page": page,
        "per_page": per_page,
        "pages": pagination.pages,
    }), 200
