"""Email sending utility for SipSetu.

Renders HTML/plain-text bodies from Jinja2 templates in
``backend/templates/emails/``, then sends via:
  1. Resend API (HTTPS, works on Render free tier) if RESEND_API_KEY is set
  2. SMTP if SMTP_HOST/SMTP_PORT are set
  3. Falls back to logging the email content for local development
"""

import logging
import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

_TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates" / "emails"

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


RESEND_API = "https://api.resend.com/emails"


def render_email(template_name: str, **context) -> tuple[str, str]:
    """Render an email template to (html, text)."""
    context.setdefault("year", datetime.now().year)
    html = _env.get_template(f"{template_name}.html.j2").render(**context)
    text = _env.get_template(f"{template_name}.txt.j2").render(**context)
    return html, text


_smtp_missing_warned = False


def _smtp_config() -> dict | None:
    """Read SMTP settings from environment."""
    global _smtp_missing_warned
    host = os.environ.get("SMTP_HOST")
    port = os.environ.get("SMTP_PORT")
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    use_tls = os.environ.get("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes")
    from_addr = os.environ.get("SMTP_FROM", "noreply@sipsetu.com")

    if host and port:
        return {
            "host": host,
            "port": int(port),
            "user": user,
            "password": password,
            "use_tls": use_tls,
            "from_addr": from_addr,
        }
    if not _smtp_missing_warned:
        logger.warning(
            "SMTP_HOST and SMTP_PORT are not configured - emails are being "
            "logged to stderr instead of sent. Set SMTP_HOST, SMTP_PORT, "
            "SMTP_USER, and SMTP_PASSWORD in your environment to enable "
            "real email delivery."
        )
        _smtp_missing_warned = True
    return None


def _increment_email_metric(kind: str) -> None:
    """Best-effort Prometheus business metric (no-op when metrics disabled)."""
    try:
        from flask import current_app, has_app_context

        from metrics import increment

        if has_app_context():
            increment(
                current_app._get_current_object(),
                "sipsetu_emails_sent_total",
                "Total emails sent by kind",
                {"kind": kind},
            )
    except Exception:
        # Metrics must never break email delivery.
        pass


def _send_via_resend(to: str, subject: str, html_body: str, text_body: str | None) -> bool:
    """Send email via Resend REST API directly (avoids SDK/gevent recursion)."""
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        return False
    import requests as _requests

    from_addr = os.environ.get("SMTP_FROM", "noreply@sipsetu.com")
    payload = {
        "from": f"SipSetu <{from_addr}>",
        "to": [to],
        "subject": subject,
        "html": html_body,
    }
    if text_body:
        payload["text"] = text_body
    try:
        resp = _requests.post(
            RESEND_API,
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15,
        )
        if resp.ok:
            logger.info(f"Email sent via Resend to {to}: {subject} (id={resp.json().get('id')})")
            return True
        logger.error(
            f"Resend API error {resp.status_code} for {to}: {resp.text[:300]}"
        )
        return False
    except Exception as e:
        logger.error(f"Failed to send email via Resend to {to}: {e}")
        return False


def _send_via_smtp(to: str, subject: str, html_body: str, text_body: str | None) -> bool:
    """Send email via SMTP."""
    config = _smtp_config()
    if not config:
        return False
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = config["from_addr"]
    msg["To"] = to
    msg.set_content(text_body or html_body)
    msg.add_alternative(html_body, subtype="html")
    try:
        with smtplib.SMTP(config["host"], config["port"], timeout=10) as server:
            if config["use_tls"]:
                server.starttls()
            if config["user"] and config["password"]:
                server.login(config["user"], config["password"])
            server.send_message(msg)
        logger.info(f"Email sent via SMTP to {to}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email via SMTP to {to}: {e}")
        return False


