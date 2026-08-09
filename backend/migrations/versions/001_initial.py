"""Initial migration - create all SipSetu tables.

Revision ID: 001_initial
Revises: 
Create Date: 2026-08-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable uuid-ossp extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;')

    # USERS (base table)
    op.create_table(
        'users',
        sa.Column('user_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('profile_image', sa.Text(), nullable=True),
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.CheckConstraint("role IN ('applicant', 'recruiter')", name='users_role_check'),
    )

    # APPLICANTS
    op.create_table(
        'applicants',
        sa.Column('user_id', UUID(as_uuid=True), primary_key=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
    )

    # RECRUITERS
    op.create_table(
        'recruiters',
        sa.Column('user_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('company', sa.String(255), nullable=True),
        sa.Column('job_title', sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
    )

    # SKILLS
    op.create_table(
        'skills',
        sa.Column('skill_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('skill_name', sa.String(100), nullable=False, unique=True),
    )

    # JOBS
    op.create_table(
        'jobs',
        sa.Column('job_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('recruiter_id', UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('job_type', sa.String(50), nullable=True),
        sa.Column('experience_level', sa.String(50), nullable=True),
        sa.Column('salary_min', sa.Float(), nullable=True),
        sa.Column('salary_max', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['recruiter_id'], ['recruiters.user_id'], ondelete='CASCADE'),
    )

    # JOB_SKILLS junction
    op.create_table(
        'job_skills',
        sa.Column('job_id', UUID(as_uuid=True), nullable=False),
        sa.Column('skill_id', UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.job_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.skill_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('job_id', 'skill_id'),
    )

    # RESUMES
    op.create_table(
        'resumes',
        sa.Column('resume_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('applicant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['applicant_id'], ['applicants.user_id'], ondelete='CASCADE'),
    )

    # RESUME_SKILLS junction
    op.create_table(
        'resume_skills',
        sa.Column('resume_id', UUID(as_uuid=True), nullable=False),
        sa.Column('skill_id', UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.resume_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.skill_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('resume_id', 'skill_id'),
    )

    # JOB_APPLICATIONS
    op.create_table(
        'job_applications',
        sa.Column('application_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('job_id', UUID(as_uuid=True), nullable=False),
        sa.Column('applicant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('applied_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('status', sa.String(20), nullable=False, server_default=sa.text("'pending'")),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.job_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['applicant_id'], ['applicants.user_id'], ondelete='CASCADE'),
        sa.UniqueConstraint('job_id', 'applicant_id', name='uq_job_applicant_application'),
        sa.CheckConstraint("status IN ('pending', 'shortlisted', 'rejected')", name='job_applications_status_check'),
    )

    # RANKINGS
    op.create_table(
        'rankings',
        sa.Column('ranking_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('job_id', UUID(as_uuid=True), nullable=False),
        sa.Column('resume_id', UUID(as_uuid=True), nullable=False),
        sa.Column('matching_score', sa.Float(), nullable=True),
        sa.Column('candidate_rank', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.job_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.resume_id'], ondelete='CASCADE'),
    )

    # EMAIL_VERIFICATION_TOKENS
    op.create_table(
        'email_verification_tokens',
        sa.Column('token_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('token', sa.String(255), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
    )
    op.create_index('idx_email_verification_tokens_token', 'email_verification_tokens', ['token'])

    # PASSWORD_RESET_TOKENS
    op.create_table(
        'password_reset_tokens',
        sa.Column('token_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('token', sa.String(255), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
    )
    op.create_index('idx_password_reset_tokens_token', 'password_reset_tokens', ['token'])

    # SAVED_JOBS
    op.create_table(
        'saved_jobs',
        sa.Column('saved_job_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('applicant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['applicant_id'], ['applicants.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.job_id'], ondelete='CASCADE'),
        sa.UniqueConstraint('applicant_id', 'job_id', name='uq_applicant_saved_job'),
    )

    # INTERVIEWS
    op.create_table(
        'interviews',
        sa.Column('interview_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('job_id', UUID(as_uuid=True), nullable=False),
        sa.Column('applicant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('recruiter_id', UUID(as_uuid=True), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False, server_default=sa.text('60')),
        sa.Column('status', sa.String(20), nullable=False, server_default=sa.text("'pending'")),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('meeting_link', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.job_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['applicant_id'], ['applicants.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recruiter_id'], ['recruiters.user_id'], ondelete='CASCADE'),
        sa.CheckConstraint(
            "status IN ('pending', 'confirmed', 'completed', 'cancelled', 'declined')",
            name='interviews_status_check'
        ),
    )

    # SKILL_PROGRESS
    op.create_table(
        'skill_progress',
        sa.Column('progress_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('applicant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('skill_name', sa.String(100), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default=sa.text("'learning'")),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['applicant_id'], ['applicants.user_id'], ondelete='CASCADE'),
        sa.UniqueConstraint('applicant_id', 'skill_name', name='uq_applicant_skill_progress'),
        sa.CheckConstraint("status IN ('learning', 'learned')", name='skill_progress_status_check'),
    )

    # NOTIFICATIONS
    op.create_table(
        'notifications',
        sa.Column('notification_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('type', sa.String(50), nullable=False, server_default=sa.text("'info'")),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')),
        sa.Column('related_job_id', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['related_job_id'], ['jobs.job_id'], ondelete='SET NULL'),
        sa.CheckConstraint(
            "type IN ('info', 'success', 'warning', 'shortlisted', 'rejected')",
            name='notifications_type_check'
        ),
    )


def downgrade() -> None:
    op.drop_table('notifications')
    op.drop_table('skill_progress')
    op.drop_table('interviews')
    op.drop_table('saved_jobs')
    op.drop_index('idx_password_reset_tokens_token', table_name='password_reset_tokens')
    op.drop_table('password_reset_tokens')
    op.drop_index('idx_email_verification_tokens_token', table_name='email_verification_tokens')
    op.drop_table('email_verification_tokens')
    op.drop_table('rankings')
    op.drop_table('job_applications')
    op.drop_table('resume_skills')
    op.drop_table('resumes')
    op.drop_table('job_skills')
    op.drop_table('jobs')
    op.drop_table('skills')
    op.drop_table('recruiters')
    op.drop_table('applicants')
    op.drop_table('users')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp";')