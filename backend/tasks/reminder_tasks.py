"""Reminder tasks for Celery."""

from celery_app import celery_app
from tasks.email_tasks import send_interview_reminder_task


@celery_app.task(bind=True)
def send_due_reminders(self):
    """Send due interview reminders - called by Celery Beat every minute."""
    try:
        from models import db, Interview
        from datetime import datetime, timedelta

        now = datetime.utcnow()
        horizon = now + timedelta(hours=24, minutes=30)

        upcoming = Interview.query.filter(
            Interview.status.in_(['pending', 'confirmed']),
            Interview.scheduled_at <= horizon,
            Interview.scheduled_at > now,
        ).all()

        sent_count = 0
        for interview in upcoming:
            remaining_hours = (interview.scheduled_at - now).total_seconds() / 3600
            sent_tokens = {t for t in (interview.reminders_sent or "").split(",") if t}

            for hours_before, label in [(24, "24h"), (1, "1h")]:
                if remaining_hours > hours_before:
                    continue

                for party in ("applicant", "recruiter"):
                    token = f"{hours_before}h_{party}"
                    if token in sent_tokens:
                        continue

                    if party == "applicant":
                        recipient = interview.applicant
                        name = recipient.name or recipient.email
                        other_name = interview.recruiter.name or interview.recruiter.email
                        role = "applicant"
                    else:
                        recipient = interview.recruiter
                        name = recipient.name or recipient.email
                        other_name = interview.applicant.name or interview.applicant.email
                        role = "recruiter"

                    job_title = interview.job.title if interview.job else "the position"
                    company = (interview.recruiter.company
                               or interview.recruiter.name
                               or "the company") if interview.recruiter else "the company"

                    # Queue the email task
                    send_interview_reminder_task.delay(
                        to=recipient.email,
                        name=name,
                        role=role,
                        job_title=job_title,
                        company=company,
                        other_name=other_name,
                        scheduled_at=interview.scheduled_at.isoformat(),
                        duration_minutes=interview.duration_minutes or 60,
                        meeting_link=interview.meeting_link or "",
                        remaining_hours=remaining_hours,
                    )
                    sent_tokens.add(token)
                    sent_count += 1

            # Update reminders_sent
            interview.reminders_sent = ",".join(sorted(sent_tokens))

        if sent_count > 0:
            db.session.commit()

        return {"sent": sent_count, "interviews_processed": len(upcoming)}
    except Exception as exc:
        db.session.rollback()
        raise self.retry(exc=exc, countdown=60)