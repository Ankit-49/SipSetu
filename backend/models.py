import uuid
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.dialects.postgresql import UUID as _PgUUID

db = SQLAlchemy()


class UUID(_PgUUID):
    """PostgreSQL UUID column that also accepts string UUIDs on bind.

    Postgres casts string UUIDs natively, but character-based dialects
    (SQLite - used by the tests and the Docker smoke test) require real
    ``uuid.UUID`` objects and raise on strings. JWT claims and URL path
    params arrive as strings, so accepting both keeps every route working
    on every dialect.
    """

    def bind_processor(self, dialect):
        processor = super().bind_processor(dialect)
        if processor is None:
            return None

        def process(value):
            if isinstance(value, str):
                value = uuid.UUID(value)
            return processor(value)

        return process

# Junction tables
job_skills = db.Table('job_skills',
    db.Column('job_id', UUID(as_uuid=True), db.ForeignKey('jobs.job_id', ondelete='CASCADE'), primary_key=True),
    db.Column('skill_id', UUID(as_uuid=True), db.ForeignKey('skills.skill_id', ondelete='CASCADE'), primary_key=True)
)

resume_skills = db.Table('resume_skills',
    db.Column('resume_id', UUID(as_uuid=True), db.ForeignKey('resumes.resume_id', ondelete='CASCADE'), primary_key=True),
    db.Column('skill_id', UUID(as_uuid=True), db.ForeignKey('skills.skill_id', ondelete='CASCADE'), primary_key=True)
)

class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'applicant' or 'recruiter'
    phone = db.Column(db.String(20), nullable=True)
    location = db.Column(db.String(255), nullable=True)
    profile_image = db.Column(db.Text, nullable=True)
    email_verified = db.Column(db.Boolean, default=False)
    locale = db.Column(db.String(10), nullable=True)  # Phase 6.4 — i18n user preference
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __mapper_args__ = {
        'polymorphic_on': role,
        'polymorphic_identity': 'user'
    }

class Applicant(User):
    __tablename__ = 'applicants'
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True)
    resumes = db.relationship('Resume', backref='applicant', lazy=True, cascade='all, delete-orphan')

    __mapper_args__ = {
        'polymorphic_identity': 'applicant',
    }

class Recruiter(User):
    __tablename__ = 'recruiters'
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True)
    company = db.Column(db.String(255), nullable=True)
    job_title = db.Column(db.String(255), nullable=True)
    jobs = db.relationship('Job', backref='recruiter', lazy=True, cascade='all, delete-orphan')

    __mapper_args__ = {
        'polymorphic_identity': 'recruiter',
    }

class Skill(db.Model):
    __tablename__ = 'skills'
    skill_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    skill_name = db.Column(db.String(100), unique=True, nullable=False)

