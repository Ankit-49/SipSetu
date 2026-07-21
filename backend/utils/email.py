"""Email sending utility for SipSetu.

Uses SMTP when configured (via .env), otherwise falls back to logging
the email content to the console for local development.
"""

import os
import smtplib
import logging
from email.message import EmailMessage
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


def _smtp_config() -> Optional[dict]:
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
    text_body: Optional[str] = None,
) -> bool:
    """Send an email. Falls back to console logging in development."""
    config = _smtp_config()

    if not config:
        # Dev fallback — log to console
        logger.info("=" * 60)
        logger.info(f"📧 DEV EMAIL TO: {to}")
        logger.info(f"   SUBJECT: {subject}")
        logger.info(f"   BODY:\n{html_body}")
        logger.info("=" * 60)
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


def send_password_reset_email(to: str, reset_url: str, name: str = "User") -> bool:
    """Send a password reset email with a clickable link."""
    subject = "Reset your SipSetu password"
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
                Hi {name}, we received a request to reset your SipSetu password. Click the button below to set a new one. This link expires in 1 hour.
              </p>
              <table cellpadding="0" cellspacing="0" style="margin: 0 auto 24px;">
                <tr>
                  <td style="background: #F97316; border-radius: 8px; text-align: center;">
                    <a href="{reset_url}" style="display: inline-block; padding: 14px 32px; color: #ffffff; font-size: 15px; font-weight: 600; text-decoration: none; letter-spacing: 0.3px;">Reset Password</a>
                  </td>
                </tr>
              </table>
              <p style="color: #64748b; font-size: 13px; line-height: 1.5; margin: 0 0 4px;">
                Or copy this link into your browser:
              </p>
              <p style="color: #1E3A5F; font-size: 12px; word-break: break-all; margin: 0;">
                {reset_url}
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

We received a request to reset your SipSetu password. Click the link below to set a new one. This link expires in 1 hour.

{reset_url}

If you didn't request this, you can safely ignore this email.
"""
    return send_email(to, subject, html, text)
