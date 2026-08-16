import uuid
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
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
    
    skills = db.relationship('Skill', secondary=job_skills, backref=db.backref('jobs', lazy='dynamic'))
    rankings = db.relationship('Ranking', backref='job', lazy=True, cascade='all, delete-orphan')
    applications = db.relationship('JobApplication', backref='job', lazy=True, cascade='all, delete-orphan')

    # Phase 4.4 — hot-query composite indexes (mirrored by migration 003):
    #   - default public list + v1 keyset pagination (ORDER BY created_at DESC, job_id DESC)
    #   - recruiter's job list / dashboard (WHERE recruiter_id = ? ORDER BY created_at DESC)
    #   - job-type browsing (WHERE job_type = ? ORDER BY created_at DESC)
    __table_args__ = (
        db.Index('ix_jobs_created_at_id', 'created_at', 'job_id',
                 postgresql_ops={'created_at': 'DESC', 'job_id': 'DESC'}),
        db.Index('ix_jobs_recruiter_created', 'recruiter_id', 'created_at',
                 postgresql_ops={'created_at': 'DESC'}),
        db.Index('ix_jobs_type_created', 'job_type', 'created_at',
                 postgresql_ops={'created_at': 'DESC'}),
    )

class Resume(db.Model):
    __tablename__ = 'resumes'
    resume_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    applicant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('applicants.user_id', ondelete='CASCADE'), nullable=False)
    raw_text = db.Column(db.Text)
    file_path = db.Column(db.String(500))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

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