class Job(db.Model):
    __tablename__ = 'jobs'
    job_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recruiter_id = db.Column(UUID(as_uuid=True), db.ForeignKey('recruiters.user_id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(255), nullable=True)
    job_type = db.Column(db.String(50), nullable=True)  # full-time, part-time, contract
    experience_level = db.Column(db.String(50), nullable=True)  # fresher, 1-3, 3-5, 5+
    salary_min = db.Column(db.Float, nullable=True)
    salary_max = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Phase 6.2 — semantic embedding (JSON-encoded float list, portability across dialects)
    embedding = db.Column(db.Text, nullable=True)
    # Postgres full-text search vector (migration 005) — maintained by
    # routes_common.set_job_search_vector on Postgres writes; always NULL on
    # SQLite (dev/tests), where the search path falls back to ILIKE. The
    # with_variant keeps db.create_all() working on both dialects.
    search_vector = db.Column(
        TSVECTOR().with_variant(db.Text(), 'sqlite'),
        nullable=True,
    )

    skills = db.relationship('Skill', secondary=job_skills, backref=db.backref('jobs', lazy='dynamic'))
    rankings = db.relationship('Ranking', backref='job', lazy=True, cascade='all, delete-orphan')
    applications = db.relationship('JobApplication', backref='job', lazy=True, cascade='all, delete-orphan')

    # Phase 4.4 — hot-query composite indexes (mirrored by migration 003):
    #   - default public list + v1 keyset pagination (ORDER BY created_at DESC, job_id DESC)
    #   - recruiter's job list / dashboard (WHERE recruiter_id = ? ORDER BY created_at DESC)
    #   - job-type browsing (WHERE job_type = ? ORDER BY created_at DESC)
    #   - GET /jobs?search= leading-wildcard ILIKE -> pg_trgm GIN (migration 004;
    #     plain btree equivalents on SQLite since postgresql_using/ops are ignored)
    __table_args__ = (
        db.Index('ix_jobs_created_at_id', 'created_at', 'job_id',
                 postgresql_ops={'created_at': 'DESC', 'job_id': 'DESC'}),
        db.Index('ix_jobs_recruiter_created', 'recruiter_id', 'created_at',
                 postgresql_ops={'created_at': 'DESC'}),
        db.Index('ix_jobs_type_created', 'job_type', 'created_at',
                 postgresql_ops={'created_at': 'DESC'}),
        db.Index('ix_jobs_title_trgm', 'title',
                 postgresql_using='gin', postgresql_ops={'title': 'gin_trgm_ops'}),
        db.Index('ix_jobs_location_trgm', 'location',
                 postgresql_using='gin', postgresql_ops={'location': 'gin_trgm_ops'}),
        db.Index('ix_jobs_job_type_trgm', 'job_type',
                 postgresql_using='gin', postgresql_ops={'job_type': 'gin_trgm_ops'}),
        # Full-text search over the search_vector column (migration 005).
        db.Index('ix_jobs_search_vector', 'search_vector',
                 postgresql_using='gin'),
    )

class Resume(db.Model):
    __tablename__ = 'resumes'
    resume_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    applicant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('applicants.user_id', ondelete='CASCADE'), nullable=False)
    raw_text = db.Column(db.Text)
    file_path = db.Column(db.String(500))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Phase 6.2 — semantic embedding (JSON-encoded float list)
    embedding = db.Column(db.Text, nullable=True)
    # Phase 5.1 — LLM-parsed structured sections and confidence
    parsed_sections = db.Column(db.Text, nullable=True)  # JSON: {summary, experience, education, skills, projects}
    parse_confidence = db.Column(db.Float, nullable=True)  # 0.0-1.0 extraction confidence
    parse_method = db.Column(db.String(20), nullable=True)  # 'llm' | 'regex'

    skills = db.relationship('Skill', secondary=resume_skills, backref=db.backref('resumes', lazy='dynamic'))
    rankings = db.relationship('Ranking', backref='resume', lazy=True, cascade='all, delete-orphan')


class JobApplication(db.Model):
    __tablename__ = 'job_applications'
    application_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = db.Column(UUID(as_uuid=True), db.ForeignKey('jobs.job_id', ondelete='CASCADE'), nullable=False)
    applicant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('applicants.user_id', ondelete='CASCADE'), nullable=False)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending', nullable=False)  # 'pending', 'shortlisted', 'rejected'

    __table_args__ = (
        db.UniqueConstraint('job_id', 'applicant_id', name='uq_job_applicant_application'),
    )

    applicant = db.relationship('Applicant', backref=db.backref('job_applications', cascade='all, delete-orphan'))

class Ranking(db.Model):
    __tablename__ = 'rankings'
    ranking_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = db.Column(UUID(as_uuid=True), db.ForeignKey('jobs.job_id', ondelete='CASCADE'), nullable=False)
    resume_id = db.Column(UUID(as_uuid=True), db.ForeignKey('resumes.resume_id', ondelete='CASCADE'), nullable=False)
    matching_score = db.Column(db.Float)
    candidate_rank = db.Column(db.Integer)

    # Phase 4.4 — hot-query composite indexes (mirrored by migration 003):
    #   - candidate lists: WHERE job_id = ? AND matching_score >= ? ORDER BY
    #     matching_score DESC, ranking_id DESC (keyset cursor)
    #   - ranking regeneration after resume changes (WHERE resume_id IN (...))
    __table_args__ = (
        db.Index('ix_rankings_job_score', 'job_id', 'matching_score', 'ranking_id',
                 postgresql_ops={'matching_score': 'DESC', 'ranking_id': 'DESC'}),
        db.Index('ix_rankings_resume', 'resume_id'),
    )

