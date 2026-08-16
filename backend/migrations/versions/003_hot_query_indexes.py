"""Add composite indexes for hot queries (Phase 4.4).

Covers the dominant read paths identified in the EXPLAIN ANALYZE audit:

- jobs:        default public list + v1 keyset pagination (created_at, job_id);
               recruiter job list/dashboard (recruiter_id, created_at);
               job-type browsing (job_type, created_at)
- rankings:    candidate lists (job_id, matching_score, ranking_id);
               ranking regeneration after resume changes (resume_id)
- notifications: notification list + unread badge (user_id, created_at)

Revision ID: 003_hot_query_indexes
Revises: 002_bulk_screen_jobs
Create Date: 2026-08-15 00:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '003_hot_query_indexes'
down_revision = '002_bulk_screen_jobs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Jobs — DESC variants so ORDER BY created_at DESC / keyset seek is an
    # index scan rather than a sort. postgresql_ops are ignored on SQLite.
    op.create_index(
        'ix_jobs_created_at_id', 'jobs', ['created_at', 'job_id'],
        postgresql_ops={'created_at': 'DESC', 'job_id': 'DESC'},
    )
    op.create_index(
        'ix_jobs_recruiter_created', 'jobs', ['recruiter_id', 'created_at'],
        postgresql_ops={'created_at': 'DESC'},
    )
    op.create_index(
        'ix_jobs_type_created', 'jobs', ['job_type', 'created_at'],
        postgresql_ops={'created_at': 'DESC'},
    )

    # Rankings — candidate list query filters job_id + matching_score range and
    # orders by (matching_score DESC, ranking_id DESC) for cursor pagination.
    op.create_index(
        'ix_rankings_job_score', 'rankings',
        ['job_id', 'matching_score', 'ranking_id'],
        postgresql_ops={'matching_score': 'DESC', 'ranking_id': 'DESC'},
    )
    op.create_index('ix_rankings_resume', 'rankings', ['resume_id'])

    # Notifications — per-user feed ordered newest-first.
    op.create_index(
        'ix_notifications_user_created', 'notifications', ['user_id', 'created_at'],
        postgresql_ops={'created_at': 'DESC'},
    )


def downgrade() -> None:
    op.drop_index('ix_notifications_user_created', table_name='notifications')
    op.drop_index('ix_rankings_resume', table_name='rankings')
    op.drop_index('ix_rankings_job_score', table_name='rankings')
    op.drop_index('ix_jobs_type_created', table_name='jobs')
    op.drop_index('ix_jobs_recruiter_created', table_name='jobs')
    op.drop_index('ix_jobs_created_at_id', table_name='jobs')
