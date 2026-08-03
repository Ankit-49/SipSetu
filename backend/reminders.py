"""Background scheduler that emails interview reminders.

Polls the database every minute and sends reminder emails to both the
applicant and the recruiter 24h and 1h before a scheduled interview.

Idempotency is tracked per recipient per window using tokens (e.g.
"1h_applicant", "24h_recruiter") stored in the Interview.reminders_sent
column. Because each recipient is tracked independently, a transient email
failure on one side never causes a duplicate email to the other side.

The thread is a daemon and uses its own app context, so it works with
`python app.py` and most WSGI servers without extra infrastructure.
"""

import logging
import threading
import time
from datetime import datetime, timedelta

from models import db, Interview
from utils.email import send_interview_reminder

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 60
REMINDER_WINDOW = {
    # hours_before -> short label
    24: "24h",
    1: "1h",
}
PARTIES = ("applicant", "recruiter")

_started = False
_lock = threading.Lock()


def start_reminder_scheduler(app):
    """Start the reminder thread exactly once per process."""
    global _started
    with _lock:
        if _started:
            return
        _started = True

    thread = threading.Thread(
        target=_run_loop,
        args=(app,),
        daemon=True,
        name="interview-reminder-scheduler",
    )
    thread.start()
    logger.info("Interview reminder scheduler started (polling every %ss)", POLL_INTERVAL_SECONDS)


def _run_loop(app):
    while True:
        try:
            with app.app_context():
                _send_due_reminders()
        except Exception:
            logger.exception("Interview reminder sweep failed")
        time.sleep(POLL_INTERVAL_SECONDS)


def _reminder_tokens(interview) -> set:
    return {t for t in (interview.reminders_sent or "").split(",") if t}


def _send_due_reminders():
    """Find interviews within the next 24h and send any due reminders."""
    now = datetime.utcnow()
    horizon = now + timedelta(hours=24, minutes=30)

    upcoming = Interview.query.filter(
        Interview.status.in_(['pending', 'confirmed']),
        Interview.scheduled_at <= horizon,
        Interview.scheduled_at > now,
    ).all()

    any_changed = False
    for interview in upcoming:
        remaining_hours = (interview.scheduled_at - now).total_seconds() / 3600
        sent = _reminder_tokens(interview)

        # Walk from the farthest window (24h) to the closest (1h) so a single
        # sweep can send both reminders for interviews just an hour away.
        for hours_before, label in sorted(REMINDER_WINDOW.items(), reverse=True):
            if remaining_hours > hours_before:
                continue
            for party in PARTIES:
                token = f"{hours_before}h_{party}"
                if token in sent:
                    continue
                if _send_reminder(interview, party, label, remaining_hours):
                    sent.add(token)
                    any_changed = True

        merged = ",".join(sorted(sent))
        if merged != (interview.reminders_sent or ""):
            interview.reminders_sent = merged

    if any_changed:
        db.session.commit()


def _send_reminder(interview, party, label, remaining_hours) -> bool:
    """Send one reminder email to a single recipient. True only on success."""
    job = interview.job
    job_title = job.title if job else "the position"
    company = (interview.recruiter.company
               or interview.recruiter.name
               or "the company") if interview.recruiter else "the company"

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

    ok = send_interview_reminder(
        to=recipient.email,
        name=name,
        role=role,
        job_title=job_title,
        company=company,
        other_name=other_name,
        scheduled_at=interview.scheduled_at,
        duration_minutes=interview.duration_minutes or 60,
        meeting_link=interview.meeting_link or "",
        remaining_hours=remaining_hours,
    )
    if ok:
        logger.info(
            "Sent %s-before reminder (%s) for interview %s (%s) to %s",
            label, party, interview.interview_id, job_title, recipient.email,
        )
    return ok
