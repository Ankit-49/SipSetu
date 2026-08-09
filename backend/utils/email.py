"""Email sending utility for SipSetu.

Uses SMTP when configured (via .env), otherwise falls back to logging
the email content to the console for local development.
"""

import logging
import os
import smtplib
import sys
from datetime import datetime
from email.message import EmailMessage

logger = logging.getLogger(__name__)


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


def send_email(
    to: str,
    subject: str,
    html_body: str,
    text_body: str | None = None,
) -> bool:
    """Send an email. Falls back to console logging in development."""
    config = _smtp_config()

    if not config:
        # Dev fallback — print to stderr so it's visible in the terminal
        print("\n" + "=" * 60, file=sys.stderr)
        print(f"📧 DEV EMAIL TO: {to}", file=sys.stderr)
        print(f"   SUBJECT: {subject}", file=sys.stderr)
        print(f"   BODY:\n{html_body}", file=sys.stderr)
        print("=" * 60 + "\n", file=sys.stderr)
        sys.stderr.flush()
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
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        return False


def send_password_reset_otp(to: str, otp: str, name: str = "User") -> bool:
    """Send a password reset email with a 6-digit OTP code."""
    subject = "Your SipSetu password reset code"
    html = f"""\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; margin: 0; padding: 0;">
  <table width="100%" cellpadding="0" cellspacing="0" style="padding: 32px 16px;">
    <tr>
      <td align="center">
        <table width="480" cellpadding="0" cellspacing="0" style="background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.08);">
          <tr>
            <td style="background: #1E3A5F; padding: 32px 24px; text-align: center;">
              <h1 style="color: #ffffff; font-size: 24px; margin: 0; letter-spacing: -0.5px;">SipSetu</h1>
            </td>
          </tr>
          <tr>
            <td style="padding: 32px 24px;">
              <h2 style="color: #1E3A5F; font-size: 20px; margin: 0 0 8px;">Password reset request</h2>
              <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 24px;">
                Hi {name}, we received a request to reset your SipSetu password. Use the code below to verify your identity. This code expires in 10 minutes.
              </p>
              <table cellpadding="0" cellspacing="0" style="margin: 0 auto 24px;">
                <tr>
                  <td style="background: #f1f5f9; border-radius: 12px; padding: 24px 40px; letter-spacing: 12px; text-align: center;">
                    <span style="font-size: 36px; font-weight: 800; color: #1E3A5F; font-family: 'Courier New', monospace;">{otp}</span>
                  </td>
                </tr>
              </table>
              <p style="color: #64748b; font-size: 13px; line-height: 1.5; margin: 0;">
                Enter this code on the password reset page to confirm your identity and set a new password.
              </p>
            </td>
          </tr>
          <tr>
            <td style="background: #f1f5f9; padding: 16px 24px; text-align: center;">
              <p style="color: #94a3b8; font-size: 12px; margin: 0;">
                If you didn't request this, you can safely ignore this email.<br>
                &copy; {datetime.now().year} SipSetu
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
    text = f"""\
Hi {name},

We received a request to reset your SipSetu password. Your verification code is:

{otp}

This code expires in 10 minutes. Enter it on the password reset page to set a new password.

