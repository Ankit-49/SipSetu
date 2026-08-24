"""Phase 6.3 — Integration routes: ATS sync, Calendar, Communication, SSO.

Endpoints:
  6.3a — ATS Sync:
    GET    /ats/connections               List ATS connections
    POST   /ats/connections               Create ATS connection
    GET    /ats/connections/<id>          Get connection detail
    DELETE /ats/connections/<id>          Disconnect ATS
    POST   /ats/connections/<id>/sync     Trigger manual sync
    POST   /ats/webhook/<connection_id>   Inbound webhook receiver
    GET    /ats/connections/<id>/webhooks List webhook subscriptions
    POST   /ats/connections/<id>/webhooks Create webhook subscription

  6.3b — Calendar:
    GET    /calendar/tokens               List OAuth tokens
    POST   /calendar/tokens               Store OAuth token (after OAuth flow)
    DELETE /calendar/tokens/<id>          Remove OAuth token
    GET    /calendar/events               List calendar events
    POST   /calendar/events               Create calendar event for interview
    PUT    /calendar/events/<id>/sync     Sync event to external calendar
    DELETE /calendar/events/<id>          Delete calendar event

  6.3c — Communication (Slack/Teams):
    GET    /channels                      List communication channels
    POST   /channels                      Add Slack/Teams channel
    GET    /channels/<id>                 Get channel detail
    DELETE /channels/<id>                 Remove channel
    POST   /channels/<id>/test            Send test notification
    GET    /channels/events               List available event types

  6.3d — SSO:
    GET    /sso/providers                 List SSO providers
    POST   /sso/providers                 Create SSO provider
    GET    /sso/providers/<id>            Get provider detail
    PUT    /sso/providers/<id>            Update provider
    DELETE /sso/providers/<id>            Remove provider
    POST   /sso/providers/<id>/metadata   Refresh SAML metadata
    POST   /sso/login/<provider_id>       Initiate SSO login (returns redirect URL)
    POST   /sso/callback                  SSO callback (OIDC code exchange)
"""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, current_app, g, jsonify, request

from auth_middleware import require_auth, require_role
from models import (
    ATSConnection,
    CalendarEvent,
    CommunicationChannel,
    OAuthToken,
    SSOProvider,
    WebhookSubscription,
    db,
)

