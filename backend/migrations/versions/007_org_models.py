"""Add Organization and OrganizationMember models (Phase 6.1)

Revision ID: 007
Revises: 006
Create Date: 2026-08-23
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create organizations table
    op.create_table(
        'organizations',
        sa.Column('org_id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False, unique=True),
        sa.Column('logo_url', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('website', sa.String(500), nullable=True),
        sa.Column('industry', sa.String(100), nullable=True),
        sa.Column('size', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_organizations_slug', 'organizations', ['slug'])

    # Create organization_members table
    op.create_table(
        'organization_members',
        sa.Column('membership_id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', sa.dialects.postgresql.UUID(as_uuid=True),
                   sa.ForeignKey('organizations.org_id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True),
                   sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(30), nullable=False, server_default='viewer'),
        sa.Column('invited_by', sa.dialects.postgresql.UUID(as_uuid=True),
                   sa.ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True),
        sa.Column('joined_at', sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('org_id', 'user_id', name='uq_org_user_membership'),
    )
    op.create_index('ix_org_members_user', 'organization_members', ['user_id'])

    # Add optional organization_id FK to jobs
    op.add_column('jobs', sa.Column('organization_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_jobs_organization', 'jobs', 'organizations', ['organization_id'], ['org_id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint('fk_jobs_organization', 'jobs', type_='foreignkey')
    op.drop_column('jobs', 'organization_id')
    op.drop_index('ix_org_members_user', 'organization_members')
    op.drop_table('organization_members')
    op.drop_index('ix_organizations_slug', 'organizations')
    op.drop_table('organizations')
