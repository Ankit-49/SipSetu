"""Add user locale preference for i18n (Phase 6.4).

Revision ID: 011
Revises: 010_add_reminders_sent
Create Date: 2026-08-25
"""

from alembic import op
import sqlalchemy as sa

revision = "011_add_user_locale"
down_revision = "010_add_reminders_sent"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("locale", sa.String(10), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "locale")