def send_email(
    to: str,
    subject: str,
    html_body: str,
    text_body: str | None = None,
    kind: str = "generic",
) -> bool:
    """Send an email. Tries Resend (HTTPS), then SMTP, then dev fallback."""
    resend_api_key = os.environ.get("RESEND_API_KEY", "")
    smtp_host = os.environ.get("SMTP_HOST", "")
    logger.info(
        f"[EMAIL] Attempting to send '{kind}' to {to} | "
        f"RESEND_API_KEY={'set (' + resend_api_key[:6] + '...)' if resend_api_key else 'NOT SET'} | "
        f"SMTP_HOST={smtp_host or 'NOT SET'}"
    )

    # 1. Try Resend API (works on Render free tier)
    if _send_via_resend(to, subject, html_body, text_body):
        _increment_email_metric(kind)
        return True

    # 2. Try SMTP (works locally, blocked on some free-tier hosts)
    if _send_via_smtp(to, subject, html_body, text_body):
        _increment_email_metric(kind)
        return True

    # 3. Dev fallback - log to console
    logger.warning(
        f"[DEV EMAIL - NOT SENT] To: {to} | Subject: {subject} | "
        f"Set RESEND_API_KEY or SMTP_HOST/SMTP_PORT to enable email delivery."
    )
    logger.info(f"[DEV EMAIL BODY]\n{text_body or html_body}")
    _increment_email_metric(kind)
    return True


def send_password_reset_otp(to: str, otp: str, name: str = "User") -> bool:
    """Send a password reset email with a 6-digit OTP code."""
    subject = "Your SipSetu password reset code"
    html, text = render_email("password_reset", otp=otp, name=name)
    return send_email(to, subject, html, text, kind="password_reset")


def send_verification_otp(to: str, otp: str, name: str = "User") -> bool:
    """Send an email verification OTP code."""
    subject = "Your SipSetu email verification code"
    html, text = render_email("verification", otp=otp, name=name)
    return send_email(to, subject, html, text, kind="verification")


def send_interview_reminder(
    to: str,
    name: str,
    role: str,  # 'applicant' or 'recruiter'
    job_title: str,
    company: str,
    other_name: str,
    scheduled_at,
    duration_minutes: int = 60,
    meeting_link: str = "",
    remaining_hours: float = 24,
) -> bool:
    """Send a reminder email for an upcoming interview."""
    when = scheduled_at.strftime("%A, %B %d at %I:%M %p")
    # Label adapts to the real time left, so interviews created inside the
    # 24h window still get an accurate subject line.
    if remaining_hours <= 1.5:
        time_label = "in about an hour"
    elif remaining_hours <= 8:
        time_label = "later today"
    elif remaining_hours <= 26:
        time_label = "tomorrow"
    else:
        time_label = f"in {int(round(remaining_hours))} hours"

    if role == "recruiter":
        subject = f"Interview reminder: {job_title} with {other_name} {time_label}"
        greeting = (
            f"Hi {name}, this is a friendly reminder about your interview with "
            f"<strong>{other_name}</strong> for <strong>{job_title}</strong>."
        )
        schedule_line = (
            f"The interview is scheduled for <strong>{when}</strong> and should last about "
            f"{duration_minutes} minutes."
        )
        cta = "Join the interview on time and review the candidate's resume beforehand."
    else:
        subject = f"Interview reminder: {job_title} at {company} {time_label}"
        greeting = (
            f"Hi {name}, this is a friendly reminder about your upcoming interview for "
            f"<strong>{job_title}</strong> at <strong>{company}</strong>."
        )
        schedule_line = (
            f"The interview is scheduled for <strong>{when}</strong> and should last about "
            f"{duration_minutes} minutes. Your interviewer is {other_name}."
        )
        cta = "Prepare your questions and make sure you can join from a quiet, well-lit space."

    html, text = render_email(
        "interview_reminder",
        greeting=greeting,
        schedule_line=schedule_line,
        cta=cta,
        meeting_link=meeting_link or "",
        time_label=time_label,
        job_title=job_title,
        when=when,
        duration_minutes=duration_minutes,
    )
    return send_email(to, subject, html, text, kind="interview_reminder")
