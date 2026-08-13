"""Email sending utility for SipSetu.

Renders HTML/plain-text bodies from Jinja2 templates in
``backend/templates/emails/``, then sends via SMTP when configured (via
.env), otherwise falls back to logging the email content to the console
for local development.
"""

import logging
import os
import smtplib
import sys
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


def render_email(template_name: str, **context) -> tuple[str, str]:
    """Render an email template to (html, text)."""
    context.setdefault("year", datetime.now().year)
    html = _env.get_template(f"{template_name}.html.j2").render(**context)
    text = _env.get_template(f"{template_name}.txt.j2").render(**context)
    return html, text


def _smtp_config() -> dict | None:
    """Read SMTP settings from environment."""
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


def send_email(
    to: str,
    subject: str,
    html_body: str,
    text_body: str | None = None,
    kind: str = "generic",
) -> bool:
    """Send an email. Falls back to console logging in development."""
    config = _smtp_config()

    if not config:
        # Dev fallback — print to stderr so it's visible in the terminal
        print("\n" + "=" * 60, file=sys.stderr)
        print(f"EMAIL TO: {to}", file=sys.stderr)
        print(f"   SUBJECT: {subject}", file=sys.stderr)
        print(f"   BODY:\n{html_body}", file=sys.stderr)
        print("=" * 60 + "\n", file=sys.stderr)
        sys.stderr.flush()
        _increment_email_metric(kind)
        return True

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = config["from_addr"]
    msg["To"] = to
    msg.set_content(text_body or html_body)
    msg.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP(config["host"], config["port"]) as server:
            if config["use_tls"]:
                server.starttls()
            if config["user"] and config["password"]:
                server.login(config["user"], config["password"])
            server.send_message(msg)
        logger.info(f"Email sent to {to}: {subject}")
        _increment_email_metric(kind)
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        return False


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