phase63 = Blueprint('phase63', __name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _json_safe(obj):
    """Convert datetimes to ISO strings for JSON serialisation."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj


def _serialize_ats(conn):
    return {
        "connection_id": str(conn.connection_id),
        "recruiter_id": str(conn.recruiter_id),
        "provider": conn.provider,
        "ats_org_id": conn.ats_org_id,
        "sync_status": conn.sync_status,
        "last_synced_at": _json_safe(conn.last_synced_at),
        "is_active": conn.is_active,
        "created_at": _json_safe(conn.created_at),
    }


def _serialize_webhook(sub):
    return {
        "subscription_id": str(sub.subscription_id),
        "connection_id": str(sub.connection_id),
        "event_type": sub.event_type,
        "target_url": sub.target_url,
        "is_active": sub.is_active,
        "last_triggered_at": _json_safe(sub.last_triggered_at),
        "failure_count": sub.failure_count,
    }


def _serialize_oauth(token):
    return {
        "token_id": str(token.token_id),
        "user_id": str(token.user_id),
        "provider": token.provider,
        "scopes": token.scopes,
        "calendar_id": token.calendar_id,
        "is_active": token.is_active,
        "token_expiry": _json_safe(token.token_expiry),
        "created_at": _json_safe(token.created_at),
    }


def _serialize_calendar_event(evt):
    return {
        "event_id": str(evt.event_id),
        "interview_id": str(evt.interview_id),
        "provider": evt.provider,
        "external_event_id": evt.external_event_id,
        "sync_status": evt.sync_status,
        "last_synced_at": _json_safe(evt.last_synced_at),
    }


def _serialize_channel(ch):
    return {
        "channel_id": str(ch.channel_id),
        "recruiter_id": str(ch.recruiter_id),
        "provider": ch.provider,
        "channel_name": ch.channel_name,
        "channel_id_external": ch.channel_id_external,
        "events_subscribed": ch.events_subscribed,
        "is_active": ch.is_active,
        "last_notified_at": _json_safe(ch.last_notified_at),
        "created_at": _json_safe(ch.created_at),
    }


def _serialize_sso(prov):
    return {
        "provider_id": str(prov.provider_id),
        "organization_id": str(prov.organization_id) if prov.organization_id else None,
        "name": prov.name,
        "protocol": prov.protocol,
        "issuer": prov.issuer,
        "redirect_url": prov.redirect_url,
        "auto_provision": prov.auto_provision,
        "default_role": prov.default_role,
        "is_active": prov.is_active,
        "created_at": _json_safe(prov.created_at),
    }


# ─── 6.3a — ATS Sync ────────────────────────────────────────────────────────


@phase63.route('/ats/connections', methods=['GET'])
@require_auth
def list_ats_connections():
    """List all ATS connections for the current recruiter."""
    conns = ATSConnection.query.filter_by(recruiter_id=g.current_user_id).all()
    return jsonify([_serialize_ats(c) for c in conns])


@phase63.route('/ats/connections', methods=['POST'])
@require_role('recruiter', 'admin')
def create_ats_connection():
    """Create a new ATS connection (Greenhouse, Lever, Workday)."""
    data = request.get_json(force=True) or {}
    provider = (data.get('provider') or '').lower().strip()
    api_key = (data.get('api_key') or '').strip()

    if provider not in ('greenhouse', 'lever', 'workday'):
        return jsonify({"error": "provider must be 'greenhouse', 'lever', or 'workday'"}), 400
    if not api_key:
        return jsonify({"error": "api_key is required"}), 400

    conn = ATSConnection(
        recruiter_id=g.current_user_id,
        provider=provider,
        api_key_encrypted=hashlib.sha256(api_key.encode()).hexdigest(),  # placeholder encryption
        webhook_secret=secrets.token_hex(32),
        ats_org_id=data.get('ats_org_id'),
        config=json.dumps(data.get('config', {})),
    )
    db.session.add(conn)
    db.session.commit()
    return jsonify(_serialize_ats(conn)), 201


@phase63.route('/ats/connections/<connection_id>', methods=['GET'])
@require_auth
def get_ats_connection(connection_id):
    """Get ATS connection detail."""
    conn = ATSConnection.query.get(connection_id)
    if not conn or str(conn.recruiter_id) != g.current_user_id:
        return jsonify({"error": "Connection not found"}), 404
    return jsonify(_serialize_ats(conn))


@phase63.route('/ats/connections/<connection_id>', methods=['DELETE'])
@require_auth
def delete_ats_connection(connection_id):
    """Disconnect an ATS integration."""
    conn = ATSConnection.query.get(connection_id)
    if not conn or str(conn.recruiter_id) != g.current_user_id:
        return jsonify({"error": "Connection not found"}), 404
    db.session.delete(conn)
    db.session.commit()
    return jsonify({"message": "ATS connection deleted"}), 200


@phase63.route('/ats/connections/<connection_id>/sync', methods=['POST'])
@require_auth
def trigger_ats_sync(connection_id):
    """Trigger a manual sync with the connected ATS."""
    conn = ATSConnection.query.get(connection_id)
    if not conn or str(conn.recruiter_id) != g.current_user_id:
        return jsonify({"error": "Connection not found"}), 404
    if not conn.is_active:
        return jsonify({"error": "Connection is disabled"}), 400
    conn.sync_status = 'syncing'
    conn.last_synced_at = datetime.utcnow()
    db.session.commit()
    # In production, this would dispatch a background task (Celery)
    return jsonify({"message": "Sync started", "status": conn.sync_status})


@phase63.route('/ats/webhook/<connection_id>', methods=['POST'])
def receive_ats_webhook(connection_id):
    """Receive inbound webhook from an ATS provider.

    Verifies the HMAC signature using the connection's webhook_secret.
    """
    conn = ATSConnection.query.get(connection_id)
    if not conn or not conn.is_active:
        return jsonify({"error": "Connection not found or inactive"}), 404

    # Verify HMAC signature
    signature = request.headers.get('X-Hub-Signature-256', '')
    if conn.webhook_secret:
        expected = 'sha256=' + hmac.new(
            conn.webhook_secret.encode(), request.data, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return jsonify({"error": "Invalid signature"}), 401

    payload = request.get_json(force=True) or {}
    event_type = payload.get('event', 'unknown')

    # In production, this would dispatch to a background processor
    # For now, return accepted
    return jsonify({
        "message": "Webhook received",
        "event_type": event_type,
        "provider": conn.provider,
    }), 200


@phase63.route('/ats/connections/<connection_id>/webhooks', methods=['GET'])
@require_auth
def list_webhook_subscriptions(connection_id):
    """List webhook subscriptions for an ATS connection."""
    conn = ATSConnection.query.get(connection_id)
    if not conn or str(conn.recruiter_id) != g.current_user_id:
        return jsonify({"error": "Connection not found"}), 404
    subs = WebhookSubscription.query.filter_by(connection_id=connection_id).all()
    return jsonify([_serialize_webhook(s) for s in subs])


@phase63.route('/ats/connections/<connection_id>/webhooks', methods=['POST'])
@require_auth
def create_webhook_subscription(connection_id):
    """Create a webhook subscription for an ATS connection."""
    conn = ATSConnection.query.get(connection_id)
    if not conn or str(conn.recruiter_id) != g.current_user_id:
        return jsonify({"error": "Connection not found"}), 404

    data = request.get_json(force=True) or {}
    event_type = (data.get('event_type') or '').strip()
    target_url = (data.get('target_url') or '').strip()

    if not event_type or not target_url:
        return jsonify({"error": "event_type and target_url are required"}), 400

    sub = WebhookSubscription(
        connection_id=connection_id,
        event_type=event_type,
        target_url=target_url,
        secret=secrets.token_hex(32),
    )
    db.session.add(sub)
    db.session.commit()
    return jsonify(_serialize_webhook(sub)), 201


# ─── 6.3b — Calendar ────────────────────────────────────────────────────────


@phase63.route('/calendar/tokens', methods=['GET'])
@require_auth
def list_calendar_tokens():
    """List OAuth tokens for calendar integrations."""
    tokens = OAuthToken.query.filter_by(user_id=g.current_user_id).all()
    return jsonify([_serialize_oauth(t) for t in tokens])


@phase63.route('/calendar/tokens', methods=['POST'])
@require_auth
def create_calendar_token():
    """Store an OAuth token after completing the OAuth flow."""
    data = request.get_json(force=True) or {}
    provider = (data.get('provider') or '').lower().strip()
    access_token = (data.get('access_token') or '').strip()

    if provider not in ('google', 'microsoft'):
        return jsonify({"error": "provider must be 'google' or 'microsoft'"}), 400
    if not access_token:
        return jsonify({"error": "access_token is required"}), 400

    token = OAuthToken(
        user_id=g.current_user_id,
        provider=provider,
        scopes=data.get('scopes', 'calendar.events'),
        access_token_encrypted=hashlib.sha256(access_token.encode()).hexdigest(),
        refresh_token_encrypted=hashlib.sha256(data.get('refresh_token', '').encode()).hexdigest() if data.get('refresh_token') else None,
        token_expiry=datetime.utcnow() + timedelta(hours=data.get('expires_in', 3600) // 3600),
        calendar_id=data.get('calendar_id'),
    )
    db.session.add(token)
    db.session.commit()
    return jsonify(_serialize_oauth(token)), 201


@phase63.route('/calendar/tokens/<token_id>', methods=['DELETE'])
@require_auth
def delete_calendar_token(token_id):
    """Remove a calendar OAuth token."""
    token = OAuthToken.query.get(token_id)
    if not token or str(token.user_id) != g.current_user_id:
        return jsonify({"error": "Token not found"}), 404
    db.session.delete(token)
    db.session.commit()
    return jsonify({"message": "Calendar token deleted"}), 200


@phase63.route('/calendar/events', methods=['GET'])
@require_auth
def list_calendar_events():
    """List calendar events for the current user's interviews."""
    events = (
        CalendarEvent.query
        .join(OAuthToken, CalendarEvent.oauth_token_id == OAuthToken.token_id)
        .filter(OAuthToken.user_id == g.current_user_id)
        .all()
    )
    return jsonify([_serialize_calendar_event(e) for e in events])


@phase63.route('/calendar/events', methods=['POST'])
@require_auth
def create_calendar_event():
    """Create a calendar event for an interview."""
    data = request.get_json(force=True) or {}
    interview_id = data.get('interview_id')
    token_id = data.get('token_id')
    provider = (data.get('provider') or 'google').lower()

    if not interview_id or not token_id:
        return jsonify({"error": "interview_id and token_id are required"}), 400

    # Verify the token belongs to the user
    token = OAuthToken.query.get(token_id)
    if not token or str(token.user_id) != g.current_user_id:
        return jsonify({"error": "Token not found"}), 404

    evt = CalendarEvent(
        interview_id=interview_id,
        oauth_token_id=token_id,
        provider=provider,
        sync_status='pending',
    )
    db.session.add(evt)
    db.session.commit()
    return jsonify(_serialize_calendar_event(evt)), 201


@phase63.route('/calendar/events/<event_id>/sync', methods=['PUT'])
@require_auth
def sync_calendar_event(event_id):
    """Sync a calendar event to the external provider (Google/Outlook)."""
    evt = CalendarEvent.query.get(event_id)
    if not evt:
        return jsonify({"error": "Calendar event not found"}), 404
    # In production, this would call Google Calendar API / Microsoft Graph API
    evt.sync_status = 'synced'
    evt.external_event_id = secrets.token_hex(16)  # placeholder
    evt.last_synced_at = datetime.utcnow()
    db.session.commit()
    return jsonify(_serialize_calendar_event(evt))


@phase63.route('/calendar/events/<event_id>', methods=['DELETE'])
@require_auth
def delete_calendar_event(event_id):
    """Delete a calendar event."""
    evt = CalendarEvent.query.get(event_id)
    if not evt:
        return jsonify({"error": "Calendar event not found"}), 404
    db.session.delete(evt)
    db.session.commit()
    return jsonify({"message": "Calendar event deleted"}), 200


# ─── 6.3c — Communication (Slack/Teams) ─────────────────────────────────────

AVAILABLE_EVENTS = [
    "application.received",
    "application.shortlisted",
    "application.rejected",
    "application.withdrawn",
    "interview.scheduled",
    "interview.confirmed",
    "interview.completed",
    "job.created",
    "job.updated",
    "bulk_screen.completed",
]


@phase63.route('/channels', methods=['GET'])
@require_auth
def list_communication_channels():
    """List Slack/Teams notification channels."""
    channels = CommunicationChannel.query.filter_by(recruiter_id=g.current_user_id).all()
    return jsonify([_serialize_channel(c) for c in channels])


@phase63.route('/channels', methods=['POST'])
@require_role('recruiter', 'admin')
def create_communication_channel():
    """Add a Slack or Teams notification channel."""
    data = request.get_json(force=True) or {}
    provider = (data.get('provider') or '').lower().strip()
    webhook_url = (data.get('webhook_url') or '').strip()

    if provider not in ('slack', 'teams'):
        return jsonify({"error": "provider must be 'slack' or 'teams'"}), 400
    if not webhook_url:
        return jsonify({"error": "webhook_url is required"}), 400

    channel = CommunicationChannel(
        recruiter_id=g.current_user_id,
        provider=provider,
        webhook_url=webhook_url,
        channel_name=data.get('channel_name'),
        channel_id_external=data.get('channel_id_external'),
        events_subscribed=data.get('events_subscribed', 'application.received,application.shortlisted'),
    )
    db.session.add(channel)
    db.session.commit()
    return jsonify(_serialize_channel(channel)), 201


@phase63.route('/channels/<channel_id>', methods=['GET'])
@require_auth
def get_communication_channel(channel_id):
    """Get channel detail."""
    ch = CommunicationChannel.query.get(channel_id)
    if not ch or str(ch.recruiter_id) != g.current_user_id:
        return jsonify({"error": "Channel not found"}), 404
    return jsonify(_serialize_channel(ch))


@phase63.route('/channels/<channel_id>', methods=['DELETE'])
@require_auth
def delete_communication_channel(channel_id):
    """Remove a notification channel."""
    ch = CommunicationChannel.query.get(channel_id)
    if not ch or str(ch.recruiter_id) != g.current_user_id:
        return jsonify({"error": "Channel not found"}), 404
    db.session.delete(ch)
    db.session.commit()
    return jsonify({"message": "Channel deleted"}), 200


@phase63.route('/channels/<channel_id>/test', methods=['POST'])
@require_auth
def test_communication_channel(channel_id):
    """Send a test notification to a channel."""
    ch = CommunicationChannel.query.get(channel_id)
    if not ch or str(ch.recruiter_id) != g.current_user_id:
        return jsonify({"error": "Channel not found"}), 404
    if not ch.is_active:
        return jsonify({"error": "Channel is disabled"}), 400

    # In production, this would POST to the Slack/Teams webhook URL
    ch.last_notified_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"message": f"Test notification sent to {ch.provider}", "status": "sent"})


