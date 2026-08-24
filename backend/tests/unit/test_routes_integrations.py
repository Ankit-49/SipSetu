"""Unit tests for Phase 6.3 integration routes.

Covers:
  6.3a — ATS Sync: create, list, get, delete connections; webhook receiver; sync
  6.3b — Calendar: OAuth tokens CRUD; calendar events CRUD + sync
  6.3c — Communication: Slack/Teams channels CRUD + test notification
  6.3d — SSO: SAML/OIDC providers CRUD + metadata refresh, login initiation, callback
"""
from __future__ import annotations

import hashlib
import hmac
import json
from uuid import uuid4

import pytest
from werkzeug.security import generate_password_hash

from auth_middleware import create_token
from models import (
    Applicant,
    ATSConnection,
    AuditLog,
    BulkScreenJob,
    CalendarEvent,
    CommunicationChannel,
    Job,
    Notification,
    OAuthToken,
    Organization,
    OrganizationMember,
    Ranking,
    RankingFeedback,
    Recruiter,
    Resume,
    Skill,
    SSOProvider,
    User,
    WebhookSubscription,
    db,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

RECRUITER_EMAIL = "integ_recruiter@example.com"
APPLICANT_EMAIL = "integ_applicant@example.com"
ADMIN_EMAIL = "admin_integ@example.com"


@pytest.fixture(autouse=True)
def _clean(app):
    """Ensure every test starts and ends with a clean slate."""
    with app.app_context():
        _delete_all()
        yield
        _delete_all()


def _delete_all():
    """Remove all integration-related rows."""
    from models import Interview
    AuditLog.query.delete(synchronize_session=False)
    RankingFeedback.query.delete(synchronize_session=False)
    Ranking.query.delete(synchronize_session=False)
    Notification.query.delete(synchronize_session=False)
    BulkScreenJob.query.delete(synchronize_session=False)
    Resume.query.delete(synchronize_session=False)
    CalendarEvent.query.delete(synchronize_session=False)
    OAuthToken.query.delete(synchronize_session=False)
    CommunicationChannel.query.delete(synchronize_session=False)
    SSOProvider.query.delete(synchronize_session=False)
    WebhookSubscription.query.delete(synchronize_session=False)
    ATSConnection.query.delete(synchronize_session=False)
    Job.query.delete(synchronize_session=False)
    Skill.query.delete(synchronize_session=False)
    Interview.query.delete(synchronize_session=False)
    OrganizationMember.query.delete(synchronize_session=False)
    Organization.query.delete(synchronize_session=False)
    for email in [RECRUITER_EMAIL, APPLICANT_EMAIL, ADMIN_EMAIL]:
        user = User.query.filter_by(email=email).first()
        if user:
            db.session.delete(user)
    db.session.commit()


@pytest.fixture()
def test_recruiter(app):
    """Create a test recruiter."""
    with app.app_context():
        uid = uuid4()
        r = Recruiter(
            user_id=uid,
            email=RECRUITER_EMAIL,
            name="Integ Recruiter",
            password_hash=generate_password_hash("password123"),
            role="recruiter",
            email_verified=True,
            company="Integ Corp",
        )
        db.session.add(r)
        db.session.commit()
        return type("RD", (), {"user_id": uid, "role": "recruiter"})()


@pytest.fixture()
def recruiter_headers(test_recruiter, app):
    with app.app_context():
        token = create_token(str(test_recruiter.user_id), test_recruiter.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def test_applicant(app):
    """Create a test applicant."""
    with app.app_context():
        uid = uuid4()
        a = Applicant(
            user_id=uid,
            email=APPLICANT_EMAIL,
            name="Integ Applicant",
            password_hash=generate_password_hash("password123"),
            role="applicant",
            email_verified=True,
        )
        db.session.add(a)
        db.session.commit()
        return type("AD", (), {"user_id": uid, "role": "applicant"})()


@pytest.fixture()
def applicant_headers(test_applicant, app):
    with app.app_context():
        token = create_token(str(test_applicant.user_id), test_applicant.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def test_admin_user(app):
    """Create an admin user."""
    with app.app_context():
        uid = uuid4()
        a = Recruiter(
            user_id=uid,
            email=ADMIN_EMAIL,
            name="Admin Integ",
            password_hash=generate_password_hash("password123"),
            role="recruiter",
            email_verified=True,
        )
        db.session.add(a)
        db.session.commit()
        return type("AdminData", (), {"user_id": uid, "role": "recruiter"})()


@pytest.fixture()
def admin_headers(test_admin_user, app):
    with app.app_context():
        token = create_token(str(test_admin_user.user_id), test_admin_user.role)
    return {"Authorization": f"Bearer {token}"}


# ─── 6.3a — ATS Sync Tests ────────────────────────────────────────────────


class TestATSConnections:
    def test_create_ats_connection(self, client, recruiter_headers, app):
        with app.app_context():
            resp = client.post(
                "/api/v1/ats/connections",
                json={"provider": "greenhouse", "api_key": "test-key-123", "ats_org_id": "gh-123"},
                headers=recruiter_headers,
            )
            assert resp.status_code == 201
            data = resp.get_json()
            assert data["provider"] == "greenhouse"
            assert data["ats_org_id"] == "gh-123"
            assert data["sync_status"] == "idle"
            assert data["is_active"] is True
            assert "connection_id" in data

    def test_create_ats_connection_invalid_provider(self, client, recruiter_headers, app):
        with app.app_context():
            resp = client.post(
                "/api/v1/ats/connections",
                json={"provider": "invalid", "api_key": "key"},
                headers=recruiter_headers,
            )
            assert resp.status_code == 400

    def test_create_ats_connection_no_key(self, client, recruiter_headers, app):
        with app.app_context():
            resp = client.post(
                "/api/v1/ats/connections",
                json={"provider": "lever"},
                headers=recruiter_headers,
            )
            assert resp.status_code == 400

    def test_list_ats_connections(self, client, recruiter_headers, app):
        with app.app_context():
            # Create two connections
            for prov in ("greenhouse", "lever"):
                client.post(
                    "/api/v1/ats/connections",
                    json={"provider": prov, "api_key": f"key-{prov}"},
                    headers=recruiter_headers,
                )
            resp = client.get("/api/v1/ats/connections", headers=recruiter_headers)
            assert resp.status_code == 200
            data = resp.get_json()
            assert len(data) == 2
            providers = {c["provider"] for c in data}
            assert providers == {"greenhouse", "lever"}

    def test_get_ats_connection(self, client, recruiter_headers, app):
        with app.app_context():
            create_resp = client.post(
                "/api/v1/ats/connections",
                json={"provider": "greenhouse", "api_key": "key"},
                headers=recruiter_headers,
            )
            conn_id = create_resp.get_json()["connection_id"]
            resp = client.get(f"/api/v1/ats/connections/{conn_id}", headers=recruiter_headers)
            assert resp.status_code == 200
            assert resp.get_json()["provider"] == "greenhouse"

    def test_get_ats_connection_not_found(self, client, recruiter_headers, app):
        with app.app_context():
            fake_id = str(uuid4())
            resp = client.get(f"/api/v1/ats/connections/{fake_id}", headers=recruiter_headers)
            assert resp.status_code == 404

    def test_delete_ats_connection(self, client, recruiter_headers, app):
        with app.app_context():
            create_resp = client.post(
                "/api/v1/ats/connections",
                json={"provider": "greenhouse", "api_key": "key"},
                headers=recruiter_headers,
            )
            conn_id = create_resp.get_json()["connection_id"]
            resp = client.delete(f"/api/v1/ats/connections/{conn_id}", headers=recruiter_headers)
            assert resp.status_code == 200
            # Verify deleted
            resp2 = client.get(f"/api/v1/ats/connections/{conn_id}", headers=recruiter_headers)
            assert resp2.status_code == 404

    def test_trigger_ats_sync(self, client, recruiter_headers, app):
        with app.app_context():
            create_resp = client.post(
                "/api/v1/ats/connections",
                json={"provider": "greenhouse", "api_key": "key"},
                headers=recruiter_headers,
            )
            conn_id = create_resp.get_json()["connection_id"]
            resp = client.post(f"/api/v1/ats/connections/{conn_id}/sync", headers=recruiter_headers)
            assert resp.status_code == 200
            assert resp.get_json()["status"] == "syncing"

    def test_webhook_receiver(self, client, recruiter_headers, test_recruiter, app):
        with app.app_context():
            create_resp = client.post(
                "/api/v1/ats/connections",
                json={"provider": "greenhouse", "api_key": "key"},
                headers=recruiter_headers,
            )
            conn_id = create_resp.get_json()["connection_id"]

            # Retrieve the webhook_secret from the DB
            conn = ATSConnection.query.get(conn_id)
            secret = conn.webhook_secret

            # Build the raw payload to compute HMAC
            payload_dict = {"event": "candidate.created", "data": {"id": "123"}}
            payload_bytes = json.dumps(payload_dict, separators=(',', ':')).encode('utf-8')
            sig = 'sha256=' + hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()

            resp = client.post(
                f"/api/v1/ats/webhook/{conn_id}",
                data=payload_bytes,
                content_type='application/json',
                headers={"X-Hub-Signature-256": sig},
            )
            assert resp.status_code == 200
            assert resp.get_json()["event_type"] == "candidate.created"

    def test_webhook_invalid_signature(self, client, recruiter_headers, app):
        with app.app_context():
            create_resp = client.post(
                "/api/v1/ats/connections",
                json={"provider": "greenhouse", "api_key": "key"},
                headers=recruiter_headers,
            )
            conn_id = create_resp.get_json()["connection_id"]

            # Send with bad signature
            resp = client.post(
                f"/api/v1/ats/webhook/{conn_id}",
                json={"event": "candidate.created"},
                headers={"X-Hub-Signature-256": "sha256=bad"},
            )
            assert resp.status_code == 401

    def test_webhook_not_found(self, client, app):
        resp = client.post(
            f"/api/v1/ats/webhook/{uuid4()}",
            json={"event": "test"},
        )
        assert resp.status_code == 404

    def test_list_webhook_subscriptions(self, client, recruiter_headers, app):
        with app.app_context():
            create_resp = client.post(
                "/api/v1/ats/connections",
                json={"provider": "greenhouse", "api_key": "key"},
                headers=recruiter_headers,
            )
            conn_id = create_resp.get_json()["connection_id"]
            # Create subscription
            client.post(
                f"/api/v1/ats/connections/{conn_id}/webhooks",
                json={"event_type": "candidate.created", "target_url": "https://example.com/hook"},
                headers=recruiter_headers,
            )
            resp = client.get(f"/api/v1/ats/connections/{conn_id}/webhooks", headers=recruiter_headers)
            assert resp.status_code == 200
            data = resp.get_json()
            assert len(data) == 1
            assert data[0]["event_type"] == "candidate.created"

    def test_create_webhook_subscription(self, client, recruiter_headers, app):
        with app.app_context():
            create_resp = client.post(
                "/api/v1/ats/connections",
                json={"provider": "greenhouse", "api_key": "key"},
                headers=recruiter_headers,
            )
            conn_id = create_resp.get_json()["connection_id"]
            resp = client.post(
                f"/api/v1/ats/connections/{conn_id}/webhooks",
                json={"event_type": "job.updated", "target_url": "https://example.com/hook2"},
                headers=recruiter_headers,
            )
            assert resp.status_code == 201
            data = resp.get_json()
            assert data["event_type"] == "job.updated"

    def test_create_webhook_missing_fields(self, client, recruiter_headers, app):
        with app.app_context():
            create_resp = client.post(
                "/api/v1/ats/connections",
                json={"provider": "greenhouse", "api_key": "key"},
                headers=recruiter_headers,
            )
            conn_id = create_resp.get_json()["connection_id"]
            resp = client.post(
                f"/api/v1/ats/connections/{conn_id}/webhooks",
                json={"event_type": "job.updated"},  # missing target_url
                headers=recruiter_headers,
            )
            assert resp.status_code == 400


# ─── 6.3b — Calendar Tests ────────────────────────────────────────────────


class TestCalendar:
    def test_create_calendar_token(self, client, recruiter_headers, app):
        with app.app_context():
            resp = client.post(
                "/api/v1/calendar/tokens",
                json={"provider": "google", "access_token": "ya29.test-token", "scopes": "calendar.events"},
                headers=recruiter_headers,
            )
            assert resp.status_code == 201
            data = resp.get_json()
            assert data["provider"] == "google"
            assert data["is_active"] is True

    def test_create_calendar_token_invalid_provider(self, client, recruiter_headers, app):
        with app.app_context():
            resp = client.post(
                "/api/v1/calendar/tokens",
                json={"provider": "apple", "access_token": "tok"},
                headers=recruiter_headers,
            )
            assert resp.status_code == 400

    def test_list_calendar_tokens(self, client, recruiter_headers, app):
        with app.app_context():
            client.post(
                "/api/v1/calendar/tokens",
                json={"provider": "google", "access_token": "tok1"},
                headers=recruiter_headers,
            )
            client.post(
                "/api/v1/calendar/tokens",
                json={"provider": "microsoft", "access_token": "tok2"},
                headers=recruiter_headers,
            )
            resp = client.get("/api/v1/calendar/tokens", headers=recruiter_headers)
            assert resp.status_code == 200
            assert len(resp.get_json()) == 2

    def test_delete_calendar_token(self, client, recruiter_headers, app):
        with app.app_context():
            create_resp = client.post(
                "/api/v1/calendar/tokens",
                json={"provider": "google", "access_token": "tok"},
                headers=recruiter_headers,
            )
            token_id = create_resp.get_json()["token_id"]
            resp = client.delete(f"/api/v1/calendar/tokens/{token_id}", headers=recruiter_headers)
            assert resp.status_code == 200

    def test_create_calendar_event(self, client, recruiter_headers, test_recruiter, app):
        with app.app_context():
            # Create a job, applicant, and interview for the FK constraints
            from datetime import datetime

            from models import Applicant as AppModel
            from models import Interview, Job
            job = Job(title="Test Job", recruiter_id=test_recruiter.user_id)
            db.session.add(job)
            db.session.commit()
            app_uid = uuid4()
            applicant = AppModel(user_id=app_uid, email="cal_app@example.com", name="Cal Applicant",
                                password_hash=generate_password_hash("pass"), role="applicant")
            db.session.add(applicant)
            db.session.commit()
            iv = Interview(
                job_id=job.job_id,
                applicant_id=app_uid,
                recruiter_id=test_recruiter.user_id,
                scheduled_at=datetime.utcnow(),
                status="scheduled",
            )
            db.session.add(iv)
            db.session.commit()

            # Create a token
            token_resp = client.post(
                "/api/v1/calendar/tokens",
                json={"provider": "google", "access_token": "tok"},
                headers=recruiter_headers,
            )
            token_id = token_resp.get_json()["token_id"]

            resp = client.post(
                "/api/v1/calendar/events",
                json={"interview_id": str(iv.interview_id), "token_id": token_id, "provider": "google"},
                headers=recruiter_headers,
            )
            assert resp.status_code == 201
            data = resp.get_json()
            assert data["provider"] == "google"
            assert data["sync_status"] == "pending"

    def test_sync_calendar_event(self, client, recruiter_headers, test_recruiter, app):
        with app.app_context():
            from datetime import datetime

            from models import Applicant as AppModel
            from models import Interview, Job
            job = Job(title="Test Job", recruiter_id=test_recruiter.user_id)
            db.session.add(job)
            db.session.commit()
            app_uid = uuid4()
            applicant = AppModel(user_id=app_uid, email="sync_app@example.com", name="Sync Applicant",
                                password_hash=generate_password_hash("pass"), role="applicant")
            db.session.add(applicant)
            db.session.commit()
            iv = Interview(
                job_id=job.job_id, applicant_id=app_uid,
                recruiter_id=test_recruiter.user_id,
                scheduled_at=datetime.utcnow(), status="scheduled",
            )
            db.session.add(iv)
            db.session.commit()

            token_resp = client.post(
                "/api/v1/calendar/tokens",
                json={"provider": "google", "access_token": "tok"},
                headers=recruiter_headers,
            )
            token_id = token_resp.get_json()["token_id"]

            event_resp = client.post(
                "/api/v1/calendar/events",
                json={"interview_id": str(iv.interview_id), "token_id": token_id},
                headers=recruiter_headers,
            )
            event_id = event_resp.get_json()["event_id"]

            resp = client.put(f"/api/v1/calendar/events/{event_id}/sync", headers=recruiter_headers)
            assert resp.status_code == 200
            assert resp.get_json()["sync_status"] == "synced"

    def test_delete_calendar_event(self, client, recruiter_headers, test_recruiter, app):
        with app.app_context():
            from datetime import datetime

            from models import Applicant as AppModel
            from models import Interview, Job
            job = Job(title="Test Job", recruiter_id=test_recruiter.user_id)
            db.session.add(job)
            db.session.commit()
            app_uid = uuid4()
            applicant = AppModel(user_id=app_uid, email="del_app@example.com", name="Del Applicant",
                                password_hash=generate_password_hash("pass"), role="applicant")
            db.session.add(applicant)
            db.session.commit()
            iv = Interview(
                job_id=job.job_id, applicant_id=app_uid,
                recruiter_id=test_recruiter.user_id,
                scheduled_at=datetime.utcnow(), status="scheduled",
            )
            db.session.add(iv)
            db.session.commit()

            token_resp = client.post(
                "/api/v1/calendar/tokens",
                json={"provider": "microsoft", "access_token": "tok"},
                headers=recruiter_headers,
            )
            token_id = token_resp.get_json()["token_id"]

            event_resp = client.post(
                "/api/v1/calendar/events",
                json={"interview_id": str(iv.interview_id), "token_id": token_id},
                headers=recruiter_headers,
            )
            event_id = event_resp.get_json()["event_id"]
            resp = client.delete(f"/api/v1/calendar/events/{event_id}", headers=recruiter_headers)
            assert resp.status_code == 200

    def test_list_calendar_events(self, client, recruiter_headers, app):
        with app.app_context():
            resp = client.get("/api/v1/calendar/events", headers=recruiter_headers)
            assert resp.status_code == 200
            assert resp.get_json() == []


# ─── 6.3c — Communication Tests ───────────────────────────────────────────


class TestCommunication:
    def test_create_slack_channel(self, client, recruiter_headers, app):
        with app.app_context():
            resp = client.post(
                "/api/v1/channels",
                json={
                    "provider": "slack",
                    "webhook_url": "https://hooks.slack.com/services/T00/B00/xxx",
                    "channel_name": "#hiring",
                },
                headers=recruiter_headers,
            )
            assert resp.status_code == 201
            data = resp.get_json()
            assert data["provider"] == "slack"
            assert data["channel_name"] == "#hiring"

    def test_create_teams_channel(self, client, recruiter_headers, app):
        with app.app_context():
            resp = client.post(
                "/api/v1/channels",
                json={
                    "provider": "teams",
                    "webhook_url": "https://outlook.office.com/webhook/xxx",
                    "channel_name": "Hiring Team",
                },
                headers=recruiter_headers,
            )
            assert resp.status_code == 201

    def test_create_channel_invalid_provider(self, client, recruiter_headers, app):
        with app.app_context():
            resp = client.post(
                "/api/v1/channels",
                json={"provider": "discord", "webhook_url": "https://discord.com/api/xxx"},
                headers=recruiter_headers,
            )
            assert resp.status_code == 400

    def test_list_channels(self, client, recruiter_headers, app):
        with app.app_context():
            client.post(
                "/api/v1/channels",
                json={"provider": "slack", "webhook_url": "https://hooks.slack.com/a"},
                headers=recruiter_headers,
            )
            client.post(
                "/api/v1/channels",
                json={"provider": "teams", "webhook_url": "https://outlook.office.com/b"},
                headers=recruiter_headers,
            )
            resp = client.get("/api/v1/channels", headers=recruiter_headers)
            assert resp.status_code == 200
            assert len(resp.get_json()) == 2

    def test_get_channel(self, client, recruiter_headers, app):
        with app.app_context():
            create_resp = client.post(
                "/api/v1/channels",
                json={"provider": "slack", "webhook_url": "https://hooks.slack.com/a"},
                headers=recruiter_headers,
            )
            ch_id = create_resp.get_json()["channel_id"]
            resp = client.get(f"/api/v1/channels/{ch_id}", headers=recruiter_headers)
            assert resp.status_code == 200
            assert resp.get_json()["provider"] == "slack"

    def test_delete_channel(self, client, recruiter_headers, app):
        with app.app_context():
            create_resp = client.post(
                "/api/v1/channels",
                json={"provider": "slack", "webhook_url": "https://hooks.slack.com/a"},
                headers=recruiter_headers,
            )
            ch_id = create_resp.get_json()["channel_id"]
            resp = client.delete(f"/api/v1/channels/{ch_id}", headers=recruiter_headers)
            assert resp.status_code == 200

    def test_test_channel(self, client, recruiter_headers, app):
        with app.app_context():
            create_resp = client.post(
                "/api/v1/channels",
                json={"provider": "slack", "webhook_url": "https://hooks.slack.com/a"},
                headers=recruiter_headers,
            )
            ch_id = create_resp.get_json()["channel_id"]
            resp = client.post(f"/api/v1/channels/{ch_id}/test", headers=recruiter_headers)
            assert resp.status_code == 200
            assert resp.get_json()["status"] == "sent"

    def test_list_available_events(self, client, recruiter_headers, app):
        resp = client.get("/api/v1/channels/events", headers=recruiter_headers)
        assert resp.status_code == 200
        events = resp.get_json()["events"]
        assert "application.received" in events
        assert "interview.scheduled" in events
        assert len(events) == 10

    def test_no_auth_create_channel(self, client, app):
        resp = client.post(
            "/api/v1/channels",
            json={"provider": "slack", "webhook_url": "https://hooks.slack.com/a"},
        )
        assert resp.status_code == 401


# ─── 6.3d — SSO Tests ──────────────────────────────────────────────────────


class TestSSO:
    def test_create_sso_provider(self, client, admin_headers, app):
        with app.app_context():
            resp = client.post(
                "/api/v1/sso/providers",
                json={
                    "name": "Corporate SSO",
                    "protocol": "oidc",
                    "issuer": "https://login.microsoftonline.com/tenant",
                    "client_id": "app-id-123",
                    "client_secret": "secret-456",
                    "redirect_url": "https://sipsetu.com/sso/callback",
                },
                headers=admin_headers,
            )
            assert resp.status_code == 201
            data = resp.get_json()
            assert data["protocol"] == "oidc"
            assert data["name"] == "Corporate SSO"
            assert data["auto_provision"] is True
            assert data["default_role"] == "viewer"

    def test_create_sso_provider_saml(self, client, admin_headers, app):
        with app.app_context():
            resp = client.post(
                "/api/v1/sso/providers",
                json={
                    "name": "Acme IdP",
                    "protocol": "saml",
                    "issuer": "https://idp.acme.com",
                    "redirect_url": "https://sipsetu.com/sso/saml/callback",
                    "metadata_url": "https://idp.acme.com/metadata",
                },
                headers=admin_headers,
            )
            assert resp.status_code == 201
            assert resp.get_json()["protocol"] == "saml"

    def test_create_sso_missing_fields(self, client, admin_headers, app):
        with app.app_context():
            resp = client.post(
                "/api/v1/sso/providers",
                json={"name": "Bad SSO"},  # missing protocol, issuer, redirect_url
                headers=admin_headers,
            )
            assert resp.status_code == 400

    def test_create_sso_invalid_protocol(self, client, admin_headers, app):
        with app.app_context():
            resp = client.post(
                "/api/v1/sso/providers",
                json={
                    "name": "Bad",
                    "protocol": "ldap",
                    "issuer": "https://ldap.example.com",
                    "redirect_url": "https://sipsetu.com/callback",
                },
                headers=admin_headers,
            )
            assert resp.status_code == 400

    def test_list_sso_providers(self, client, admin_headers, app):
        with app.app_context():
            # Create two providers
            for proto in ("oidc", "saml"):
                client.post(
                    "/api/v1/sso/providers",
                    json={
                        "name": f"SSO {proto}",
                        "protocol": proto,
                        "issuer": f"https://{proto}.example.com",
                        "redirect_url": f"https://sipsetu.com/{proto}/cb",
                    },
                    headers=admin_headers,
                )
            resp = client.get("/api/v1/sso/providers", headers=admin_headers)
            assert resp.status_code == 200
            assert len(resp.get_json()) == 2

    def test_get_sso_provider(self, client, admin_headers, app):
        with app.app_context():
            create_resp = client.post(
                "/api/v1/sso/providers",
                json={
                    "name": "My SSO",
                    "protocol": "oidc",
                    "issuer": "https://auth.example.com",
                    "redirect_url": "https://sipsetu.com/cb",
                },
                headers=admin_headers,
            )
            prov_id = create_resp.get_json()["provider_id"]
            resp = client.get(f"/api/v1/sso/providers/{prov_id}", headers=admin_headers)
            assert resp.status_code == 200
            assert resp.get_json()["name"] == "My SSO"

    def test_update_sso_provider(self, client, admin_headers, app):
        with app.app_context():
            create_resp = client.post(
                "/api/v1/sso/providers",
                json={
                    "name": "Old Name",
                    "protocol": "oidc",
                    "issuer": "https://auth.example.com",
                    "redirect_url": "https://sipsetu.com/cb",
                },
                headers=admin_headers,
            )
            prov_id = create_resp.get_json()["provider_id"]
            resp = client.put(
                f"/api/v1/sso/providers/{prov_id}",
                json={"name": "New Name", "is_active": False},
                headers=admin_headers,
            )
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["name"] == "New Name"
            assert data["is_active"] is False

    def test_delete_sso_provider(self, client, admin_headers, app):
        with app.app_context():
            create_resp = client.post(
                "/api/v1/sso/providers",
                json={
                    "name": "Doomed SSO",
                    "protocol": "oidc",
                    "issuer": "https://auth.example.com",
                    "redirect_url": "https://sipsetu.com/cb",
                },
                headers=admin_headers,
            )
            prov_id = create_resp.get_json()["provider_id"]
            resp = client.delete(f"/api/v1/sso/providers/{prov_id}", headers=admin_headers)
            assert resp.status_code == 200

    def test_refresh_saml_metadata(self, client, admin_headers, app):
        with app.app_context():
            create_resp = client.post(
                "/api/v1/sso/providers",
                json={
                    "name": "SAML IdP",
                    "protocol": "saml",
                    "issuer": "https://idp.example.com",
                    "redirect_url": "https://sipsetu.com/saml/cb",
                    "metadata_url": "https://idp.example.com/metadata.xml",
                },
                headers=admin_headers,
            )
            prov_id = create_resp.get_json()["provider_id"]
            resp = client.post(f"/api/v1/sso/providers/{prov_id}/metadata", headers=admin_headers)
            assert resp.status_code == 200

    def test_refresh_metadata_not_saml(self, client, admin_headers, app):
        with app.app_context():
            create_resp = client.post(
                "/api/v1/sso/providers",
                json={
                    "name": "OIDC Provider",
                    "protocol": "oidc",
                    "issuer": "https://auth.example.com",
                    "redirect_url": "https://sipsetu.com/cb",
                },
                headers=admin_headers,
            )
            prov_id = create_resp.get_json()["provider_id"]
            resp = client.post(f"/api/v1/sso/providers/{prov_id}/metadata", headers=admin_headers)
            assert resp.status_code == 400

    def test_initiate_sso_login_oidc(self, client, admin_headers, app):
        with app.app_context():
            create_resp = client.post(
                "/api/v1/sso/providers",
                json={
                    "name": "OIDC Login",
                    "protocol": "oidc",
                    "issuer": "https://login.example.com",
                    "client_id": "my-client",
                    "redirect_url": "https://sipsetu.com/cb",
                },
                headers=admin_headers,
            )
            prov_id = create_resp.get_json()["provider_id"]
            # Login endpoint is public (no auth required)
            resp = client.get(f"/api/v1/sso/login/{prov_id}")
            assert resp.status_code == 200
            data = resp.get_json()
            assert "redirect_url" in data
            assert data["protocol"] == "oidc"
            assert "state" in data

    def test_initiate_sso_login_not_found(self, client, app):
        resp = client.get(f"/api/v1/sso/login/{uuid4()}")
        assert resp.status_code == 404

    def test_sso_callback_oidc(self, client, admin_headers, app):
        with app.app_context():
            create_resp = client.post(
                "/api/v1/sso/providers",
                json={
                    "name": "Callback SSO",
                    "protocol": "oidc",
                    "issuer": "https://auth.example.com",
                    "client_id": "cid",
                    "redirect_url": "https://sipsetu.com/cb",
                },
                headers=admin_headers,
            )
            prov_id = create_resp.get_json()["provider_id"]
            resp = client.post(
                "/api/v1/sso/callback",
                json={"provider_id": prov_id, "code": "auth-code-123"},
            )
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["protocol"] == "oidc"

    def test_sso_callback_missing_code(self, client, admin_headers, app):
        with app.app_context():
            create_resp = client.post(
                "/api/v1/sso/providers",
                json={
                    "name": "CB SSO",
                    "protocol": "oidc",
                    "issuer": "https://auth.example.com",
                    "redirect_url": "https://sipsetu.com/cb",
                },
                headers=admin_headers,
            )
            prov_id = create_resp.get_json()["provider_id"]
            resp = client.post(
                "/api/v1/sso/callback",
                json={"provider_id": prov_id},
            )
            assert resp.status_code == 400