If you didn't request this, you can safely ignore this email.
"""
    return send_email(to, subject, html, text)


def send_verification_otp(to: str, otp: str, name: str = "User") -> bool:
    """Send an email verification OTP code."""
    subject = "Your SipSetu email verification code"
    html = f"""\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; margin: 0; padding: 0;">
  <table width="100%" cellpadding="0" cellspacing="0" style="padding: 32px 16px;">
    <tr>
      <td align="center">
        <table width="480" cellpadding="0" cellspacing="0" style="background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.08);">
          <tr>
            <td style="background: #1E3A5F; padding: 32px 24px; text-align: center;">
              <h1 style="color: #ffffff; font-size: 24px; margin: 0; letter-spacing: -0.5px;">SipSetu</h1>
            </td>
          </tr>
          <tr>
            <td style="padding: 32px 24px;">
              <h2 style="color: #1E3A5F; font-size: 20px; margin: 0 0 8px;">Verify your email address</h2>
              <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 24px;">
                Hi {name}, thanks for creating your SipSetu account! Please use the code below to verify your email address. This code expires in 10 minutes.
              </p>
              <table cellpadding="0" cellspacing="0" style="margin: 0 auto 24px;">
                <tr>
                  <td style="background: #f1f5f9; border-radius: 12px; padding: 24px 40px; letter-spacing: 12px; text-align: center;">
                    <span style="font-size: 36px; font-weight: 800; color: #1E3A5F; font-family: 'Courier New', monospace;">{otp}</span>
                  </td>
                </tr>
              </table>
              <p style="color: #64748b; font-size: 13px; line-height: 1.5; margin: 0;">
                Enter this code on the verification page to confirm your email address and unlock all features.
              </p>
            </td>
          </tr>
          <tr>
            <td style="background: #f1f5f9; padding: 16px 24px; text-align: center;">
              <p style="color: #94a3b8; font-size: 12px; margin: 0;">
                If you didn't create this account, you can safely ignore this email.<br>
                &copy; {datetime.now().year} SipSetu
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
    text = f"""\
Hi {name},

Thanks for creating your SipSetu account! Your email verification code is:

{otp}

This code expires in 10 minutes. Enter it on the verification page to confirm your email address.

If you didn't create this account, you can safely ignore this email.
"""
    return send_email(to, subject, html, text)


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

    link_button = ""
    if meeting_link:
        link_button = (
            f'<table cellpadding="0" cellspacing="0" style="margin: 0 auto 24px;">'
            "<tr><td>"
            f'<a href="{meeting_link}" style="background: #F97316; color: #ffffff; text-decoration: none; '
            'padding: 12px 28px; border-radius: 10px; font-size: 15px; font-weight: 600; display: inline-block;">'
            "Join the interview</a></td></tr></table>"
        )

    html = f"""\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; margin: 0; padding: 0;">
  <table width="100%" cellpadding="0" cellspacing="0" style="padding: 32px 16px;">
    <tr>
      <td align="center">
        <table width="480" cellpadding="0" cellspacing="0" style="background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.08);">
          <tr>
            <td style="background: #1E3A5F; padding: 32px 24px; text-align: center;">
              <h1 style="color: #ffffff; font-size: 24px; margin: 0; letter-spacing: -0.5px;">SipSetu</h1>
            </td>
          </tr>
          <tr>
            <td style="padding: 32px 24px;">
              <h2 style="color: #1E3A5F; font-size: 20px; margin: 0 0 8px;">⏰ Interview reminder</h2>
              <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 24px;">
                {greeting}
              </p>
              <table cellpadding="0" cellspacing="0" style="background: #f8fafc; border-radius: 12px; padding: 20px 24px; width: 100%; margin-bottom: 24px;">
                <tr>
                  <td style="font-size: 14px; color: #64748b; padding: 4px 0;">{schedule_line}</td>
                </tr>
              </table>
              {link_button}
              <p style="color: #64748b; font-size: 13px; line-height: 1.5; margin: 0;">
                {cta}
              </p>
            </td>
          </tr>
          <tr>
            <td style="background: #f1f5f9; padding: 16px 24px; text-align: center;">
              <p style="color: #94a3b8; font-size: 12px; margin: 0;">
                You're receiving this because you have an interview scheduled on SipSetu.<br>
                &copy; {datetime.now().year} SipSetu
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
    text = f"""\
Hi {name},

This is a reminder about your interview {time_label}:

  Role: {job_title}
  When: {scheduled_at.strftime('%A, %B %d at %I:%M %p')}
  Duration: {duration_minutes} minutes
  Meeting link: {meeting_link or 'will be shared by the recruiter'}

{cta}
"""
    return send_email(to, subject, html, text)
