"""Phase 6.3 — Integration tables (ATS, Calendar, Communication, SSO).

Revision ID: 009_integrations
Revises: 008_phase6_embeddings
Create Date: 2026-08-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PgUUID

revision = '009_integrations'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use raw connection to check dialect
    bind = op.get_bind()
    dialect = bind.dialect.name

    uuid_type = PgUUID(as_uuid=True) if dialect == 'postgresql' else sa.String(36)

    # ATS Connections
    op.create_table(
        'ats_connections',
        sa.Column('connection_id', uuid_type, primary_key=True),
        sa.Column('recruiter_id', uuid_type, sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('api_key_encrypted', sa.Text, nullable=False),
        sa.Column('webhook_secret', sa.String(128), nullable=True),
        sa.Column('ats_org_id', sa.String(255), nullable=True),
        sa.Column('sync_status', sa.String(20), server_default='idle'),
        sa.Column('last_synced_at', sa.DateTime, nullable=True),
        sa.Column('sync_cursor', sa.Text, nullable=True),
        sa.Column('config', sa.Text, nullable=True),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_ats_connections_recruiter', 'ats_connections', ['recruiter_id'])

    # Webhook Subscriptions
    op.create_table(
        'webhook_subscriptions',
        sa.Column('subscription_id', uuid_type, primary_key=True),
        sa.Column('connection_id', uuid_type, sa.ForeignKey('ats_connections.connection_id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('target_url', sa.Text, nullable=False),
        sa.Column('secret', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('last_triggered_at', sa.DateTime, nullable=True),
        sa.Column('failure_count', sa.Integer, server_default='0'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_webhook_subscriptions_connection', 'webhook_subscriptions', ['connection_id'])

    # OAuth Tokens (Calendar)
    op.create_table(
        'oauth_tokens',
        sa.Column('token_id', uuid_type, primary_key=True),
        sa.Column('user_id', uuid_type, sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('scopes', sa.Text, nullable=False),
        sa.Column('access_token_encrypted', sa.Text, nullable=False),
        sa.Column('refresh_token_encrypted', sa.Text, nullable=True),
        sa.Column('token_expiry', sa.DateTime, nullable=False),
        sa.Column('calendar_id', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_oauth_tokens_user_provider', 'oauth_tokens', ['user_id', 'provider'])

    # Calendar Events
    op.create_table(
        'calendar_events',
        sa.Column('event_id', uuid_type, primary_key=True),
        sa.Column('interview_id', uuid_type, sa.ForeignKey('interviews.interview_id', ondelete='CASCADE'), nullable=False),
        sa.Column('oauth_token_id', uuid_type, sa.ForeignKey('oauth_tokens.token_id', ondelete='CASCADE'), nullable=False),
        sa.Column('external_event_id', sa.String(255), nullable=True),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('sync_status', sa.String(20), server_default='pending'),
        sa.Column('last_synced_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_calendar_events_interview', 'calendar_events', ['interview_id'])

    # Communication Channels (Slack/Teams)
    op.create_table(
        'communication_channels',
        sa.Column('channel_id', uuid_type, primary_key=True),
        sa.Column('recruiter_id', uuid_type, sa.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('webhook_url', sa.Text, nullable=False),
        sa.Column('channel_name', sa.String(255), nullable=True),
        sa.Column('channel_id_external', sa.String(255), nullable=True),
        sa.Column('events_subscribed', sa.Text, server_default='application.received,application.shortlisted'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('last_notified_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_communication_channels_recruiter', 'communication_channels', ['recruiter_id'])

    # SSO Providers
    op.create_table(
        'sso_providers',
        sa.Column('provider_id', uuid_type, primary_key=True),
        sa.Column('organization_id', uuid_type, sa.ForeignKey('organizations.org_id', ondelete='CASCADE'), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('protocol', sa.String(20), nullable=False),
        sa.Column('issuer', sa.Text, nullable=False),
        sa.Column('client_id', sa.String(255), nullable=True),
        sa.Column('client_secret_encrypted', sa.Text, nullable=True),
        sa.Column('metadata_url', sa.Text, nullable=True),
        sa.Column('metadata_xml', sa.Text, nullable=True),
        sa.Column('certificate', sa.Text, nullable=True),
        sa.Column('redirect_url', sa.Text, nullable=False),
        sa.Column('auto_provision', sa.Boolean, server_default='true'),
        sa.Column('default_role', sa.String(50), server_default='viewer'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_sso_providers_organization', 'sso_providers', ['organization_id'])


def downgrade() -> None:
    op.drop_table('sso_providers')
    op.drop_table('communication_channels')
    op.drop_table('calendar_events')
    op.drop_table('oauth_tokens')
    op.drop_table('webhook_subscriptions')
    op.drop_table('ats_connections')
