"""Add full-text search support to jobs (Phase 4.4 follow-up).

GET /jobs?search=term was previously a leading-wildcard ILIKE over
title/location/job_type. This migration adds a maintained ``search_vector``
tsvector column + GIN index so Postgres can answer the query with

    search_vector @@ plainto_tsquery('english', term)

and rank results by relevance (ts_rank). The column is written by the
application (routes_common.set_job_search_vector) on every job create/update
so the value always matches this backfill expression; the migration backfills
rows created before the column existed. SQLite dev/tests ignore the column
(always NULL) and keep using the ILIKE fallback path.

Revision ID: 005_jobs_full_text_search
Revises: 004_pg_trgm_jobs_search
Create Date: 2026-08-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_jobs_full_text_search'
down_revision = '004_pg_trgm_jobs_search'
branch_labels = None
depends_on = None

_SEARCH_VECTOR_EXPR = (
    "to_tsvector('english', "
    "coalesce(title, '') || ' ' || coalesce(description, '') || ' ' || "
    "coalesce(location, '') || ' ' || coalesce(job_type, ''))"
)


def upgrade() -> None:
    op.add_column(
        'jobs',
        sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True),
    )
    # Backfill rows created before the column existed so nothing is invisible
    # to search after the migration.
    op.execute(
        f'UPDATE jobs SET search_vector = {_SEARCH_VECTOR_EXPR} '
        'WHERE search_vector IS NULL'
    )
    op.create_index(
        'ix_jobs_search_vector', 'jobs', ['search_vector'],
        postgresql_using='gin',
    )


def downgrade() -> None:
    op.drop_index('ix_jobs_search_vector', table_name='jobs')
    op.drop_column('jobs', 'search_vector')
