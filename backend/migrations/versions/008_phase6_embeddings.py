"""Add embedding columns for semantic search (Phase 6.2)

Revision ID: 008
Revises: 007
Create Date: 2026-08-23
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('jobs', sa.Column('embedding', sa.Text(), nullable=True))
    op.add_column('resumes', sa.Column('embedding', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('resumes', 'embedding')
    op.drop_column('jobs', 'embedding')