class EmailVerificationToken(db.Model):
    __tablename__ = 'email_verification_tokens'
    token_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Cascade matches the DB-level ON DELETE CASCADE on user_id; without it
    # the ORM tries to NULL the FK on delete (NOT NULL violation).
    user = db.relationship('User', backref=db.backref('email_verification_tokens', cascade='all, delete-orphan'))


class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens'
    token_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('password_reset_tokens', cascade='all, delete-orphan'))


class SkillProgress(db.Model):
    __tablename__ = 'skill_progress'
    progress_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    applicant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('applicants.user_id', ondelete='CASCADE'), nullable=False)
    skill_name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='learning', nullable=False)  # 'learning', 'learned'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('applicant_id', 'skill_name', name='uq_applicant_skill_progress'),
    )

    applicant = db.relationship('Applicant', backref=db.backref('skill_progress', cascade='all, delete-orphan'))


class SavedJob(db.Model):
    __tablename__ = 'saved_jobs'
    saved_job_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    applicant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('applicants.user_id', ondelete='CASCADE'), nullable=False)
    job_id = db.Column(UUID(as_uuid=True), db.ForeignKey('jobs.job_id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('applicant_id', 'job_id', name='uq_applicant_saved_job'),
    )

    applicant = db.relationship('Applicant', backref=db.backref('saved_jobs', cascade='all, delete-orphan'))
    job = db.relationship('Job', backref=db.backref('saved_by_applicants', cascade='all, delete-orphan'))


class Interview(db.Model):
    __tablename__ = 'interviews'
    interview_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = db.Column(UUID(as_uuid=True), db.ForeignKey('jobs.job_id', ondelete='CASCADE'), nullable=False)
    applicant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('applicants.user_id', ondelete='CASCADE'), nullable=False)
    recruiter_id = db.Column(UUID(as_uuid=True), db.ForeignKey('recruiters.user_id', ondelete='CASCADE'), nullable=False)
    scheduled_at = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=60)
    status = db.Column(db.String(20), default='pending', nullable=False)  # 'pending', 'confirmed', 'completed', 'cancelled', 'declined'
    notes = db.Column(db.Text, nullable=True)
    meeting_link = db.Column(db.String(500), nullable=True)
    # Comma-separated reminder tokens already sent, e.g. "1h_applicant,24h_recruiter".
    reminders_sent = db.Column(db.String(255), default="", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    job = db.relationship('Job', backref=db.backref('interviews', cascade='all, delete-orphan'))
    applicant = db.relationship('Applicant', backref=db.backref('interviews', cascade='all, delete-orphan'), foreign_keys=[applicant_id])
    recruiter = db.relationship('Recruiter', backref=db.backref('interviews_as_recruiter', cascade='all, delete-orphan'), foreign_keys=[recruiter_id])


class RankingFeedback(db.Model):
    """Explicit recruiter feedback on a candidate ranking (Phase 5.2).

    Recruiters can indicate that a candidate should be ranked higher or
    lower, providing active-learning labels that improve the ML model
    over time.
    """
    __tablename__ = 'ranking_feedback'
    feedback_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ranking_id = db.Column(UUID(as_uuid=True), db.ForeignKey('rankings.ranking_id', ondelete='CASCADE'), nullable=False)
    recruiter_id = db.Column(UUID(as_uuid=True), db.ForeignKey('recruiters.user_id', ondelete='CASCADE'), nullable=False)
    direction = db.Column(db.String(10), nullable=False)  # 'higher', 'lower', 'correct'
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ranking = db.relationship('Ranking', backref=db.backref('feedbacks', cascade='all, delete-orphan'))
    recruiter = db.relationship('Recruiter', backref=db.backref('ranking_feedbacks', cascade='all, delete-orphan'))

    __table_args__ = (
        db.UniqueConstraint('ranking_id', 'recruiter_id', name='uq_ranking_recruiter_feedback'),
    )


class AuditLog(db.Model):
    """Immutable audit log for admin and sensitive actions (Phase 5.4)."""
    __tablename__ = 'audit_logs'
    log_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    target_type = db.Column(db.String(50), nullable=True)  # 'user', 'job', 'application', etc.
    target_id = db.Column(db.String(255), nullable=True)
    details = db.Column(db.Text, nullable=True)  # JSON
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    actor = db.relationship('User', backref=db.backref('audit_logs', cascade='all, delete-orphan'))

    __table_args__ = (
        db.Index('ix_audit_logs_actor_created', 'actor_id', 'created_at',
                 postgresql_ops={'created_at': 'DESC'}),
    )


class Organization(db.Model):
    """Multi-tenant organization that recruiters belong to (Phase 6.1).

    Organizations provide shared job pools, team dashboards, and role-based
    access control for hiring teams.
    """
    __tablename__ = 'organizations'
    org_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    logo_url = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    website = db.Column(db.String(500), nullable=True)
    industry = db.Column(db.String(100), nullable=True)
    size = db.Column(db.String(50), nullable=True)  # '1-10', '11-50', '51-200', '201-500', '500+'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    members = db.relationship('OrganizationMember', backref='organization', lazy=True, cascade='all, delete-orphan')
    jobs = db.relationship('Job', backref='organization', lazy=True)


class OrganizationMember(db.Model):
    """Membership of a user in an organization with a specific role (Phase 6.1).

    Roles: owner, admin, hiring_manager, interviewer, viewer.
    """
    __tablename__ = 'organization_members'
    membership_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = db.Column(UUID(as_uuid=True), db.ForeignKey('organizations.org_id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    role = db.Column(db.String(30), nullable=False, default='viewer')
    # owner, admin, hiring_manager, interviewer, viewer
    invited_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id], backref='organization_memberships')
    inviter = db.relationship('User', foreign_keys=[invited_by])

    __table_args__ = (
        db.UniqueConstraint('org_id', 'user_id', name='uq_org_user_membership'),
        db.Index('ix_org_members_user', 'user_id'),
    )


# Add optional org_id to Job
Job.organization_id = db.Column(UUID(as_uuid=True), db.ForeignKey('organizations.org_id', ondelete='SET NULL'), nullable=True)


class BulkScreenJob(db.Model):
    """Asynchronous bulk resume screening job (Phase 4.3).

    The POST /recruiters/bulk-screen endpoint persists the uploaded files to
    disk, records a row here, and enqueues a Celery task; the worker updates
    progress and stores the JSON results so the status endpoint can serve
    them. JSON payloads live in Text columns so the model stays portable
    across Postgres and the sqlite test database.
    """
    __tablename__ = 'bulk_screen_jobs'
    job_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recruiter_id = db.Column(UUID(as_uuid=True), db.ForeignKey('recruiters.user_id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(20), default='queued', nullable=False)  # queued, running, completed, failed
    total_files = db.Column(db.Integer, default=0, nullable=False)
    processed_files = db.Column(db.Integer, default=0, nullable=False)
    file_paths = db.Column(db.Text, nullable=True)   # JSON: [{filename, path}]
    job_title = db.Column(db.String(255), nullable=True)
    job_skills = db.Column(db.Text, nullable=True)   # JSON: [str]
    job_desc = db.Column(db.Text, nullable=True)
    target_experience_years = db.Column(db.Float, nullable=True)
    job_experience_level = db.Column(db.String(50), nullable=True)
    results = db.Column(db.Text, nullable=True)      # JSON: [per-file result]
    error = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Cascade matches the DB-level ON DELETE CASCADE on recruiter_id.
    recruiter = db.relationship(
        'Recruiter', backref=db.backref('bulk_screen_jobs', cascade='all, delete-orphan')
    )


class Notification(db.Model):
    __tablename__ = 'notifications'
    notification_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default='info')  # 'info', 'success', 'warning', 'shortlisted', 'rejected'
    is_read = db.Column(db.Boolean, default=False)
    related_job_id = db.Column(UUID(as_uuid=True), db.ForeignKey('jobs.job_id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('notifications', cascade='all, delete-orphan'))
    related_job = db.relationship('Job', foreign_keys=[related_job_id])

    # Phase 4.4 — hot-query composite index (mirrored by migration 003):
    # notification list + unread badge (WHERE user_id = ? ORDER BY created_at DESC).
    __table_args__ = (
        db.Index('ix_notifications_user_created', 'user_id', 'created_at',
                 postgresql_ops={'created_at': 'DESC'}),
    )


# ─── Phase 6.3 — Integrations ───────────────────────────────────────────────

class ATSConnection(db.Model):
    """ATS (Applicant Tracking System) connection — Greenhouse, Lever, Workday.

    Stores API credentials and sync state for each recruiter's external ATS.
    """
    __tablename__ = 'ats_connections'
    connection_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recruiter_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    provider = db.Column(db.String(50), nullable=False)  # 'greenhouse', 'lever', 'workday'
    api_key_encrypted = db.Column(db.Text, nullable=False)  # encrypted API key
    webhook_secret = db.Column(db.String(128), nullable=True)  # for inbound webhooks
    ats_org_id = db.Column(db.String(255), nullable=True)  # external ATS org identifier
    sync_status = db.Column(db.String(20), default='idle')  # idle, syncing, error, disabled
    last_synced_at = db.Column(db.DateTime, nullable=True)
    sync_cursor = db.Column(db.Text, nullable=True)  # pagination cursor for incremental sync
    config = db.Column(db.Text, nullable=True)  # JSON blob for provider-specific settings
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    recruiter = db.relationship('User', backref=db.backref('ats_connections', cascade='all, delete-orphan'))

    __table_args__ = (
        db.Index('ix_ats_connections_recruiter', 'recruiter_id'),
    )


class WebhookSubscription(db.Model):
    """Inbound webhook subscriptions for ATS events.

    When an ATS fires an event (candidate applied, job updated, etc.), the
    webhook hits our endpoint and we verify the signature using ``secret``.
    """
    __tablename__ = 'webhook_subscriptions'
    subscription_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_id = db.Column(UUID(as_uuid=True), db.ForeignKey('ats_connections.connection_id', ondelete='CASCADE'), nullable=False)
    event_type = db.Column(db.String(100), nullable=False)  # 'candidate.created', 'job.updated', etc.
    target_url = db.Column(db.Text, nullable=False)  # our internal webhook URL
    secret = db.Column(db.String(255), nullable=False)  # HMAC secret for signature verification
    is_active = db.Column(db.Boolean, default=True)
    last_triggered_at = db.Column(db.DateTime, nullable=True)
    failure_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    connection = db.relationship('ATSConnection', backref=db.backref('webhook_subscriptions', cascade='all, delete-orphan'))

    __table_args__ = (
        db.Index('ix_webhook_subscriptions_connection', 'connection_id'),
    )


class OAuthToken(db.Model):
    """OAuth tokens for calendar integrations (Google Calendar, Outlook).

    Stores encrypted refresh/access tokens and handles token lifecycle.
    """
    __tablename__ = 'oauth_tokens'
    token_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    provider = db.Column(db.String(50), nullable=False)  # 'google', 'microsoft'
    scopes = db.Column(db.Text, nullable=False)  # comma-separated OAuth scopes
    access_token_encrypted = db.Column(db.Text, nullable=False)
    refresh_token_encrypted = db.Column(db.Text, nullable=True)
    token_expiry = db.Column(db.DateTime, nullable=False)
    calendar_id = db.Column(db.String(255), nullable=True)  # default calendar ID
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('oauth_tokens', cascade='all, delete-orphan'))

    __table_args__ = (
        db.Index('ix_oauth_tokens_user_provider', 'user_id', 'provider'),
    )


class CalendarEvent(db.Model):
    """Scheduled interview calendar events synced via OAuth.

    Maps internal interview records to external calendar events for
    bi-directional sync.
    """
    __tablename__ = 'calendar_events'
    event_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id = db.Column(UUID(as_uuid=True), db.ForeignKey('interviews.interview_id', ondelete='CASCADE'), nullable=False)
    oauth_token_id = db.Column(UUID(as_uuid=True), db.ForeignKey('oauth_tokens.token_id', ondelete='CASCADE'), nullable=False)
    external_event_id = db.Column(db.String(255), nullable=True)  # Google/Outlook event ID
    provider = db.Column(db.String(50), nullable=False)
    sync_status = db.Column(db.String(20), default='pending')  # pending, synced, error
    last_synced_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    interview = db.relationship('Interview', backref=db.backref('calendar_events', cascade='all, delete-orphan'))
    oauth_token = db.relationship('OAuthToken', backref=db.backref('calendar_events', cascade='all, delete-orphan'))

    __table_args__ = (
        db.Index('ix_calendar_events_interview', 'interview_id'),
    )


class CommunicationChannel(db.Model):
    """Slack / Microsoft Teams notification channel configuration.

    Stores webhook URLs and channel mappings for recruiter notifications.
    """
    __tablename__ = 'communication_channels'
    channel_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recruiter_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    provider = db.Column(db.String(50), nullable=False)  # 'slack', 'teams'
    webhook_url = db.Column(db.Text, nullable=False)  # Slack/Teams incoming webhook URL
    channel_name = db.Column(db.String(255), nullable=True)  # display name
    channel_id_external = db.Column(db.String(255), nullable=True)  # Slack channel ID
    events_subscribed = db.Column(db.Text, default='application.received,application.shortlisted')  # comma-separated event types
    is_active = db.Column(db.Boolean, default=True)
    last_notified_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    recruiter = db.relationship('User', backref=db.backref('communication_channels', cascade='all, delete-orphan'))

    __table_args__ = (
        db.Index('ix_communication_channels_recruiter', 'recruiter_id'),
    )


class SSOProvider(db.Model):
    """SSO provider configuration (SAML / OIDC).

    Each organization can have one or more SSO providers for enterprise
    single sign-on.
    """
    __tablename__ = 'sso_providers'
    provider_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = db.Column(UUID(as_uuid=True), db.ForeignKey('organizations.org_id', ondelete='CASCADE'), nullable=True)
    name = db.Column(db.String(255), nullable=False)  # display name
    protocol = db.Column(db.String(20), nullable=False)  # 'saml' or 'oidc'
    issuer = db.Column(db.Text, nullable=False)  # IdP issuer URL
    client_id = db.Column(db.String(255), nullable=True)  # OIDC client ID
    client_secret_encrypted = db.Column(db.Text, nullable=True)  # OIDC client secret
    metadata_url = db.Column(db.Text, nullable=True)  # SAML metadata XML URL
    metadata_xml = db.Column(db.Text, nullable=True)  # cached SAML metadata XML
    certificate = db.Column(db.Text, nullable=True)  # SAML signing certificate
    redirect_url = db.Column(db.Text, nullable=False)  # callback URL
    auto_provision = db.Column(db.Boolean, default=True)  # auto-create users on first SSO login
    default_role = db.Column(db.String(50), default='viewer')  # role for auto-provisioned users
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = db.relationship('Organization', backref=db.backref('sso_providers', cascade='all, delete-orphan'))

    __table_args__ = (
        db.Index('ix_sso_providers_organization', 'organization_id'),
    )