@phase63.route('/channels/events', methods=['GET'])
@require_auth
def list_available_events():
    """List available event types for channel subscriptions."""
    return jsonify({"events": AVAILABLE_EVENTS})


# ─── 6.3d — SSO ──────────────────────────────────────────────────────────────


@phase63.route('/sso/providers', methods=['GET'])
@require_auth
def list_sso_providers():
    """List SSO providers for the current user's organization(s)."""
    from models import OrganizationMember

    # Get org IDs the user belongs to
    memberships = OrganizationMember.query.filter_by(user_id=g.current_user_id).all()
    org_ids = [str(m.organization_id) for m in memberships]

    if not org_ids:
        # Return global SSO providers (no org)
        providers = SSOProvider.query.filter_by(organization_id=None, is_active=True).all()
    else:
        providers = SSOProvider.query.filter(
            db.or_(
                SSOProvider.organization_id.in_(org_ids),
                SSOProvider.organization_id.is_(None),
            ),
            SSOProvider.is_active.is_(True),
        ).all()

    return jsonify([_serialize_sso(p) for p in providers])


@phase63.route('/sso/providers', methods=['POST'])
@require_role('recruiter', 'admin')
def create_sso_provider():
    """Create an SSO provider configuration."""
    data = request.get_json(force=True) or {}
    name = (data.get('name') or '').strip()
    protocol = (data.get('protocol') or '').lower().strip()
    issuer = (data.get('issuer') or '').strip()
    redirect_url = (data.get('redirect_url') or '').strip()

    if not name or not protocol or not issuer or not redirect_url:
        return jsonify({"error": "name, protocol, issuer, and redirect_url are required"}), 400
    if protocol not in ('saml', 'oidc'):
        return jsonify({"error": "protocol must be 'saml' or 'oidc'"}), 400

    prov = SSOProvider(
        organization_id=data.get('organization_id'),
        name=name,
        protocol=protocol,
        issuer=issuer,
        client_id=data.get('client_id'),
        client_secret_encrypted=hashlib.sha256((data.get('client_secret') or '').encode()).hexdigest() if data.get('client_secret') else None,
        metadata_url=data.get('metadata_url'),
        certificate=data.get('certificate'),
        redirect_url=redirect_url,
        auto_provision=data.get('auto_provision', True),
        default_role=data.get('default_role', 'viewer'),
    )
    db.session.add(prov)
    db.session.commit()
    return jsonify(_serialize_sso(prov)), 201


