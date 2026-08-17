"""Add pg_trgm GIN indexes for the jobs search path (Phase 4.4 follow-up).

GET /jobs?search=... filters with leading-wildcard ILIKE patterns:

    title.ilike('%term%') OR location.ilike('%term%') OR job_type.ilike('%term%')

A btree index cannot help leading-wildcard LIKE, which is why the Phase 4.4
audit (explain_analyze.sql) flagged this path as non-indexable. The pg_trgm
extension provides trigram GIN indexes that DO support '%term%' patterns, so
the planner can use a Bitmap Index Scan instead of a Seq Scan.

Notes:
- The GIN index only helps when the LIKE pattern contains at least 3
  characters (trigram granularity); 1-2 character searches still Seq Scan,
  which is acceptable for those rare queries.
- ILIKE is handled because pg_trgm indexes are case-insensitive by default
  (trigrams are extracted from lowercased text).
- postgresql_using/ops are ignored on SQLite, so db.create_all() parity is
  preserved (the model adds plain btree equivalents).

Revision ID: 004_pg_trgm_jobs_search
Revises: 003_hot_query_indexes
Create Date: 2026-08-16 00:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '004_pg_trgm_jobs_search'
down_revision = '003_hot_query_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')

    op.create_index(
        'ix_jobs_title_trgm', 'jobs', ['title'],
        postgresql_using='gin',
        postgresql_ops={'title': 'gin_trgm_ops'},
    )
    op.create_index(
        'ix_jobs_location_trgm', 'jobs', ['location'],
        postgresql_using='gin',
        postgresql_ops={'location': 'gin_trgm_ops'},
    )
    op.create_index(
        'ix_jobs_job_type_trgm', 'jobs', ['job_type'],
        postgresql_using='gin',
        postgresql_ops={'job_type': 'gin_trgm_ops'},
    )


def downgrade() -> None:
    op.drop_index('ix_jobs_job_type_trgm', table_name='jobs')
    op.drop_index('ix_jobs_location_trgm', table_name='jobs')
    op.drop_index('ix_jobs_title_trgm', table_name='jobs')
    op.execute('DROP EXTENSION IF EXISTS pg_trgm')
