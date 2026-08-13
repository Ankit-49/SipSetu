"""Add bulk_screen_jobs table for async bulk resume screening.

Revision ID: 002_bulk_screen_jobs
Revises: 001_initial
Create Date: 2026-08-13 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '002_bulk_screen_jobs'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'bulk_screen_jobs',
        sa.Column('job_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('recruiter_id', UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default=sa.text("'queued'")),
        sa.Column('total_files', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('processed_files', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('file_paths', sa.Text(), nullable=True),
        sa.Column('job_title', sa.String(255), nullable=True),
        sa.Column('job_skills', sa.Text(), nullable=True),
        sa.Column('job_desc', sa.Text(), nullable=True),
        sa.Column('target_experience_years', sa.Float(), nullable=True),
        sa.Column('job_experience_level', sa.String(50), nullable=True),
        sa.Column('results', sa.Text(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['recruiter_id'], ['recruiters.user_id'], ondelete='CASCADE'),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'completed', 'failed')",
            name='bulk_screen_jobs_status_check'
        ),
    )
    op.create_index('idx_bulk_screen_jobs_recruiter_id', 'bulk_screen_jobs', ['recruiter_id'])


def downgrade() -> None:
    op.drop_index('idx_bulk_screen_jobs_recruiter_id', table_name='bulk_screen_jobs')
    op.drop_table('bulk_screen_jobs')
