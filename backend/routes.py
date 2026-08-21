import json
import os
import random
import secrets
import uuid
from datetime import datetime, timedelta
from functools import wraps

import fitz  # PyMuPDF
from flask import Blueprint, current_app, g, jsonify, request
from sqlalchemy import func, or_
from werkzeug.security import check_password_hash, generate_password_hash

from auth_middleware import create_token, require_auth, require_role
from config import settings
from models import (
    Applicant,
    BulkScreenJob,
    EmailVerificationToken,
    Interview,
    Job,
    JobApplication,
    Notification,
    PasswordResetToken,
    Ranking,
    Recruiter,
    Resume,
    SavedJob,
    Skill,
    SkillProgress,
    User,
    db,
)
from pagination import (
    build_envelope,
    decode_cursor,
    encode_cursor,
    in_memory_after,
    is_v1_request,
    keyset_filter,
    parse_limit,
)
from ranking_ml import (
    explain_ranking_score,
    get_ranking_model_status,
    train_ranking_model,
)
from rate_limiter import rate_limit
from routes_common import (
    bulk_screen_job_dir,
    calculate_ranking_score,
    create_rankings_for_job,
    create_rankings_for_resume,
    create_rankings_for_resume_after_delete,
    experience_level_to_years,
    extract_experience_years,
    extract_skills_from_text,
    format_candidate_preview,
    format_job,
    set_job_search_vector,
)
from utils.email import (
    render_email,
    send_password_reset_otp,
    send_verification_otp,
)
from utils.storage import get_storage

api = Blueprint('api', __name__)


# ---------------------------------------------------------------------------
# WebSocket helper (Phase 5.3)
# ---------------------------------------------------------------------------

def _emit_ws(user_id, title, message, notif_type="info", related_job_id=None):
    """Emit a real-time notification via WebSocket (no-op if not configured)."""
    try:
        from websocket import emit_notification, emit_notification_count
        emit_notification(user_id, title, message, notif_type, related_job_id)
        emit_notification_count(user_id)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ownership_required(f):
    """Verify the URL user/applicant/recruiter ID matches the JWT subject."""
    @wraps(f)
    @require_auth
    def wrapper(*args, **kwargs):
        target_id = (
            kwargs.get("user_id")
            or kwargs.get("applicant_id")
            or kwargs.get("recruiter_id")
        )
        if target_id and target_id != g.current_user_id:
            return jsonify({"error": "You can only access your own data"}), 403
        return f(*args, **kwargs)
    return wrapper


# ============ AUTHENTICATION ROUTES ============


