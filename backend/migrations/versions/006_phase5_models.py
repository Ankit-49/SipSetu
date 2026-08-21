"""006 — Phase 5 models: ranking_feedback, audit_logs, resume LLM columns.

Revision ID: 006
Revises: 005
Create Date: 2026-08-21
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '006'
down_revision = '005_jobs_full_text_search'
branch_labels = None
depends_on = None


def upgrade():
    # --- ranking_feedback table ---
    op.create_table(
        'ranking_feedback',
        sa.Column('feedback_id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('ranking_id', sa.dialects.postgresql.UUID(as_uuid=True),
                   sa.ForeignKey('rankings.ranking_id', ondelete='CASCADE'), nullable=False),
        sa.Column('recruiter_id', sa.dialects.postgresql.UUID(as_uuid=True),
                   sa.ForeignKey('recruiters.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('direction', sa.String(10), nullable=False),
        sa.Column('note', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint('ranking_id', 'recruiter_id', name='uq_ranking_recruiter_feedback'),
    )
    op.create_index('ix_ranking_feedback_ranking', 'ranking_feedback', ['ranking_id'])

    # --- audit_logs table ---
    op.create_table(
        'audit_logs',
        sa.Column('log_id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('actor_id', sa.dialects.postgresql.UUID(as_uuid=True),
                   sa.ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('target_type', sa.String(50), nullable=True),
        sa.Column('target_id', sa.String(255), nullable=True),
        sa.Column('details', sa.Text, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_audit_logs_actor_created', 'audit_logs', ['actor_id', 'created_at'],
                     postgresql_ops={'created_at': 'DESC'})

    # --- Resume LLM columns ---
    op.add_column('resumes', sa.Column('parsed_sections', sa.Text, nullable=True))
    op.add_column('resumes', sa.Column('parse_confidence', sa.Float, nullable=True))
    op.add_column('resumes', sa.Column('parse_method', sa.String(20), nullable=True))


def downgrade():
    op.drop_column('resumes', 'parse_method')
    op.drop_column('resumes', 'parse_confidence')
    op.drop_column('resumes', 'parsed_sections')
    op.drop_index('ix_audit_logs_actor_created', 'audit_logs')
    op.drop_table('audit_logs')
    op.drop_index('ix_ranking_feedback_ranking', 'ranking_feedback')
    op.drop_table('ranking_feedback')