@phase63.route('/sso/providers/<provider_id>', methods=['GET'])
@require_auth
def get_sso_provider(provider_id):
    """Get SSO provider detail."""
    prov = SSOProvider.query.get(provider_id)
    if not prov:
        return jsonify({"error": "SSO provider not found"}), 404
    return jsonify(_serialize_sso(prov))


@phase63.route('/sso/providers/<provider_id>', methods=['PUT'])
@require_auth
def update_sso_provider(provider_id):
    """Update an SSO provider configuration."""
    prov = SSOProvider.query.get(provider_id)
    if not prov:
        return jsonify({"error": "SSO provider not found"}), 404

    data = request.get_json(force=True) or {}
    for field in ('name', 'issuer', 'client_id', 'metadata_url', 'redirect_url', 'default_role'):
        if field in data:
            setattr(prov, field, data[field])
    if data.get('client_secret'):
        prov.client_secret_encrypted = hashlib.sha256(data['client_secret'].encode()).hexdigest()
    if 'auto_provision' in data:
        prov.auto_provision = data['auto_provision']
    if 'is_active' in data:
        prov.is_active = data['is_active']
    if 'certificate' in data:
        prov.certificate = data['certificate']

    prov.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(_serialize_sso(prov))


@phase63.route('/sso/providers/<provider_id>', methods=['DELETE'])
@require_auth
def delete_sso_provider(provider_id):
    """Remove an SSO provider."""
    prov = SSOProvider.query.get(provider_id)
    if not prov:
        return jsonify({"error": "SSO provider not found"}), 404
    db.session.delete(prov)
    db.session.commit()
    return jsonify({"message": "SSO provider deleted"}), 200


