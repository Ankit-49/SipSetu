"""Email tasks for Celery."""

from celery_app import celery_app
from utils.email import (
    send_email,
    send_interview_reminder,
    send_password_reset_otp,
    send_verification_otp,
)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_password_reset_otp_task(self, to: str, otp: str, name: str = "User"):
    """Send password reset OTP email asynchronously."""
    try:
        return send_password_reset_otp(to, otp, name)
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_verification_otp_task(self, to: str, otp: str, name: str = "User"):
    """Send email verification OTP asynchronously."""
    try:
        return send_verification_otp(to, otp, name)
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_interview_reminder_task(self, to: str, name: str, role: str, job_title: str,
                                  company: str, other_name: str, scheduled_at: str,
                                  duration_minutes: int = 60, meeting_link: str = "",
                                  remaining_hours: float = 24):
    """Send interview reminder email asynchronously."""
    try:
        from datetime import datetime
        scheduled_at_dt = datetime.fromisoformat(scheduled_at)
        return send_interview_reminder(
            to=to,
            name=name,
            role=role,
            job_title=job_title,
            company=company,
            other_name=other_name,
            scheduled_at=scheduled_at_dt,
            duration_minutes=duration_minutes,
            meeting_link=meeting_link,
            remaining_hours=remaining_hours,
        )
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_generic_email_task(self, to: str, subject: str, html_body: str, text_body: str = None):
    """Send generic email asynchronously."""
    try:
        return send_email(to, subject, html_body, text_body)
    except Exception as exc:
        raise self.retry(exc=exc)