@api.route('/auth/forgot-password', methods=['POST'])
@rate_limit(max_requests=3, window_seconds=900, key_by="email")
def forgot_password():
    """Send a password reset OTP to the user's email.

    Returns 200 even when the email is unregistered to prevent user
    enumeration.
    ---
    tags:
      - auth
    parameters:
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/ForgotPasswordRequest'
    responses:
      200:
        description: OTP sent (or intentionally ambiguous for unregistered emails)
        schema:
          $ref: '#/definitions/ForgotPasswordResponse'
      400:
        description: Email is required
        schema:
          $ref: '#/definitions/Error'
    """
    data = request.get_json()
    email = (data or {}).get('email', '').strip().lower()

    if not email:
        return jsonify({"error": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()

    # Return 200 even if email not found to prevent enumeration
    if not user:
        return jsonify({
            "message": "If that email is registered, an OTP has been sent."
        }), 200

    otp = str(random.randint(100000, 999999))
    otp_expires_at = datetime.utcnow() + timedelta(minutes=10)

    PasswordResetToken.query.filter_by(user_id=user.user_id, used=False).update({"used": True})
    db.session.flush()

    reset_token = PasswordResetToken(
        user_id=user.user_id,
        token=otp,
        expires_at=otp_expires_at,
    )
    db.session.add(reset_token)
    db.session.commit()

    name = user.name or email.split('@')[0]
    send_password_reset_otp(to=email, otp=otp, name=name)

    return jsonify({
        "message": "If that email is registered, an OTP has been sent."
    }), 200


@api.route('/auth/verify-reset-otp', methods=['POST'])
def verify_reset_otp():
    """Verify the OTP and return a temporary reset token for setting a new password.

    The returned reset_token is exchanged for a new password via
    /auth/reset-password.
    ---
    tags:
      - auth
    parameters:
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/VerifyOTPRequest'
    responses:
      200:
        description: OTP verified
        schema:
          $ref: '#/definitions/VerifyResetOTPResponse'
      400:
        description: Invalid or expired OTP
        schema:
          $ref: '#/definitions/Error'
      404:
        description: User not found
        schema:
          $ref: '#/definitions/Error'
    """
    data = request.get_json()
    email = (data or {}).get('email', '').strip().lower()
    otp = (data or {}).get('otp', '').strip()

    if not email or not otp:
        return jsonify({"error": "Email and OTP are required"}), 400

    if len(otp) != 6 or not otp.isdigit():
        return jsonify({"error": "OTP must be a 6-digit code"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    reset_token = PasswordResetToken.query.filter_by(
        user_id=user.user_id, token=otp, used=False
    ).first()

    if not reset_token:
        return jsonify({"error": "Invalid OTP. Please check and try again."}), 400

    if datetime.utcnow() > reset_token.expires_at:
        reset_token.used = True
        db.session.commit()
        return jsonify({"error": "OTP has expired. Please request a new one."}), 400

    # Issue a temporary reset token and overwrite the OTP
    temp_token = secrets.token_urlsafe(32)
    temp_expires_at = datetime.utcnow() + timedelta(minutes=30)
    reset_token.token = temp_token
    reset_token.expires_at = temp_expires_at
    db.session.commit()

    return jsonify({
        "message": "OTP verified successfully.",
        "reset_token": temp_token,
        "email": email,
    }), 200


@api.route('/auth/reset-password', methods=['POST'])
def reset_password():
    """Reset the password using a temp token (issued after OTP verification).
    ---
    tags:
      - auth
    parameters:
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/ResetPasswordRequest'
    responses:
      200:
        description: Password reset successfully
        schema:
          $ref: '#/definitions/ResetPasswordResponse'
      400:
        description: Invalid or expired token, or weak password
        schema:
          $ref: '#/definitions/Error'
      404:
        description: User not found
        schema:
          $ref: '#/definitions/Error'
    """
    data = request.get_json()
    token = (data or {}).get('token', '').strip()
    email = (data or {}).get('email', '').strip().lower()
    new_password = (data or {}).get('password', '')

    if not token or not new_password or not email:
        return jsonify({"error": "Token, email, and password are required"}), 400

    if len(new_password) < 8:
        return jsonify({"error": "Password must be at least 8 characters long"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    reset_token = PasswordResetToken.query.filter_by(
        user_id=user.user_id, token=token, used=False
    ).first()

    if not reset_token:
        return jsonify({"error": "Invalid or expired reset token."}), 400

    if datetime.utcnow() > reset_token.expires_at:
        reset_token.used = True
        db.session.commit()
        return jsonify({"error": "Reset token has expired. Please request a new OTP."}), 400

    user.password_hash = generate_password_hash(new_password)
    reset_token.used = True
    db.session.commit()

    return jsonify({"message": "Password has been reset successfully. You can now sign in."}), 200


@api.route('/auth/register', methods=['POST'])
@rate_limit(max_requests=5, window_seconds=3600, key_by="ip")
def register():
    """Register a new user (applicant or recruiter).

    Creates the account, sends a verification OTP, and returns a JWT.
    ---
    tags:
      - auth
    security: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/RegisterRequest'
    responses:
      201:
        description: User registered successfully
        schema:
          $ref: '#/definitions/AuthResponse'
      400:
        description: Missing fields, invalid role, or weak password
        schema:
          $ref: '#/definitions/Error'
      409:
        description: User already exists
        schema:
          $ref: '#/definitions/Error'
    """
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')
    name = data.get('name')

    if not email or not password or not role:
        return jsonify({"error": "Missing required fields"}), 400

    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters long"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "User already exists"}), 409

    if role not in ['applicant', 'recruiter']:
        return jsonify({"error": "Invalid role"}), 400

    hashed_password = generate_password_hash(password)

    if role == 'applicant':
        new_user = Applicant(
            email=email, name=name,
            password_hash=hashed_password, role=role
        )
    else:
        new_user = Recruiter(
            email=email, name=name,
            password_hash=hashed_password, role=role
        )

    db.session.add(new_user)
    db.session.flush()

    otp = str(random.randint(100000, 999999))
    otp_expires_at = datetime.utcnow() + timedelta(minutes=10)
    verification = EmailVerificationToken(
        user_id=new_user.user_id,
        token=otp,
        expires_at=otp_expires_at,
    )
    db.session.add(verification)
    db.session.commit()

    from metrics import increment
    increment(
        current_app._get_current_object(),
        "sipsetu_registrations_total",
        "Total user registrations by role",
        {"role": role},
    )

    send_verification_otp(to=email, otp=otp, name=name or email.split('@')[0])

    token = create_token(str(new_user.user_id), role)

    return jsonify({
        "message": "User registered successfully. Please check your email to verify your account.",
        "token": token,
        "user_id": str(new_user.user_id),
        "role": role,
        "name": name,
        "email": email,
        "email_verified": False,
    }), 201


@api.route('/auth/login', methods=['POST'])
def login():
    """Login and retrieve user credentials with JWT token.
    ---
    tags:
      - auth
    security: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/LoginRequest'
    responses:
      200:
        description: Login successful
        schema:
          $ref: '#/definitions/AuthResponse'
      400:
        description: Missing email or password
        schema:
          $ref: '#/definitions/Error'
      401:
        description: Invalid credentials
        schema:
          $ref: '#/definitions/Error'
    """
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Missing email or password"}), 400

    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters long"}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_token(str(user.user_id), user.role)

    return jsonify({
        "message": "Login successful",
        "token": token,
        "user_id": str(user.user_id),
        "role": user.role,
        "name": user.name,
        "email": user.email,
        "profile_image": user.profile_image,
        "email_verified": user.email_verified,
    }), 200


@api.route('/auth/me', methods=['GET'])
@require_auth
def auth_me():
    """Return the currently authenticated user's profile.

    Used by the frontend to validate the stored JWT on page reload.
    ---
    tags:
      - auth
    security:
      - BearerAuth: []
    responses:
      200:
        description: Current user profile
        schema:
          $ref: '#/definitions/MeResponse'
      401:
        description: Missing or invalid token
        schema:
          $ref: '#/definitions/Error'
      404:
        description: User not found
        schema:
          $ref: '#/definitions/Error'
    """
    user = User.query.get(g.current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    result = {
        "user_id": str(user.user_id),
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "phone": user.phone,
        "location": user.location,
        "profile_image": user.profile_image,
        "email_verified": user.email_verified,
        "created_at": user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None,
    }
    if user.role == 'recruiter':
        result.update({
            "company": user.company,
            "job_title": user.job_title,
        })
    return jsonify(result), 200


@api.route('/auth/verify-email', methods=['POST'])
@rate_limit(max_requests=5, window_seconds=600, key_by="email")
def verify_email():
    """Verify a user's email using an OTP code.
    ---
    tags:
      - auth
    security: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/VerifyEmailRequest'
    responses:
      200:
        description: Email verified successfully
        schema:
          $ref: '#/definitions/VerifyEmailResponse'
      400:
        description: Invalid or expired verification code
        schema:
          $ref: '#/definitions/Error'
      404:
        description: User not found
        schema:
          $ref: '#/definitions/Error'
    """
    data = request.get_json()
    email = (data or {}).get('email', '').strip().lower()
    otp = (data or {}).get('otp', '').strip()

    if not email or not otp:
        return jsonify({"error": "Email and verification code are required"}), 400

    if len(otp) != 6 or not otp.isdigit():
        return jsonify({"error": "Verification code must be a 6-digit code"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    verification = EmailVerificationToken.query.filter_by(
        user_id=user.user_id, token=otp, used=False
    ).first()
    if not verification:
        return jsonify({"error": "Invalid or expired verification code. Please check and try again."}), 400

    if datetime.utcnow() > verification.expires_at:
        verification.used = True
        db.session.commit()
        return jsonify({"error": "Verification code has expired. Please request a new one."}), 400

    verification.used = True
    user.email_verified = True
    db.session.commit()

    return jsonify({
        "message": "Email verified successfully! You can now access all features.",
        "email_verified": True,
    }), 200


@api.route('/auth/resend-verification', methods=['POST'])
@require_auth
@rate_limit(max_requests=3, window_seconds=900, key_by="user_id")
def resend_verification():
    """Resend the email verification OTP to the authenticated user.
    ---
    tags:
      - auth
    security:
      - BearerAuth: []
    responses:
      200:
        description: Verification email sent (or already verified)
        schema:
          $ref: '#/definitions/ResendVerificationResponse'
      401:
        description: Missing or invalid token
        schema:
          $ref: '#/definitions/Error'
      404:
        description: User not found
        schema:
          $ref: '#/definitions/Error'
    """
    user = User.query.get(g.current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.email_verified:
        return jsonify({"message": "Your email is already verified."}), 200

    EmailVerificationToken.query.filter_by(user_id=user.user_id, used=False).update({"used": True})
    db.session.flush()

    otp = str(random.randint(100000, 999999))
    otp_expires_at = datetime.utcnow() + timedelta(minutes=10)
    verification = EmailVerificationToken(
        user_id=user.user_id,
        token=otp,
        expires_at=otp_expires_at,
    )
    db.session.add(verification)
    db.session.commit()

    send_verification_otp(to=user.email, otp=otp, name=user.name or user.email.split('@')[0])

    return jsonify({
        "message": "Verification email sent. Please check your inbox.",
        # expires_at is UTC (datetime.utcnow) — the trailing Z lets clients
        # parse it as UTC instead of their local timezone.
        "expires_at": verification.expires_at.isoformat() + "Z",
    }), 200


@api.route('/auth/logout', methods=['POST'])
def logout():
    """Clear any server-side auth state for the current client.
    ---
    tags:
      - auth
    security: []
    responses:
      200:
        description: Logged out successfully
        schema:
          $ref: '#/definitions/LogoutResponse'
    """
    return jsonify({"message": "Logged out successfully"}), 200

# ============ PROFILE ROUTES ============

@api.route('/profile/<user_id>', methods=['GET', 'PUT'])
@_ownership_required
def profile(user_id):
    """Get or update user profile (ownership-scoped via JWT)."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    if request.method == 'GET':
        result = {
            "user_id": str(user.user_id),
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "phone": user.phone,
            "location": user.location,
            "profile_image": user.profile_image,
            "email_verified": user.email_verified
        }
        if user.role == 'recruiter':
            result.update({
                "company": user.company,
                "job_title": user.job_title
            })
        return jsonify(result), 200

    elif request.method == 'PUT':
        data = request.get_json()
        user.name = data.get('name', user.name)
        user.phone = data.get('phone', user.phone)
        user.location = data.get('location', user.location)
        if 'profile_image' in data:
            user.profile_image = data.get('profile_image')

        if user.role == 'recruiter':
            user.company = data.get('company', user.company)
            user.job_title = data.get('job_title', user.job_title)

        db.session.commit()
        return jsonify({"message": "Profile updated successfully"}), 200

@api.route('/ml/ranking/train', methods=['POST'])
@require_auth
def ml_ranking_train():
    """(Re)train the ML ranking model from historical ranked pairs.

    Training labels blend the deterministic heuristic with recruiter
    decisions (shortlisted/rejected applications). Returns training
    metrics or a not-enough-data message.
    """
    result = train_ranking_model()
    status_code = 200 if result.get("trained") else 422
    return jsonify(result), status_code


@api.route('/ml/ranking/status', methods=['GET'])
@require_auth
def ml_ranking_status():
    """Report whether the ML ranking model is trained and its metrics."""
    return jsonify(get_ranking_model_status()), 200


@api.route('/public/preview', methods=['GET'])
def public_preview():
    """Return a public, database-backed snapshot for guests."""
    latest_jobs = Job.query.order_by(Job.created_at.desc()).limit(4).all()
    latest_rankings = Ranking.query.order_by(Ranking.matching_score.desc()).limit(4).all()

    total_jobs = Job.query.count()
    total_recruiters = Recruiter.query.count()
    total_applicants = Applicant.query.count()
    total_resumes = Resume.query.count()

    return jsonify({
        "stats": {
            "jobs": total_jobs,
            "recruiters": total_recruiters,
            "applicants": total_applicants,
            "resumes": total_resumes,
        },
        "recent_jobs": [format_job(job) for job in latest_jobs],
        "top_candidates": [format_candidate_preview(ranking) for ranking in latest_rankings],
    }), 200

# ============ JOB POSTING ROUTES ============

@api.route('/jobs', methods=['GET'])
def jobs():
    """List all jobs (public)."""
    # GET — supports filters: recruiter_id, search, job_type, experience_level,
    # location, salary_min, salary_max, skill. On /api/v1 also ?sort= and
    # cursor pagination (?limit=, ?cursor=) — Phase 4.2.
    recruiter_id = request.args.get('recruiter_id')
    search_q = (request.args.get('search') or '').strip().lower()
    job_type_filter = (request.args.get('job_type') or '').strip().lower()
    exp_level_filter = (request.args.get('experience_level') or '').strip().lower()
    location_filter = (request.args.get('location') or '').strip().lower()
    salary_min_filter = request.args.get('salary_min', type=float)
    salary_max_filter = request.args.get('salary_max', type=float)
    skill_filter = (request.args.get('skill') or '').strip().lower()

    query = Job.query
    if recruiter_id:
        query = query.filter_by(recruiter_id=recruiter_id)
    if job_type_filter:
        query = query.filter(Job.job_type == job_type_filter)
    if exp_level_filter:
        query = query.filter(Job.experience_level == exp_level_filter)
    if location_filter and location_filter != "all":
        query = query.filter(Job.location.ilike(f'%{location_filter}%'))
    if salary_min_filter is not None:
        query = query.filter(or_(Job.salary_max.is_(None), Job.salary_max >= salary_min_filter))
    if salary_max_filter is not None:
        query = query.filter(or_(Job.salary_min.is_(None), Job.salary_min <= salary_max_filter))
    if skill_filter:
        requested_skills = [s.strip() for s in skill_filter.split(',') if s.strip()]
        for s in requested_skills:
            skill_obj = Skill.query.filter_by(skill_name=s).first()
            if skill_obj:
                query = query.filter(Job.skills.any(Skill.skill_id == skill_obj.skill_id))

    fts_active = False
    fts_query = None
    if search_q:
        fts_active = db.engine.dialect.name == 'postgresql' and len(search_q) >= 3
        if fts_active:
            # Postgres full-text search over the tsvector column (migration 005).
            fts_query = func.plainto_tsquery('english', search_q)
            query = query.filter(Job.search_vector.op('@@')(fts_query))
        else:
            # Fallback: leading-wildcard ILIKE — used on SQLite (dev/tests) and
            # for short terms where the pg_trgm GIN indexes cannot help.
            query = query.filter(
                or_(
                    Job.title.ilike(f'%{search_q}%'),
                    Job.location.ilike(f'%{search_q}%'),
                    Job.job_type.ilike(f'%{search_q}%'),
                )
            )

    # Ordering — stable keyset (primary column + id tiebreaker). While
    # full-text searching, relevance (ts_rank) wins over the ?sort= param.
    sort = (request.args.get('sort') or '-created_at').strip().lower()
    sort_map = {
        'created_at': (Job.created_at, Job.job_id, False),
        '-created_at': (Job.created_at, Job.job_id, True),
        'title': (Job.title, Job.job_id, False),
        '-title': (Job.title, Job.job_id, True),
    }
    if fts_active:
        rank_expr = func.ts_rank(Job.search_vector, fts_query).label('search_rank')
        query = query.order_by(
            rank_expr.desc(), Job.created_at.desc(), Job.job_id.desc(),
        )
    else:
        sort_col, id_col, descending = sort_map.get(sort, sort_map['-created_at'])
        query = query.order_by(
            sort_col.desc() if descending else sort_col.asc(),
            id_col.desc() if descending else id_col.asc(),
        )

    if is_v1_request():
        # Canonical /api/v1 — cursor (keyset) pagination + {data, meta} envelope.
        limit = parse_limit(20)
        cursor_values = decode_cursor(request.args.get('cursor'))
        if fts_active:
            # Relevance ranking — keyset seek over (search_rank, created_at,
            # job_id); ts_rank is computed per row, so the cursor carries it
            # and the WHERE compares the same expression.
            fts_q = query.add_columns(rank_expr)
            if cursor_values:
                fts_q = keyset_filter(
                    fts_q, [rank_expr, Job.created_at, Job.job_id],
                    cursor_values, descending=True,
                )
            rows = fts_q.limit(limit + 1).all()
            has_more = len(rows) > limit
            page_rows = rows[:limit]
            page_items = [row[0] for row in page_rows]
            next_cursor = None
            if has_more and page_rows:
                last = page_rows[-1]
                next_cursor = encode_cursor(
                    last[1], last[0].created_at, last[0].job_id,
                )
        else:
            if cursor_values:
                query = keyset_filter(
                    query, [sort_col, id_col], cursor_values, descending=descending
                )
            rows = query.limit(limit + 1).all()
            has_more = len(rows) > limit
            page_items = rows[:limit]
            next_cursor = None
            if has_more and page_items:
                last = page_items[-1]
                next_cursor = encode_cursor(
                    getattr(last, sort_col.key), getattr(last, id_col.key)
                )
        return jsonify(build_envelope(
            [format_job(job) for job in page_items],
            total=query.count(), limit=limit,
            next_cursor=next_cursor, has_more=has_more,
        )), 200

    # Legacy /api — offset pagination with the historical response shape.
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "total": pagination.total,
        "page": page,
        "per_page": per_page,
        "pages": pagination.pages,
        "jobs": [format_job(job) for job in pagination.items],
    }), 200


@api.route('/jobs', methods=['POST'])
@require_role('recruiter')
def create_job():
    """Create a new job posting (recruiter only)."""
    data = request.get_json()
    title = data.get('title')
    skills = data.get('skills', [])
    description = data.get('description', '')
    location = data.get('location', '')
    job_type = data.get('job_type', '')
    experience_level = data.get('experience_level', '')
    salary_min = data.get('salary_min')
    salary_max = data.get('salary_max')
    if not title:
        return jsonify({"error": "Missing job title"}), 400

    new_job = Job(
        recruiter_id=g.current_user_id,
        title=title,
        description=description,
        location=location,
        job_type=job_type,
        experience_level=experience_level,
        salary_min=float(salary_min) if salary_min else None,
        salary_max=float(salary_max) if salary_max else None
    )
    for skill_name in skills:
        if not skill_name.strip():
            continue
        skill = Skill.query.filter_by(skill_name=skill_name.lower()).first()
        if not skill:
            skill = Skill(skill_name=skill_name.lower())
            db.session.add(skill)
        if skill not in new_job.skills:
            new_job.skills.append(skill)
    db.session.add(new_job)
    set_job_search_vector(new_job)
    db.session.commit()
    create_rankings_for_job(new_job.job_id)
    return jsonify({
        "message": "Job posted successfully",
        "job_id": str(new_job.job_id),
        "title": new_job.title,
        "skills": [s.skill_name for s in new_job.skills]
    }), 201

@api.route('/jobs/<job_id>/apply', methods=['POST'])
@require_role('applicant')
def apply_for_job(job_id):
    """Record an applicant's interest in a job."""
    job = Job.query.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    applicant_id = g.current_user_id
    applicant = Applicant.query.get(applicant_id)
    if not applicant:
        return jsonify({"error": "Applicant not found"}), 404

    application = JobApplication.query.filter_by(
        job_id=job_id, applicant_id=applicant_id
    ).first()
    created = False
    if not application:
        application = JobApplication(job_id=job_id, applicant_id=applicant_id)
        db.session.add(application)
        created = True

        db.session.add(Notification(
            user_id=applicant_id,
            title="Application Submitted",
            message=f"You have successfully applied for '{job.title}'.",
            type="success",
            related_job_id=job_id,
        ))
        db.session.add(Notification(
            user_id=job.recruiter_id,
            title="New Job Application",
            message=f"{applicant.name} has applied for your job '{job.title}'.",
            type="info",
            related_job_id=job_id,
        ))
        db.session.flush()
        _emit_ws(applicant_id, "Application Submitted", f"You have successfully applied for '{job.title}'.", "success", job_id)
        _emit_ws(str(job.recruiter_id), "New Job Application", f"{applicant.name} has applied for your job '{job.title}'.", "info", job_id)

    create_rankings_for_job(job_id)
    db.session.commit()

    if created:
        from metrics import increment
        increment(
            current_app._get_current_object(),
            "sipsetu_applications_total",
            "Total job applications submitted by job type",
            {"job_type": job.job_type or "unspecified"},
        )

    latest_resume = Resume.query.filter_by(applicant_id=applicant_id)\
        .order_by(Resume.uploaded_at.desc()).first()

    return jsonify({
        "message": "Job application saved successfully" if created
                     else "Job application already exists",
        "job_id": str(job.job_id),
        "applicant_id": str(applicant.user_id),
        "application_id": str(application.application_id),
        "has_resume": latest_resume is not None,
    }), 200 if not created else 201


@api.route('/applicants/<applicant_id>/applications', methods=['GET'])
@_ownership_required
def get_applicant_applications(applicant_id):
    """Get all applications for the applicant with full job details, status, and matching scores."""
    applicant = Applicant.query.get(applicant_id)
    if not applicant:
        return jsonify({"error": "Applicant not found"}), 404

    applications = JobApplication.query.filter_by(applicant_id=applicant_id)\
        .order_by(JobApplication.applied_at.desc()).all()

    latest_resume = Resume.query.filter_by(applicant_id=applicant_id)\
        .order_by(Resume.uploaded_at.desc()).first()

    result = []
    for app in applications:
        job = Job.query.get(app.job_id)
        if not job:
            continue

        job_data = format_job(job)

        score = 0.0
        if latest_resume:
            score = float(_compute_job_match_score(latest_resume, job) or 0.0)

        result.append({
            "application_id": str(app.application_id),
            "job_id": str(job.job_id),
            "title": job.title,
            "description": job.description,
            "location": job.location or "",
            "job_type": job.job_type or "",
            "experience_level": job.experience_level or "",
            "salary_min": job_data.get("salary_min"),
            "salary_max": job_data.get("salary_max"),
            "skills": job_data.get("skills", []),
            "recruiter_name": job.recruiter.name or "",
            "recruiter_company": job.recruiter.company or "",
            "status": app.status,
            "applied_at": app.applied_at.isoformat() if app.applied_at else None,
            "matching_score": round(score, 2),
        })

    if is_v1_request():
        return jsonify(build_envelope(
            result, total=len(result), limit=len(result),
            applicant_id=str(applicant.user_id),
        )), 200
    return jsonify({
        "applicant_id": str(applicant.user_id),
        "total": len(result),
        "applications": result,
    }), 200


@api.route('/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    """Get details of a specific job (public)."""
    job = Job.query.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(format_job(job)), 200


@api.route('/jobs/<job_id>', methods=['PUT'])
@require_auth
def update_job(job_id):
    """Update a job posting (recruiter who owns the job only)."""
    job = Job.query.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    if str(job.recruiter_id) != g.current_user_id:
        return jsonify({"error": "You can only edit your own job postings"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    if 'title' in data:
        job.title = data['title']
    if 'description' in data:
        job.description = data.get('description', '')
    if 'location' in data:
        job.location = data.get('location', '')
    if 'job_type' in data:
        job.job_type = data.get('job_type', '')
    if 'experience_level' in data:
        job.experience_level = data.get('experience_level', '')
    if 'salary_min' in data:
        job.salary_min = float(data['salary_min']) if data['salary_min'] else None
    if 'salary_max' in data:
        job.salary_max = float(data['salary_max']) if data['salary_max'] else None

    if 'skills' in data and isinstance(data['skills'], list):
        job.skills.clear()
        db.session.flush()
        for skill_name in data['skills']:
            if not skill_name.strip():
                continue
            skill = Skill.query.filter_by(skill_name=skill_name.lower()).first()
            if not skill:
                skill = Skill(skill_name=skill_name.lower())
                db.session.add(skill)
            if skill not in job.skills:
                job.skills.append(skill)

    set_job_search_vector(job)
    db.session.commit()
    create_rankings_for_job(job.job_id)

    return jsonify({
        "message": "Job updated successfully",
        "job_id": str(job.job_id),
        "title": job.title,
        "skills": [s.skill_name for s in job.skills],
    }), 200


@api.route('/jobs/<job_id>', methods=['DELETE'])
@require_auth
def delete_job(job_id):
    """Delete a job posting (recruiter who owns the job only)."""
    job = Job.query.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    if str(job.recruiter_id) != g.current_user_id:
        return jsonify({"error": "You can only delete your own job postings"}), 403

    db.session.delete(job)
    db.session.commit()

    return jsonify({"message": "Job deleted successfully"}), 200


# ============ RESUME & MATCHING ROUTES ============

@api.route('/resumes/<resume_id>', methods=['GET', 'PUT', 'DELETE'])
@require_auth
def resume_detail(resume_id):
    """Fetch, update, or delete a single resume by id."""
    resume = Resume.query.get(resume_id)
    if not resume:
        return jsonify({"error": "Resume not found"}), 404

    if str(resume.applicant_id) != g.current_user_id:
        return jsonify({"error": "You can only access your own resume"}), 403

    if request.method == 'GET':
        return jsonify({
            "resume_id": str(resume.resume_id),
            "applicant_id": str(resume.applicant_id),
            "raw_text": resume.raw_text or "",
            "file_path": resume.file_path or "",
            "uploaded_at": resume.uploaded_at.isoformat() if resume.uploaded_at else None,
            "skills": [s.skill_name for s in resume.skills],
        }), 200

    if request.method == 'DELETE':
        applicant_id = str(resume.applicant_id)
        db.session.delete(resume)
        db.session.commit()
        create_rankings_for_resume_after_delete(applicant_id)
        return jsonify({"message": "Resume deleted successfully"}), 200

    data = request.get_json(silent=True) or {}
    new_text = data.get('raw_text')
    new_file_path = data.get('file_path')
    client_skills = data.get('skills')

    if new_text is None or not isinstance(new_text, str):
        return jsonify({"error": "Missing or invalid 'raw_text'"}), 400

    resume.raw_text = new_text
    if new_file_path is not None:
        resume.file_path = new_file_path

    if isinstance(client_skills, list) and all(isinstance(s, str) for s in client_skills):
        extracted_skills = [s.strip().lower() for s in client_skills if s.strip()]
    else:
        extracted_skills = extract_skills_from_text(new_text)
    resume.skills.clear()
    db.session.flush()
    for skill_name in extracted_skills:
        skill = Skill.query.filter_by(skill_name=skill_name.lower()).first()
        if not skill:
            skill = Skill(skill_name=skill_name.lower())
            db.session.add(skill)
        if skill not in resume.skills:
            resume.skills.append(skill)

    db.session.flush()
    create_rankings_for_resume(resume.resume_id, str(resume.applicant_id))
    db.session.commit()

    return jsonify({
        "message": "Resume updated successfully",
        "resume_id": str(resume.resume_id),
        "skills_extracted": extracted_skills,
        "skill_count": len(extracted_skills),
    }), 200


@api.route('/resumes', methods=['POST', 'GET'])
@require_role('applicant')
def resumes():
    """Upload a new resume or list the authenticated applicant's resumes."""
    applicant_id = g.current_user_id

    if request.method == 'POST':
        data = request.get_json()
        raw_text = data.get('raw_text', '')
        client_skills = data.get('skills')

        applicant = Applicant.query.get(applicant_id)
        if not applicant:
            return jsonify({"error": "Only applicants can upload resumes"}), 403

        if isinstance(client_skills, list) and all(isinstance(s, str) for s in client_skills):
            extracted_skills = [s.strip().lower() for s in client_skills if s.strip()]
        else:
            extracted_skills = extract_skills_from_text(raw_text)

        new_resume = Resume(applicant_id=applicant_id, raw_text=raw_text)
        for skill_name in extracted_skills:
            skill = Skill.query.filter_by(skill_name=skill_name.lower()).first()
            if not skill:
                skill = Skill(skill_name=skill_name.lower())
                db.session.add(skill)
            if skill not in new_resume.skills:
                new_resume.skills.append(skill)
        db.session.add(new_resume)
        db.session.flush()
        create_rankings_for_resume(new_resume.resume_id, applicant_id)
        db.session.commit()

        return jsonify({
            "message": "Resume uploaded successfully",
            "resume_id": str(new_resume.resume_id),
            "skills_extracted": extracted_skills,
        }), 201

    # GET -- list resumes for authenticated applicant
    resumes_list = Resume.query.filter_by(applicant_id=applicant_id)\
        .order_by(Resume.uploaded_at.desc()).all()
    payload = [{
        "resume_id": str(r.resume_id),
        "uploaded_at": r.uploaded_at.isoformat(),
        "file_path": r.file_path or "",
        "skills": [s.skill_name for s in r.skills],
    } for r in resumes_list]
    if is_v1_request():
        return jsonify(build_envelope(
            payload, total=len(payload), limit=len(payload),
        )), 200
    return jsonify(payload), 200


@api.route('/resumes/upload-pdf', methods=['POST'])
@require_role('applicant')
def upload_resume_pdf():
    """Upload a PDF resume, extract text & skills, store in DB."""
    applicant_id = g.current_user_id
    applicant = Applicant.query.get(applicant_id)
    if not applicant:
        return jsonify({"error": "Applicant not found"}), 404

    file = request.files.get('file')
    if not file or file.filename == '':
        return jsonify({"error": "No file uploaded"}), 400
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Only PDF files are supported"}), 400

    # File size validation (10MB max)
    max_size = 10 * 1024 * 1024  # 10MB
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning
    if file_size > max_size:
        return jsonify({"error": "File size exceeds maximum allowed (10MB)"}), 400

    try:
        file_bytes = file.read()
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = "".join(page.get_text() for page in doc).strip()
        doc.close()
    except Exception as e:
        # A corrupt/invalid PDF is a client error (400), not a server failure.
        return jsonify({"error": f"Invalid or corrupted PDF file: {e!s}"}), 400

    if not text:
        return jsonify({"error": "The PDF has no readable text"}), 400

    try:
        extracted_skills = extract_skills_from_text(text)

        # Upload to storage (S3/MinIO/local)
        storage = get_storage()
        upload_result = storage.upload_file(
            file_bytes if isinstance(file_bytes, bytes) else file_bytes,
            file.filename,
            content_type='application/pdf',
            prefix='resumes'
        )

        # Keep only the latest resume per applicant
        for old in Resume.query.filter_by(applicant_id=applicant_id).all():
            db.session.delete(old)
        db.session.flush()

        new_resume = Resume(
            applicant_id=applicant_id,
            raw_text=text,
            file_path=upload_result.get('key', file.filename)  # Store storage key
        )
        for skill_name in extracted_skills:
            skill = Skill.query.filter_by(skill_name=skill_name.lower()).first()
            if not skill:
                skill = Skill(skill_name=skill_name.lower())
                db.session.add(skill)
            if skill not in new_resume.skills:
                new_resume.skills.append(skill)
        db.session.add(new_resume)
        db.session.flush()
        create_rankings_for_resume(new_resume.resume_id, applicant_id)
        db.session.commit()

        return jsonify({
            "message": "Resume uploaded and analyzed successfully",
            "resume_id": str(new_resume.resume_id),
            "filename": file.filename,
            "uploaded_at": new_resume.uploaded_at.isoformat(),
            "skills_extracted": extracted_skills,
            "skill_count": len(extracted_skills),
            "file_url": upload_result.get('url'),
            "storage_provider": upload_result.get('provider'),
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error processing PDF: {e!s}"}), 500


@api.route('/resumes/presigned-upload-url', methods=['POST'])
@require_role('applicant')
def get_presigned_upload_url():
    """Generate a presigned S3 URL for direct-to-S3 resume upload.

    The frontend uploads the file directly to S3 (bypassing the backend),
    then calls POST /resumes/confirm-upload to record the upload.
    Falls back gracefully for local storage providers.

    ---
    tags:
      - resumes
    security:
      - BearerAuth: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            filename:
              type: string
              description: Original filename (used for extension)
            content_type:
              type: string
              default: application/pdf
    responses:
      200:
        description: Presigned URL and metadata
      400:
        description: Missing filename
    """
    data = request.get_json(silent=True) or {}
    filename = (data.get('filename') or '').strip()
    content_type = data.get('content_type', 'application/pdf')

    if not filename:
        return jsonify({"error": "filename is required"}), 400

    ext = os.path.splitext(filename)[1] or '.pdf'
    storage = get_storage()
    key = f"resumes/{g.current_user_id}/{uuid.uuid4().hex}{ext}"

    result = storage.get_presigned_upload_url(
        key=key,
        content_type=content_type,
        expires_in=3600,
    )

    if 'error' in result:
        return jsonify({
            "error": result['error'],
            "fallback": True,
            "message": "Direct upload not available; use multipart upload instead",
        }), 200

    return jsonify({
        "upload_url": result['url'],
        "key": result['key'],
        "method": result.get('method', 'PUT'),
        "headers": result.get('headers', {}),
        "expires_in": result.get('expires_in', 3600),
        "storage_provider": storage.provider,
    }), 200


@api.route('/resumes/confirm-upload', methods=['POST'])
@require_role('applicant')
def confirm_upload():
    """Confirm a direct-to-S3 upload by extracting text & storing the resume.

    Called after the frontend has uploaded the file to S3 using the
    presigned URL from GET /resumes/presigned-upload-url.

    ---
    tags:
      - resumes
    security:
      - BearerAuth: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            key:
              type: string
              description: S3 storage key from presigned upload response
            filename:
              type: string
              description: Original filename for metadata
    responses:
      201:
        description: Resume confirmed and analyzed
      400:
        description: Missing key or filename
    """
    data = request.get_json(silent=True) or {}
    key = (data.get('key') or '').strip()
    filename = (data.get('filename') or 'resume.pdf').strip()

    if not key:
        return jsonify({"error": "key is required"}), 400

    applicant_id = g.current_user_id
    applicant = Applicant.query.get(applicant_id)
    if not applicant:
        return jsonify({"error": "Applicant not found"}), 404

    storage = get_storage()
    try:
        # Download the file from storage for text extraction
        if storage.provider in ('s3', 'minio') and storage._client:
            import io
            buf = io.BytesIO()
            storage._client.download_fileobj(storage.bucket, key, buf)
            file_bytes = buf.getvalue()
        else:
            return jsonify({"error": "Confirm-upload requires S3/MinIO storage"}), 400

        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = "".join(page.get_text() for page in doc).strip()
        doc.close()
    except Exception as e:
        return jsonify({"error": f"Error reading uploaded file: {e!s}"}), 400

    if not text:
        return jsonify({"error": "The PDF has no readable text"}), 400

    extracted_skills = extract_skills_from_text(text)

    # Keep only the latest resume per applicant
    for old in Resume.query.filter_by(applicant_id=applicant_id).all():
        db.session.delete(old)
    db.session.flush()

    new_resume = Resume(
        applicant_id=applicant_id,
        raw_text=text,
        file_path=key,
    )
    for skill_name in extracted_skills:
        skill = Skill.query.filter_by(skill_name=skill_name.lower()).first()
        if not skill:
            skill = Skill(skill_name=skill_name.lower())
            db.session.add(skill)
        if skill not in new_resume.skills:
            new_resume.skills.append(skill)
    db.session.add(new_resume)
    db.session.flush()
    create_rankings_for_resume(new_resume.resume_id, applicant_id)
    db.session.commit()

    return jsonify({
        "message": "Resume upload confirmed and analyzed successfully",
        "resume_id": str(new_resume.resume_id),
        "filename": filename,
        "uploaded_at": new_resume.uploaded_at.isoformat(),
        "skills_extracted": extracted_skills,
        "skill_count": len(extracted_skills),
        "file_url": storage.get_url(key),
        "storage_provider": storage.provider,
    }), 201


def _compute_job_match_score(resume, job):
    if not resume or not job:
        return 0.0
    return calculate_ranking_score(resume, job)


def _resume_strength(raw_text, skill_count, avg_score, missing_count):
    """Composite 0-100 resume strength with a sub-score breakdown.

    Weights: content depth 30, skill coverage 25, match quality 30,
    gap closure 15. Pass missing_count=None when no target roles were
    evaluated (no resume or no jobs), in which case the gap-closure
    bonus is skipped so a resume-less user doesn't get a fake score.
    Returns a dict with the rounded total plus the four component
    scores so the dashboard can explain why the score is what it is.
    """
    text_len = len((raw_text or "").strip())

    # Content depth (0-30): real text is the backbone of a resume.
    if text_len >= 2000:
        content_score = 30
    elif text_len >= 1000:
        content_score = 22
    elif text_len >= 500:
        content_score = 14
    elif text_len >= 100:
        content_score = 6
    else:
        content_score = 0

    # Skill coverage (0-25): more extracted skills, up to a point.
    if skill_count >= 15:
        skills_score = 25
    elif skill_count >= 10:
        skills_score = 20
    elif skill_count >= 6:
        skills_score = 14
    elif skill_count >= 3:
        skills_score = 8
    elif skill_count > 0:
        skills_score = 4
    else:
        skills_score = 0

    # Match quality (0-30): how well the resume scores against target roles.
    if avg_score >= 85:
        match_score = 30
    elif avg_score >= 70:
        match_score = 24
    elif avg_score >= 55:
        match_score = 18
    elif avg_score >= 40:
        match_score = 12
    elif avg_score >= 20:
        match_score = 6
    else:
        match_score = 0

    # Gap closure (0-15): fewer missing skills for target roles = stronger.
    # Skip entirely when no target roles were evaluated (missing_count=None).
    if missing_count is None:
        gap_score = 0
    elif missing_count == 0:
        gap_score = 15
    elif missing_count <= 2:
        gap_score = 12
    elif missing_count <= 4:
        gap_score = 8
    elif missing_count <= 6:
        gap_score = 4
    else:
        gap_score = 0

    total = min(100, int(round(content_score + skills_score + match_score + gap_score)))
    return {
        "content": content_score,
        "skills": skills_score,
        "match": match_score,
        "gaps": gap_score,
        "total": total,
    }


@api.route('/applicants/<applicant_id>/matched-jobs', methods=['GET'])
@_ownership_required
def get_matched_jobs(applicant_id):
    """Return ALL job postings ranked by match score against the applicant's resume."""
    applicant = Applicant.query.get(applicant_id)
    if not applicant:
        return jsonify({"error": "Applicant not found"}), 404

    latest_resume = Resume.query.filter_by(applicant_id=applicant_id)\
        .order_by(Resume.uploaded_at.desc()).first()
    if not latest_resume:
        if is_v1_request():
            return jsonify(build_envelope(
                [], total=0, limit=parse_limit(50), resume_id=None,
            )), 200
        return jsonify({
            "total": 0, "page": 1, "per_page": 20, "pages": 0,
            "resume_id": None, "matched_jobs": [],
        }), 200

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    min_score = request.args.get('min_score', 0, type=float)
    search = (request.args.get('search') or '').strip().lower()
    location = (request.args.get('location') or '').strip().lower()
    job_type_filter = (request.args.get('job_type') or '').strip().lower()
    exp_level_filter = (request.args.get('experience_level') or '').strip().lower()
    salary_min_filter = request.args.get('salary_min', type=float)
    salary_max_filter = request.args.get('salary_max', type=float)
    skill_filter = (request.args.get('skill') or '').strip().lower()

    all_jobs = Job.query.order_by(Job.created_at.desc()).all()
    applied_map = {
        str(a.job_id): str(a.application_id)
        for a in JobApplication.query.filter_by(applicant_id=applicant_id).all()
    }

    enriched = []
    for job in all_jobs:
        score = _compute_job_match_score(latest_resume, job)
        if score < min_score:
            continue

        # Apply server-side filters before enriching
        if job_type_filter and (job.job_type or '').lower() != job_type_filter:
            continue
        if exp_level_filter and (job.experience_level or '').lower() != exp_level_filter:
            continue
        if salary_min_filter is not None and (job.salary_max or 0) < salary_min_filter:
            continue
        if salary_max_filter is not None and (job.salary_min or 0) > salary_max_filter:
            continue
        if skill_filter:
            job_skill_names = {s.skill_name.lower() for s in job.skills}
            requested_skills = [s.strip() for s in skill_filter.split(',') if s.strip()]
            if not any(s in job_skill_names for s in requested_skills):
                continue

        job_data = format_job(job)
        job_data["matching_score"] = round(float(score or 0.0), 2)
        job_data["applied"] = str(job.job_id) in applied_map
        job_data["application_id"] = applied_map.get(str(job.job_id))
        enriched.append(job_data)

    if search:
        enriched = [j for j in enriched
                    if search in (j.get("title") or "").lower()
                    or search in (j.get("recruiter_company") or "").lower()
                    or search in (j.get("recruiter_name") or "").lower()]
    if location and location != "all":
        enriched = [j for j in enriched
                    if location in (j.get("location") or "").lower()]

    # Ordering — ?sort= matching_score|-matching_score|created_at|-created_at
    sort = (request.args.get('sort') or '-matching_score').strip().lower()
    if sort not in ('matching_score', '-matching_score', 'created_at', '-created_at'):
        sort = '-matching_score'
    descending = sort.startswith('-')
    field = sort.lstrip('-')

    def order_key(job):
        if field == 'created_at':
            return ((job.get("created_at") or ""), (job.get("matching_score") or 0.0), (job.get("job_id") or ""))
        return ((job.get("matching_score") or 0.0), (job.get("created_at") or ""), (job.get("job_id") or ""))

    enriched.sort(key=order_key, reverse=descending)

    if is_v1_request():
        # Canonical /api/v1 — cursor pagination over the ranked list.
        limit = parse_limit(50)
        cursor_values = decode_cursor(request.args.get('cursor'))
        if cursor_values:
            enriched = in_memory_after(
                enriched, order_key, cursor_values, descending=descending
            )
        has_more = len(enriched) > limit
        page_items = enriched[:limit]
        next_cursor = None
        if has_more and page_items:
            next_cursor = encode_cursor(*order_key(page_items[-1]))
        return jsonify(build_envelope(
            page_items,
            total=len(enriched), limit=limit,
            next_cursor=next_cursor, has_more=has_more,
            resume_id=str(latest_resume.resume_id),
        )), 200

    # Legacy /api — offset pagination with the historical response shape.
    total = len(enriched)
    pages = max(1, (total + per_page - 1) // per_page) if total else 0
    start = (page - 1) * per_page

    return jsonify({
        "total": total, "page": page, "per_page": per_page, "pages": pages,
        "resume_id": str(latest_resume.resume_id),
        "matched_jobs": enriched[start:start + per_page],
    }), 200


@api.route('/applicants/<applicant_id>/dashboard', methods=['GET'])
@_ownership_required
def applicant_dashboard(applicant_id):
    """Get dashboard stats for an applicant."""
    applicant = Applicant.query.get(applicant_id)
    if not applicant:
        return jsonify({"error": "Applicant not found"}), 404

    latest_resume = Resume.query.filter_by(applicant_id=applicant_id)\
        .order_by(Resume.uploaded_at.desc()).first()
    avg_score = 0.0
    top_jobs = []
    recent_jobs = [format_job(j) for j in Job.query.order_by(Job.created_at.desc()).limit(6).all()]
    skill_count = 0
    missing_skills = []

    if latest_resume:
        skill_count = len(latest_resume.skills)
        all_jobs = Job.query.order_by(Job.created_at.desc()).all()
        scored = []
        for job in all_jobs:
            s = _compute_job_match_score(latest_resume, job)
            scored.append((s, job))
        scored.sort(key=lambda p: p[0], reverse=True)
        top4 = scored[:4]
        if top4:
            scores = [s for s, _ in top4 if s]
            avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
            for score, job in top4:
                top_jobs.append(dict(
                    job_id=str(job.job_id), title=job.title,
                    recruiter_name=job.recruiter.name or "",
                    recruiter_company=job.recruiter.company or "",
                    location=job.location or "",
                    matching_score=round(float(score or 0.0), 2),
                    skills=[s.skill_name for s in job.skills],
                ))
            resume_skills = {s.skill_name for s in latest_resume.skills}
            for _, job in top4:
                job_skills = {s.skill_name for s in job.skills}
                missing_skills.extend(job_skills - resume_skills)
            missing_skills = list(set(missing_skills))[:6]

    strength = _resume_strength(
        latest_resume.raw_text if latest_resume else None,
        skill_count,
        avg_score,
        len(missing_skills) if top_jobs else None,
    )
    resume_strength = strength["total"]
    resume_strength_breakdown = {
        "content": strength["content"],
        "skills": strength["skills"],
        "match": strength["match"],
        "gaps": strength["gaps"],
    }

    upcoming_interviews = Interview.query.filter_by(applicant_id=applicant_id)\
        .filter(Interview.status.in_(['pending', 'confirmed']))\
        .order_by(Interview.scheduled_at.asc()).limit(5).all()

    return jsonify({
        "name": applicant.name or applicant.email,
        "email": applicant.email,
        "has_resume": latest_resume is not None,
        "email_verified": applicant.email_verified,
        "resume_uploaded_at": latest_resume.uploaded_at.isoformat() if latest_resume else None,
        "resume_filename": latest_resume.file_path if latest_resume else None,
        "skill_count": skill_count,
        "resume_strength": resume_strength,
        "resume_strength_breakdown": resume_strength_breakdown,
        "avg_match_score": avg_score,
        "top_jobs": top_jobs,
        "recent_jobs": recent_jobs,
        "missing_skills": missing_skills,
        "upcoming_interviews": [{
            "interview_id": str(iv.interview_id),
            "job_title": iv.job.title if iv.job else "",
            "recruiter_name": iv.recruiter.name or iv.recruiter.email,
            "recruiter_company": iv.recruiter.company or "",
            "scheduled_at": iv.scheduled_at.isoformat(),
            "duration_minutes": iv.duration_minutes,
            "status": iv.status,
            "meeting_link": iv.meeting_link or "",
            "notes": iv.notes or "",
        } for iv in upcoming_interviews],
    }), 200


@api.route('/applicants/<applicant_id>/skill-gap', methods=['GET'])
@_ownership_required
def applicant_skill_gap(applicant_id):
    """Compare applicant resume skills vs their target roles (matched jobs)."""
    applicant = Applicant.query.get(applicant_id)
    if not applicant:
        return jsonify({"error": "Applicant not found"}), 404

    job_id = request.args.get('job_id')
    latest_resume = Resume.query.filter_by(applicant_id=applicant_id)\
        .order_by(Resume.uploaded_at.desc()).first()
    if not latest_resume:
        return jsonify({"error": "No resume found. Please upload a resume first."}), 404

    # Skills the applicant is actively tracking toward closing (persisted).
    progress_map = {
        p.skill_name: p.status
        for p in SkillProgress.query.filter_by(applicant_id=applicant_id).all()
    }

    resume_skills = {s.skill_name for s in latest_resume.skills}

    # Rank every job against the resume (same scoring as matched-jobs) so the
    # page only surfaces roles that are actually relevant to the applicant.
    all_jobs = Job.query.order_by(Job.created_at.desc()).all()
    scored = []
    for job in all_jobs:
        score = float(_compute_job_match_score(latest_resume, job) or 0.0)
        if score > 0:
            scored.append((score, job))
    scored.sort(key=lambda p: p[0], reverse=True)

    matched_jobs = [{
        "job_id": str(job.job_id),
        "title": job.title,
        "company": job.recruiter.company or job.recruiter.name or "",
        "matching_score": round(score, 1),
    } for score, job in scored[:10]]

    considered_jobs = scored[:5]
    considered = [{
        "job_id": str(job.job_id),
        "title": job.title,
        "company": job.recruiter.company or job.recruiter.name or "",
        "matching_score": round(score, 1),
        "location": job.location or "",
        "job_type": job.job_type or "",
    } for score, job in considered_jobs]

    if job_id:
        job = Job.query.get(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        job_skills = {s.skill_name for s in job.skills}
        job_title = job.title
        job_company = job.recruiter.company or job.recruiter.name or ""
        job_detail = {
            "title": job.title,
            "company": job_company,
            "location": job.location or "",
            "job_type": job.job_type or "",
            "experience_level": job.experience_level or "",
            "salary_min": float(job.salary_min) if job.salary_min else None,
            "salary_max": float(job.salary_max) if job.salary_max else None,
        }
    else:
        job_skills = set()
        for _, job in considered_jobs:
            job_skills.update(s.skill_name for s in job.skills)
        job_title = "All Matched Jobs"
        job_company = ""
        job_detail = None

    matched = list(resume_skills & job_skills)
    missing = sorted(job_skills - resume_skills)
    # Skills the applicant has marked as "learned" close their gap, so count
    # them as effectively matched — keeps the readiness ring consistent with
    # the gap-closure progress tracker.
    learned_count = sum(1 for s in missing if progress_map.get(s) == "learned")
    total = len(job_skills)
    readiness = round((len(matched) + learned_count) / total * 100, 1) if total > 0 else 0.0

    # How many considered roles require a given skill (aggregate view only).
    job_skill_sets = [{s.skill_name for s in j.skills} for _, j in considered_jobs]

    def frequency(skill):
        return sum(1 for js in job_skill_sets if skill in js)

    def priority_for(freq):
        if job_id:
            # Single job: the fewer remaining gaps, the more urgent each one is.
            if len(missing) <= 2:
                return "High"
            if len(missing) <= 5:
                return "Medium"
            return "Low"
        # Aggregate: skills required by most of your target roles are most valuable.
        n = len(considered_jobs) or 1
        ratio = (freq or 0) / n
        if ratio >= 0.6:
            return "High"
        if ratio >= 0.3:
            return "Medium"
        return "Low"

    missing_with_priority = []
    for s in missing:
        freq = frequency(s) if not job_id else None
        missing_with_priority.append({
            "skill": s,
            "priority": priority_for(freq),
            "frequency": freq,
            "status": progress_map.get(s, "not_started"),
        })
    order = {"High": 0, "Medium": 1, "Low": 2}
    missing_with_priority.sort(key=lambda x: (order.get(x["priority"], 3), x["skill"]))

    return jsonify({
        "job_id": job_id, "job_title": job_title, "job_company": job_company,
        "job_detail": job_detail,
        "matched_jobs": matched_jobs,
        "considered_jobs": considered,
        "resume_skills": list(resume_skills),
        "matched_skills": matched, "missing_skills": missing_with_priority,
        "readiness_score": readiness,
    }), 200


@api.route('/applicants/<applicant_id>/skill-progress', methods=['PUT'])
@_ownership_required
def update_skill_progress(applicant_id):
    """Track an applicant's progress toward closing a skill gap.

    Body: {"skill": "python", "status": "learning" | "learned" | "not_started"}.
    "learning" / "learned" upsert a row; "not_started" clears any saved
    progress for that skill (back to an untracked gap).
    """
    applicant = Applicant.query.get(applicant_id)
    if not applicant:
        return jsonify({"error": "Applicant not found"}), 404

    data = request.get_json(silent=True) or {}
    skill = (data.get('skill') or '').strip().lower()
    status = (data.get('status') or '').strip().lower()

    if not skill:
        return jsonify({"error": "skill is required"}), 400
    if status not in ('learning', 'learned', 'not_started'):
        return jsonify({"error": "status must be 'learning', 'learned', or 'not_started'"}), 400

    progress = SkillProgress.query.filter_by(
        applicant_id=applicant_id, skill_name=skill
    ).first()

    if status == 'not_started':
        if progress:
            db.session.delete(progress)
            db.session.commit()
        return jsonify({"skill": skill, "status": "not_started"}), 200

    if not progress:
        progress = SkillProgress(applicant_id=applicant_id, skill_name=skill, status=status)
        db.session.add(progress)
    else:
        progress.status = status
    db.session.commit()

    return jsonify({"skill": skill, "status": status}), 200


# ============ RECRUITER CANDIDATE ROUTES ============


@api.route('/jobs/<job_id>/candidates', methods=['GET'])
@require_auth
def get_job_candidates(job_id):
    """Get all candidates for a specific job, ranked by match score."""
    job = Job.query.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    if str(job.recruiter_id) != g.current_user_id:
        return jsonify({"error": "You can only view candidates for your own jobs"}), 403

    min_score = request.args.get('min_score', 0, type=float)

    # Ordering — ?sort= matching_score|-matching_score (default desc).
    sort = (request.args.get('sort') or '-matching_score').strip().lower()
    if sort not in ('matching_score', '-matching_score'):
        sort = '-matching_score'
    descending = sort.startswith('-')

    query = Ranking.query.join(Resume).join(
        JobApplication,
        (JobApplication.applicant_id == Resume.applicant_id)
        & (JobApplication.job_id == Ranking.job_id),
    ).filter(
        Ranking.job_id == job_id,
        Ranking.matching_score >= min_score,
    ).order_by(
        Ranking.matching_score.desc() if descending else Ranking.matching_score.asc(),
        Ranking.ranking_id.desc() if descending else Ranking.ranking_id.asc(),
    )

    def _candidate_payload(r):
        return {
            "ranking_id": str(r.ranking_id),
            "applicant_id": str(r.resume.applicant_id),
            "applicant_name": r.resume.applicant.name or r.resume.applicant.email,
            "applicant_email": r.resume.applicant.email,
            "applicant_location": r.resume.applicant.location or "",
            "matching_score": r.matching_score,
            "candidate_rank": r.candidate_rank,
            "resume_skills": [s.skill_name for s in r.resume.skills],
        }

    def _dedupe(rows):
        seen: set[str] = set()
        result = []
        for r in rows:
            if str(r.ranking_id) in seen:
                continue
            seen.add(str(r.ranking_id))
            result.append(r)
        return result

    if is_v1_request():
        limit = parse_limit(10)
        cursor_values = decode_cursor(request.args.get('cursor'))
        if cursor_values:
            query = keyset_filter(
                query,
                [Ranking.matching_score, Ranking.ranking_id],
                cursor_values,
                descending=descending,
            )
        rows = _dedupe(query.limit(limit + 1).all())
        has_more = len(rows) > limit
        page_items = rows[:limit]
        next_cursor = None
        if has_more and page_items:
            last = page_items[-1]
            next_cursor = encode_cursor(last.matching_score, last.ranking_id)
        return jsonify(build_envelope(
            [_candidate_payload(r) for r in page_items],
            total=query.count(), limit=limit,
            next_cursor=next_cursor, has_more=has_more,
            job_id=str(job_id), job_title=job.title,
        )), 200

    # Legacy /api — offset pagination with the historical response shape.
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    rankings = _dedupe(pagination.items)

    return jsonify({
        "total": pagination.total, "page": page, "per_page": per_page, "pages": pagination.pages,
        "job_id": str(job_id), "job_title": job.title,
        "candidates": [_candidate_payload(r) for r in rankings],
    }), 200


@api.route('/recruiters/<recruiter_id>/candidates', methods=['GET'])
@_ownership_required
def get_recruiter_candidates(recruiter_id):
    """Get all candidates for all jobs posted by a recruiter."""
    recruiter = Recruiter.query.get(recruiter_id)
    if not recruiter:
        return jsonify({"error": "Recruiter not found"}), 404

    jobs_list = Job.query.filter_by(recruiter_id=recruiter_id).all()
    job_ids = [j.job_id for j in jobs_list]
    if not job_ids:
        if is_v1_request():
            return jsonify(build_envelope(
                [], total=0, limit=parse_limit(20),
                recruiter_id=str(recruiter_id), jobs=[],
            )), 200
        return jsonify({
            "total": 0, "recruiter_id": str(recruiter_id),
            "candidates": [], "jobs": [],
        }), 200

    min_score = request.args.get('min_score', 0, type=float)
    job_filter = request.args.get('job_id')

    # Ordering — ?sort= matching_score|-matching_score (default desc).
    sort = (request.args.get('sort') or '-matching_score').strip().lower()
    if sort not in ('matching_score', '-matching_score'):
        sort = '-matching_score'
    descending = sort.startswith('-')

    query = Ranking.query.join(Resume).join(
        JobApplication,
        (JobApplication.applicant_id == Resume.applicant_id)
        & (JobApplication.job_id == Ranking.job_id),
    ).filter(
        Ranking.job_id.in_(job_ids),
        Ranking.matching_score >= min_score,
    )

    if job_filter and job_filter in [str(j) for j in job_ids]:
        query = query.filter(Ranking.job_id == job_filter)

    query = query.order_by(
        Ranking.matching_score.desc() if descending else Ranking.matching_score.asc(),
        Ranking.ranking_id.desc() if descending else Ranking.ranking_id.asc(),
    )

    def _dedupe(rows):
        seen: set[str] = set()
        result = []
        for r in rows:
            if str(r.ranking_id) in seen:
                continue
            seen.add(str(r.ranking_id))
            result.append(r)
        return result

    def _recruiter_candidate_payload(r):
        app = JobApplication.query.filter_by(
            job_id=r.job.job_id, applicant_id=r.resume.applicant_id
        ).first()
        iv = Interview.query.filter_by(
            job_id=r.job.job_id, applicant_id=r.resume.applicant_id
        ).filter(Interview.status.in_(['pending', 'confirmed'])).first()
        return {
            "ranking_id": str(r.ranking_id),
            "job_id": str(r.job.job_id),
            "job_title": r.job.title,
            "applicant_id": str(r.resume.applicant_id),
            "applicant_name": r.resume.applicant.name or r.resume.applicant.email,
            "applicant_email": r.resume.applicant.email,
            "applicant_location": r.resume.applicant.location or "",
            "applicant_profile_image": r.resume.applicant.profile_image,
            "matching_score": r.matching_score,
            "candidate_rank": r.candidate_rank,
            "resume_skills": [s.skill_name for s in r.resume.skills],
            "application_id": str(app.application_id) if app else None,
            "application_status": app.status if app else "pending",
            "interview": ({
                "interview_id": str(iv.interview_id),
                "scheduled_at": iv.scheduled_at.isoformat(),
                "status": iv.status,
                "meeting_link": iv.meeting_link or "",
            } if iv else None),
        }

    jobs_meta = [{"job_id": str(j.job_id), "title": j.title} for j in jobs_list]

    if is_v1_request():
        limit = parse_limit(20)
        cursor_values = decode_cursor(request.args.get('cursor'))
        if cursor_values:
            query = keyset_filter(
                query,
                [Ranking.matching_score, Ranking.ranking_id],
                cursor_values,
                descending=descending,
            )
        rows = _dedupe(query.limit(limit + 1).all())
        has_more = len(rows) > limit
        page_items = rows[:limit]
        next_cursor = None
        if has_more and page_items:
            last = page_items[-1]
            next_cursor = encode_cursor(last.matching_score, last.ranking_id)
        return jsonify(build_envelope(
            [_recruiter_candidate_payload(r) for r in page_items],
            total=query.count(), limit=limit,
            next_cursor=next_cursor, has_more=has_more,
            recruiter_id=str(recruiter_id), jobs=jobs_meta,
        )), 200

    # Legacy /api — offset pagination with the historical response shape.
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    rankings = _dedupe(pagination.items)

    return jsonify({
        "total": pagination.total, "page": page, "per_page": per_page, "pages": pagination.pages,
        "recruiter_id": str(recruiter_id),
        "jobs": jobs_meta,
        "candidates": [_recruiter_candidate_payload(r) for r in rankings],
    }), 200


@api.route('/recruiters/<recruiter_id>/dashboard', methods=['GET'])
@_ownership_required
def recruiter_dashboard(recruiter_id):
    """Get dashboard stats for a recruiter."""
    recruiter = Recruiter.query.get(recruiter_id)
    if not recruiter:
        return jsonify({"error": "Recruiter not found"}), 404

    jobs = Job.query.filter_by(recruiter_id=recruiter_id).order_by(Job.created_at.desc()).all()
    job_ids = [j.job_id for j in jobs]
    total_candidates = 0
    top_candidates = []

    if job_ids:
        total_candidates = db.session.query(func.count(func.distinct(Ranking.resume_id)))\
            .join(Resume, Resume.resume_id == Ranking.resume_id)\
            .join(JobApplication,
                  (JobApplication.applicant_id == Resume.applicant_id)
                  & (JobApplication.job_id == Ranking.job_id))\
            .filter(Ranking.job_id.in_(job_ids)).scalar() or 0

        top_query = Ranking.query.join(Resume).join(
            JobApplication,
            (JobApplication.applicant_id == Resume.applicant_id)
            & (JobApplication.job_id == Ranking.job_id),
        ).filter(
            Ranking.job_id.in_(job_ids),
            Ranking.matching_score > 0,
        ).order_by(Ranking.matching_score.desc())

        seen: set[str] = set()
        for r in top_query.all():
            if str(r.ranking_id) in seen:
                continue
            seen.add(str(r.ranking_id))
            top_candidates.append({
                "applicant_id": str(r.resume.applicant_id),
                "applicant_name": r.resume.applicant.name or r.resume.applicant.email,
                "applicant_email": r.resume.applicant.email,
                "applicant_location": r.resume.applicant.location or "",
                "job_title": r.job.title,
                "matching_score": r.matching_score,
                "resume_skills": [s.skill_name for s in r.resume.skills],
            })
            if len(top_candidates) >= 3:
                break

    upcoming_interviews = Interview.query.filter_by(recruiter_id=recruiter_id)\
        .filter(Interview.status.in_(['pending', 'confirmed']))\
        .order_by(Interview.scheduled_at.asc()).limit(5).all()

    return jsonify({
        "name": recruiter.name or recruiter.email,
        "email": recruiter.email,
        "company": recruiter.company or "",
        "active_postings": len(jobs),
        "total_candidates": total_candidates,
        "top_match_score": top_candidates[0]["matching_score"] if top_candidates else 0,
        "jobs": [format_job(j) for j in jobs[:5]],
        "top_candidates": top_candidates,
        "upcoming_interviews": [{
            "interview_id": str(iv.interview_id),
            "job_title": iv.job.title if iv.job else "",
            "applicant_name": iv.applicant.name or iv.applicant.email,
            "scheduled_at": iv.scheduled_at.isoformat(),
            "duration_minutes": iv.duration_minutes,
            "status": iv.status,
            "meeting_link": iv.meeting_link or "",
        } for iv in upcoming_interviews],
    }), 200


@api.route('/recruiters/bulk-screen', methods=['POST'])
@require_role('recruiter')
def bulk_screen():
    """Upload bulk resumes in PDF (max 50) and score/rank them against a job description."""
    uploaded_files = request.files.getlist('files')
    if not uploaded_files or len(uploaded_files) == 0 or (len(uploaded_files) == 1 and uploaded_files[0].filename == ''):
        return jsonify({"error": "No files uploaded"}), 400
    if len(uploaded_files) > 50:
        return jsonify({"error": "You can upload a maximum of 50 resumes"}), 400

    job_id = request.form.get('job_id')
    custom_title = request.form.get('custom_title', 'Custom Position')
    custom_skills_raw = request.form.get('custom_skills', '')
    custom_description = request.form.get('custom_description', '')

    job_skills_list = []
    job_title = custom_title
    job_desc = custom_description
    target_experience_years = None
    selected_job = None

    if job_id:
        selected_job = Job.query.get(job_id)
        if not selected_job:
            return jsonify({"error": "Selected job posting not found"}), 404
        job_skills_list = [s.skill_name.lower() for s in selected_job.skills]
        job_title = selected_job.title
        job_desc = f"{selected_job.title} " + " ".join(job_skills_list)
        target_experience_years = experience_level_to_years(selected_job.experience_level)
    else:
        if custom_skills_raw:
            job_skills_list = [s.strip().lower() for s in custom_skills_raw.split(',') if s.strip()]
        if not job_skills_list and custom_description:
            job_skills_list = extract_skills_from_text(custom_description)
        if not job_desc:
            job_desc = f"{custom_title} " + " ".join(job_skills_list)
        target_experience_years = extract_experience_years(custom_description)

    if not job_skills_list and not job_desc:
        return jsonify({"error": "Please select a job or provide a job description/skills"}), 400

    # Persist the job + uploaded PDFs, then queue the Celery worker task so
    # large batches don't block the request thread (Phase 4.3).
    screening_job = BulkScreenJob(
        # Convert to a real uuid so the FK bind works on both Postgres and
        # the sqlite test database (JWT subjects are stored as strings).
        recruiter_id=uuid.UUID(str(g.current_user_id)),
        status="queued",
        total_files=len(uploaded_files),
        job_title=job_title,
        job_skills=json.dumps(job_skills_list),
        job_desc=job_desc,
        target_experience_years=target_experience_years,
        job_experience_level=selected_job.experience_level if selected_job else None,
    )
    db.session.add(screening_job)
    db.session.flush()

    job_dir = bulk_screen_job_dir(screening_job.job_id)
    os.makedirs(job_dir, exist_ok=True)
    saved_files = []
    for index, file in enumerate(uploaded_files):
        safe_name = f"{index}_{os.path.basename(file.filename or f'resume_{index}.pdf')}"
        path = os.path.join(job_dir, safe_name)
        file.save(path)
        saved_files.append({"filename": file.filename, "path": path})
    screening_job.file_paths = json.dumps(saved_files)
    db.session.commit()

    # Enqueue the Celery task; if no broker is available (or the enqueue
    # fails), process inline so the endpoint keeps working without Redis.
    from tasks.bulk_screen_tasks import process_bulk_screen_job, run_bulk_screen_job

    if settings.CELERY_BROKER_URL or settings.REDIS_URL:
        try:
            process_bulk_screen_job.delay(str(screening_job.job_id))
            return jsonify({
                "job_id": str(screening_job.job_id),
                "status": "queued",
                "total_files": len(uploaded_files),
                "job_title": job_title,
                "job_skills": job_skills_list,
            }), 202
        except Exception as exc:
            current_app.logger.warning(
                f"Celery enqueue failed ({exc}); processing bulk screen synchronously"
            )

    try:
        run_bulk_screen_job(str(screening_job.job_id))
    except Exception as exc:
        try:
            from tasks.bulk_screen_tasks import mark_bulk_screen_failed
            mark_bulk_screen_failed(str(screening_job.job_id), exc)
        except Exception:
            pass
        return jsonify({"error": f"Bulk screening failed: {exc!s}"}), 500

    return jsonify(_bulk_screen_job_payload(screening_job)), 200


def _bulk_screen_job_payload(job):
    """Serialize a BulkScreenJob for the status/results endpoints."""
    try:
        results = json.loads(job.results) if job.results else None
    except (ValueError, TypeError):
        results = None
    try:
        job_skills = json.loads(job.job_skills or "[]")
    except (ValueError, TypeError):
        job_skills = []
    progress = round((job.processed_files / job.total_files) * 100) if job.total_files else 0
    return {
        "job_id": str(job.job_id),
        "status": job.status,
        "total_files": job.total_files,
        "processed_files": job.processed_files,
        "progress": progress,
        "job_title": job.job_title or "",
        "job_skills": job_skills,
        "results": results,
        "error": job.error,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
    }


@api.route('/recruiters/bulk-screen/<job_id>', methods=['GET'])
@require_auth
def bulk_screen_status(job_id):
    """Poll the status of a bulk screening job (recruiter who started it only)."""
    try:
        uuid.UUID(str(job_id))
    except (ValueError, AttributeError, TypeError):
        return jsonify({"error": "Bulk screen job not found"}), 404

    job = BulkScreenJob.query.get(uuid.UUID(str(job_id)))
    if not job:
        return jsonify({"error": "Bulk screen job not found"}), 404
    if str(job.recruiter_id) != g.current_user_id:
        return jsonify({"error": "You can only view your own bulk screen jobs"}), 403
    return jsonify(_bulk_screen_job_payload(job)), 200


@api.route('/rankings/<ranking_id>/explain', methods=['GET'])
@require_auth
def explain_ranking(ranking_id):
    """Return per-feature attribution for a candidate's match score.

    The caller must be either the recruiter who owns the job or the
    applicant who owns the resume behind the ranking.
    """
    ranking = Ranking.query.get(ranking_id)
    if not ranking:
        return jsonify({"error": "Ranking not found"}), 404

    resume = Resume.query.get(ranking.resume_id)
    job = Job.query.get(ranking.job_id)
    if not resume or not job:
        return jsonify({"error": "Resume or job missing for this ranking"}), 404

    is_recruiter_owner = str(job.recruiter_id) == g.current_user_id
    is_applicant_owner = str(resume.applicant_id) == g.current_user_id
    if not (is_recruiter_owner or is_applicant_owner):
        return jsonify({"error": "You can only view explanations for your own data"}), 403

    explanation = explain_ranking_score(resume, job)
    explanation["ranking_id"] = str(ranking_id)
    explanation["applicant_id"] = str(resume.applicant_id)
    explanation["job_id"] = str(job.job_id)
    return jsonify(explanation), 200


@api.route('/rankings/<ranking_id>', methods=['PUT'])
@require_role('recruiter')
def update_ranking(ranking_id):
    """Update candidate ranking/status (recruiter who owns the job only)."""
    ranking = Ranking.query.get(ranking_id)
    if not ranking:
        return jsonify({"error": "Ranking not found"}), 404

    job = Job.query.get(ranking.job_id)
    if not job or str(job.recruiter_id) != g.current_user_id:
        return jsonify({"error": "You can only update rankings for your own jobs"}), 403

    data = request.get_json()
    if 'candidate_rank' in data:
        ranking.candidate_rank = data.get('candidate_rank')
    db.session.commit()
    return jsonify({
        "message": "Ranking updated successfully",
        "ranking_id": str(ranking.ranking_id),
        "candidate_rank": ranking.candidate_rank,
    }), 200


# ============ NOTIFICATION ROUTES ============

@api.route('/notifications/<user_id>', methods=['GET'])
@_ownership_required
def get_notifications(user_id):
    """Get notifications for a user."""
    query = Notification.query.filter_by(user_id=user_id)\
        .order_by(Notification.created_at.desc())

    def _payload(n):
        return {
            "notification_id": str(n.notification_id),
            "title": n.title, "message": n.message, "type": n.type,
            "is_read": n.is_read,
            "related_job_id": str(n.related_job_id) if n.related_job_id else None,
            "related_job_title": n.related_job.title if n.related_job else None,
            "created_at": n.created_at.isoformat(),
        }

    if is_v1_request():
        limit = parse_limit(50)
        rows = query.limit(limit).all()
        return jsonify(build_envelope(
            [_payload(n) for n in rows],
            total=query.count(), limit=limit,
        )), 200
    return jsonify([_payload(n) for n in query.limit(50).all()]), 200


@api.route('/notifications/<notification_id>/read', methods=['PATCH'])
@require_auth
def mark_notification_read(notification_id):
    """Mark a notification as read."""
    n = Notification.query.get(notification_id)
    if not n:
        return jsonify({"error": "Not found"}), 404
    if str(n.user_id) != g.current_user_id:
        return jsonify({"error": "You can only mark your own notifications"}), 403
    n.is_read = True
    db.session.commit()
    return jsonify({"success": True}), 200


@api.route('/notifications/read-all/<user_id>', methods=['PATCH'])
@_ownership_required
def mark_all_notifications_read(user_id):
    """Mark all notifications as read for a user."""
    Notification.query.filter_by(user_id=user_id, is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"success": True}), 200


# ============ SAVED JOBS ROUTES ============

@api.route('/jobs/<job_id>/save', methods=['POST', 'DELETE'])
@require_role('applicant')
def toggle_saved_job(job_id):
    """Save or unsave a job for the authenticated applicant."""
    job = Job.query.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    existing = SavedJob.query.filter_by(
        applicant_id=g.current_user_id, job_id=job_id
    ).first()

    if request.method == 'POST':
        if existing:
            return jsonify({"message": "Job already saved", "saved": True}), 200
        saved = SavedJob(applicant_id=g.current_user_id, job_id=job_id)
        db.session.add(saved)
        db.session.commit()
        return jsonify({"message": "Job saved successfully", "saved": True}), 201
    else:
        if not existing:
            return jsonify({"message": "Job not saved", "saved": False}), 200
        db.session.delete(existing)
        db.session.commit()
        return jsonify({"message": "Job unsaved successfully", "saved": False}), 200


@api.route('/applicants/<applicant_id>/saved-jobs', methods=['GET'])
@_ownership_required
def get_saved_jobs(applicant_id):
    """Get all saved jobs for the applicant."""
    applicant = Applicant.query.get(applicant_id)
    if not applicant:
        return jsonify({"error": "Applicant not found"}), 404

    saved_jobs = SavedJob.query.filter_by(applicant_id=applicant_id)\
        .order_by(SavedJob.created_at.desc()).all()

    latest_resume = Resume.query.filter_by(applicant_id=applicant_id)\
        .order_by(Resume.uploaded_at.desc()).first()

    applied_map = {
        str(a.job_id): str(a.application_id)
        for a in JobApplication.query.filter_by(applicant_id=applicant_id).all()
    }

    from routes_common import format_job

    jobs = []
    for sj in saved_jobs:
        job = sj.job
        if not job:
            continue
        job_data = format_job(job)
        score = 0.0
        if latest_resume:
            try:
                score = float(_compute_job_match_score(latest_resume, job) or 0.0)
            except Exception:
                pass
        job_data["matching_score"] = round(score, 2)
        job_data["applied"] = str(job.job_id) in applied_map
        job_data["application_id"] = applied_map.get(str(job.job_id))
        job_data["saved_at"] = sj.created_at.isoformat()
        jobs.append(job_data)

    if is_v1_request():
        return jsonify(build_envelope(
            jobs, total=len(jobs), limit=len(jobs),
        )), 200
    return jsonify({
        "total": len(jobs),
        "saved_jobs": jobs,
    }), 200


@api.route('/applicants/<applicant_id>/saved-job-ids', methods=['GET'])
@_ownership_required
def get_saved_job_ids(applicant_id):
    """Get just the IDs of saved jobs (for bookmark state on job cards)."""
    applicant = Applicant.query.get(applicant_id)
    if not applicant:
        return jsonify({"error": "Applicant not found"}), 404

    saved_ids = [
        str(sj.job_id)
        for sj in SavedJob.query.filter_by(applicant_id=applicant_id).all()
    ]
    if is_v1_request():
        return jsonify(build_envelope(
            saved_ids, total=len(saved_ids), limit=len(saved_ids),
        )), 200
    return jsonify({"saved_job_ids": saved_ids}), 200


# ============ APPLICATION STATUS / SHORTLIST ROUTES ============

@api.route('/applications/<application_id>/status', methods=['PATCH'])
@require_auth
def update_application_status(application_id):
    """Update status of a job application (shortlist / reject / pending)."""
    application = JobApplication.query.get(application_id)
    if not application:
        return jsonify({"error": "Application not found"}), 404

    job = Job.query.get(application.job_id)
    if not job or str(job.recruiter_id) != g.current_user_id:
        return jsonify({"error": "Only the job's recruiter can update application status"}), 403

    data = request.get_json()
    new_status = data.get('status')
    if new_status not in ('pending', 'shortlisted', 'rejected'):
        return jsonify({"error": "Invalid status. Must be pending, shortlisted, or rejected."}), 400

    old_status = application.status
    application.status = new_status

    if new_status != old_status:
        job_title = job.title or "a position"
        company = getattr(job.recruiter, 'company', None) or job.recruiter.name or "the recruiter"

        if new_status == 'shortlisted':
            msg = f"Congratulations! You have been shortlisted for {job_title} by {company}."
            notif_type = 'shortlisted'
        elif new_status == 'rejected':
            msg = f"Your application for {job_title} was not selected at this time. Keep applying!"
            notif_type = 'rejected'
        else:
            msg = f"Your application for {job_title} status changed to: {new_status}."
            notif_type = 'info'

        db.session.add(Notification(
            user_id=application.applicant_id,
            title="🎉 You've been shortlisted!" if new_status == 'shortlisted' else "Application Update",
            message=msg, type=notif_type, related_job_id=application.job_id,
        ))
        _emit_ws(str(application.applicant_id),
                 "🎉 You've been shortlisted!" if new_status == 'shortlisted' else "Application Update",
                 msg, notif_type, str(application.job_id))

    db.session.commit()
    return jsonify({
        "success": True,
        "application_id": str(application.application_id),
        "status": application.status,
    }), 200


@api.route('/applications/<application_id>', methods=['DELETE'])
@require_auth
def cancel_application(application_id):
    """Allow an applicant to withdraw/cancel their own job application."""
    application = JobApplication.query.get(application_id)
    if not application:
        return jsonify({"error": "Application not found"}), 404

    if str(application.applicant_id) != g.current_user_id:
        return jsonify({"error": "You can only cancel your own applications"}), 403

    job = Job.query.get(application.job_id)
    applicant = Applicant.query.get(application.applicant_id)

    # Cancel any pending/confirmed interviews tied to this application
    interviews = Interview.query.filter_by(
        job_id=application.job_id, applicant_id=application.applicant_id
    ).filter(Interview.status.in_(['pending', 'confirmed'])).all()
    for iv in interviews:
        iv.status = 'cancelled'

    # Let the recruiter know the applicant withdrew
    if job:
        db.session.add(Notification(
            user_id=job.recruiter_id,
            title="Application Withdrawn",
            message=f"{applicant.name or applicant.email} withdrew their application for '{job.title}'.",
            type="info",
            related_job_id=application.job_id,
        ))

    application_id_str = str(application.application_id)
    job_id_str = str(application.job_id)

    db.session.delete(application)
    db.session.commit()

    return jsonify({
        "message": "Application cancelled successfully",
        "application_id": application_id_str,
        "job_id": job_id_str,
    }), 200


# ============ INTERVIEW ROUTES ============

@api.route('/interviews', methods=['POST'])
@require_role('recruiter')
def propose_interview():
    """Recruiter proposes an interview for an applicant."""
    data = request.get_json()
    job_id = data.get('job_id')
    applicant_id = data.get('applicant_id')
    scheduled_at_str = data.get('scheduled_at')
    duration = data.get('duration_minutes', 60)
    notes = data.get('notes', '')
    meeting_link = data.get('meeting_link', '')

    if not all([job_id, applicant_id, scheduled_at_str]):
        return jsonify({"error": "job_id, applicant_id, and scheduled_at are required"}), 400

    job = Job.query.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    if str(job.recruiter_id) != g.current_user_id:
        return jsonify({"error": "You can only schedule interviews for your own jobs"}), 403

    applicant = Applicant.query.get(applicant_id)
    if not applicant:
        return jsonify({"error": "Applicant not found"}), 404

    # Prevent scheduling a second interview for the same job + applicant
    # while one is still pending or confirmed.
    existing = Interview.query.filter_by(
        job_id=job_id, applicant_id=applicant_id
    ).filter(Interview.status.in_(['pending', 'confirmed'])).first()
    if existing:
        return jsonify({
            "error": "An interview is already scheduled for this candidate and posting.",
            "interview_id": str(existing.interview_id),
            "status": existing.status,
        }), 409

    try:
        scheduled_at = datetime.fromisoformat(scheduled_at_str)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid datetime format. Use ISO 8601."}), 400

    if scheduled_at < datetime.utcnow():
        return jsonify({"error": "Interview time must be in the future"}), 400

    interview = Interview(
        job_id=job_id,
        applicant_id=applicant_id,
        recruiter_id=g.current_user_id,
        scheduled_at=scheduled_at,
        duration_minutes=duration,
        notes=notes,
        meeting_link=meeting_link,
        status='pending',
    )
    db.session.add(interview)

    db.session.add(Notification(
        user_id=applicant_id,
        title="Interview Invitation",
        message=f"You've been invited for an interview for '{job.title}'.",
        type="info",
        related_job_id=job_id,
    ))
    db.session.commit()
    _emit_ws(applicant_id, "Interview Invitation", f"You've been invited for an interview for '{job.title}'.", "info", job_id)

    return jsonify({
        "message": "Interview proposed successfully",
        "interview_id": str(interview.interview_id),
        "scheduled_at": interview.scheduled_at.isoformat(),
        "status": interview.status,
    }), 201


@api.route('/interviews/<interview_id>/respond', methods=['PATCH'])
@require_role('applicant')
def respond_interview(interview_id):
    """Applicant confirms or declines an interview."""
    interview = Interview.query.get(interview_id)
    if not interview:
        return jsonify({"error": "Interview not found"}), 404

    if str(interview.applicant_id) != g.current_user_id:
        return jsonify({"error": "You can only respond to your own interviews"}), 403

    if interview.status != 'pending':
        return jsonify({"error": f"Interview already {interview.status}"}), 400

    data = request.get_json()
    action = data.get('action')
    if action not in ('confirm', 'decline'):
        return jsonify({"error": "Action must be 'confirm' or 'decline'"}), 400

    interview.status = 'confirmed' if action == 'confirm' else 'declined'

    job = Job.query.get(interview.job_id)
    job_title = job.title if job else "a position"

    if action == 'confirm':
        msg = f"{interview.applicant.name or 'The applicant'} has confirmed the interview for '{job_title}'."
        notif_title = "Interview Confirmed"
    else:
        msg = f"{interview.applicant.name or 'The applicant'} has declined the interview for '{job_title}'."
        notif_title = "Interview Declined"

    db.session.add(Notification(
        user_id=interview.recruiter_id,
        title=notif_title,
        message=msg,
        type="info",
        related_job_id=interview.job_id,
    ))
    db.session.commit()

    return jsonify({
        "message": f"Interview {action}ed successfully",
        "interview_id": str(interview.interview_id),
        "status": interview.status,
    }), 200


@api.route('/interviews/<interview_id>/cancel', methods=['PATCH'])
@require_role('recruiter')
def cancel_interview(interview_id):
    """Recruiter cancels an interview."""
    interview = Interview.query.get(interview_id)
    if not interview:
        return jsonify({"error": "Interview not found"}), 404

    if str(interview.recruiter_id) != g.current_user_id:
        return jsonify({"error": "You can only cancel your own interviews"}), 403

    if interview.status not in ('pending', 'confirmed'):
        return jsonify({"error": f"Cannot cancel an interview that is {interview.status}"}), 400

    interview.status = 'cancelled'

    job = Job.query.get(interview.job_id)
    job_title = job.title if job else "a position"

    db.session.add(Notification(
        user_id=interview.applicant_id,
        title="Interview Cancelled",
        message=f"The interview for '{job_title}' has been cancelled.",
        type="warning",
        related_job_id=interview.job_id,
    ))
    db.session.commit()

    return jsonify({
        "message": "Interview cancelled successfully",
        "interview_id": str(interview.interview_id),
        "status": interview.status,
    }), 200


@api.route('/interviews/<user_id>', methods=['GET'])
@_ownership_required
def list_interviews(user_id):
    """Get all interviews for a user (works for both applicant and recruiter)."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.role == 'recruiter':
        interviews = Interview.query.filter_by(recruiter_id=user_id)\
            .order_by(Interview.scheduled_at.desc()).all()
    else:
        interviews = Interview.query.filter_by(applicant_id=user_id)\
            .order_by(Interview.scheduled_at.desc()).all()

    def _payload(iv):
        return {
            "interview_id": str(iv.interview_id),
            "job_id": str(iv.job_id),
            "job_title": iv.job.title if iv.job else "",
            "applicant_id": str(iv.applicant_id),
            "applicant_name": iv.applicant.name or iv.applicant.email,
            "recruiter_id": str(iv.recruiter_id),
            "recruiter_name": iv.recruiter.name or iv.recruiter.email,
            "recruiter_company": iv.recruiter.company or "",
            "scheduled_at": iv.scheduled_at.isoformat(),
            "duration_minutes": iv.duration_minutes,
            "status": iv.status,
            "notes": iv.notes or "",
            "meeting_link": iv.meeting_link or "",
            "created_at": iv.created_at.isoformat(),
        }

    if is_v1_request():
        return jsonify(build_envelope(
            [_payload(iv) for iv in interviews],
            total=len(interviews), limit=len(interviews),
        )), 200
    return jsonify([_payload(iv) for iv in interviews]), 200


@api.route('/jobs/<job_id>/application-status/<applicant_id>', methods=['GET'])
@require_auth
def get_application_status(job_id, applicant_id):
    """Get the status and application_id for a specific application."""
    if g.current_user_id != applicant_id:
        job = Job.query.get(job_id)
        if not job or str(job.recruiter_id) != g.current_user_id:
            return jsonify({"error": "Access denied"}), 403

    application = JobApplication.query.filter_by(
        job_id=job_id, applicant_id=applicant_id
    ).first()
    if not application:
        return jsonify({"error": "Application not found"}), 404
    return jsonify({
        "application_id": str(application.application_id),
        "status": application.status,
    }), 200


# ============ DEV ROUTES (disabled in production) ============


@api.route('/dev/email-preview', methods=['GET'])
def dev_email_preview():
    """Render an email template in the browser for visual review (dev only).

    Query param ``template`` selects which template to preview:
    ``verification`` (default), ``password_reset``, or ``interview_reminder``.
    Returns the rendered HTML email wrapped in a small preview frame plus
    the plain-text fallback body.
    """
    if settings.ENVIRONMENT == 'production':
        return jsonify({"error": "Not available in production"}), 404

    template = request.args.get('template', 'verification')
    contexts = {
        'verification': {'otp': '482931', 'name': 'Jane Doe'},
        'password_reset': {'otp': '729104', 'name': 'Jane Doe'},
        'interview_reminder': {
            'greeting': (
                'Hi Jane, this is a friendly reminder about your upcoming interview for '
                '<strong>Senior Frontend Developer</strong> at <strong>Acme Corp</strong>.'
            ),
            'schedule_line': (
                'The interview is scheduled for <strong>Monday, August 17 at 10:00 AM</strong> '
                'and should last about 60 minutes. Your interviewer is Alex Smith.'
            ),
            'cta': 'Prepare your questions and make sure you can join from a quiet, well-lit space.',
            'meeting_link': 'https://meet.example.com/sipsetu-demo',
            'time_label': 'tomorrow',
            'job_title': 'Senior Frontend Developer',
            'when': 'Monday, August 17 at 10:00 AM',
            'duration_minutes': 60,
        },
    }
    if template not in contexts:
        return jsonify({
            "error": f"Unknown template '{template}'. Choose from: {', '.join(sorted(contexts))}"
        }), 400

    html, text = render_email(template, **contexts[template])
    preview = (
        '<h2 style="font-family: sans-serif">'
        f'SipSetu email preview — <code>{template}.html.j2</code></h2>'
        '<h3 style="font-family: sans-serif; color: #64748b">Plain-text fallback</h3>'
        '<pre style="font-family: monospace; background: #f1f5f9; padding: 12px; '
        'border-radius: 8px; max-width: 560px; white-space: pre-wrap">'
        f'{text}</pre>'
        '<hr style="max-width: 560px">'
        f'{html}'
    )
    return preview, 200, {'Content-Type': 'text/html'}
