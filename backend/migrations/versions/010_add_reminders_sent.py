"""Add missing reminders_sent column to interviews.

Revision ID: 010_add_reminders_sent
Revises: 009_integrations
Create Date: 2026-08-24

"""
from alembic import op
import sqlalchemy as sa

revision = '010_add_reminders_sent'
down_revision = '009_integrations'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('interviews', sa.Column('reminders_sent', sa.String(255), server_default='', nullable=False))


def downgrade() -> None:
    op.drop_column('interviews', 'reminders_sent')