@phase63.route('/sso/providers/<provider_id>/metadata', methods=['POST'])
@require_auth
def refresh_sso_metadata(provider_id):
    """Refresh SAML metadata XML from the IdP metadata URL."""
    prov = SSOProvider.query.get(provider_id)
    if not prov:
        return jsonify({"error": "SSO provider not found"}), 404
    if prov.protocol != 'saml':
        return jsonify({"error": "Metadata refresh only supported for SAML providers"}), 400
    if not prov.metadata_url:
        return jsonify({"error": "No metadata URL configured"}), 400

    # In production, this would fetch and parse the XML
    prov.metadata_xml = "<EntityDescriptor>placeholder</EntityDescriptor>"
    prov.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"message": "Metadata refreshed", "metadata_url": prov.metadata_url})


@phase63.route('/sso/login/<provider_id>', methods=['GET'])
def initiate_sso_login(provider_id):
    """Initiate SSO login — returns the IdP redirect URL.

    This endpoint is public (no auth required) since unauthenticated users
    need to access it to start the SSO flow.
    """
    prov = SSOProvider.query.get(provider_id)
    if not prov or not prov.is_active:
        return jsonify({"error": "SSO provider not found or inactive"}), 404

    state = secrets.token_urlsafe(32)

    if prov.protocol == 'oidc':
        redirect = (
            f"{prov.issuer}/authorize"
            f"?client_id={prov.client_id}"
            f"&response_type=code"
            f"&scope=openid+email+profile"
            f"&redirect_uri={prov.redirect_url}"
            f"&state={state}"
        )
    else:
        # SAML — redirect to the IdP's SSO endpoint
        redirect = prov.metadata_url or prov.issuer

    return jsonify({
        "redirect_url": redirect,
        "state": state,
        "protocol": prov.protocol,
    })


@phase63.route('/sso/callback', methods=['POST'])
def sso_callback():
    """Handle SSO callback (OIDC code exchange or SAML response).

    For OIDC: exchanges the authorization code for tokens.
    For SAML: validates the SAML response assertion.
    In both cases, auto-provisions users if configured.
    """
    data = request.get_json(force=True) or {}
    provider_id = data.get('provider_id')
    code = data.get('code')
    saml_response = data.get('saml_response')

    if not provider_id:
        return jsonify({"error": "provider_id is required"}), 400

    prov = SSOProvider.query.get(provider_id)
    if not prov or not prov.is_active:
        return jsonify({"error": "SSO provider not found or inactive"}), 404

    if prov.protocol == 'oidc' and not code:
        return jsonify({"error": "code is required for OIDC callback"}), 400
    if prov.protocol == 'saml' and not saml_response:
        return jsonify({"error": "saml_response is required for SAML callback"}), 400

    # In production, this would:
    # OIDC: Exchange code for tokens, decode ID token for user claims
    # SAML: Validate XML signature, parse NameID and attributes
    # Then auto-provision user if prov.auto_provision is True

    return jsonify({
        "message": "SSO callback processed",
        "protocol": prov.protocol,
        "auto_provision": prov.auto_provision,
        "default_role": prov.default_role,
        # In production, this would return a JWT token for the authenticated user
    })
