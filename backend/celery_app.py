"""Celery configuration for SipSetu background tasks."""

from celery import Celery
from celery.schedules import crontab

from config import settings

celery_app = Celery(
    "sipsetu",
    broker=settings.CELERY_BROKER_URL or settings.REDIS_URL or "redis://localhost:6379/0",
    backend=settings.CELERY_RESULT_BACKEND or settings.REDIS_URL or "redis://localhost:6379/0",
    include=[
        "tasks.email_tasks",
        "tasks.ml_tasks",
        "tasks.reminder_tasks",
        "tasks.bulk_screen_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    result_expires=3600,
    # Fail fast when the broker is unreachable so the API can fall back to
    # processing inline instead of blocking the request thread.
    broker_connection_timeout=3,
    beat_schedule={
        # Nightly model retraining at 3 AM UTC
        "retrain-ranking-model-nightly": {
            "task": "tasks.ml_tasks.retrain_ranking_model",
            "schedule": crontab(hour=3, minute=0),
        },
        # Interview reminders every minute
        "send-interview-reminders": {
            "task": "tasks.reminder_tasks.send_due_reminders",
            "schedule": crontab(minute="*"),
        },
    },
)

# Flask app context for tasks. Created lazily so that importing this module
# from the API process (e.g. to enqueue a task) does not spin up a second
# Flask app. Only the worker actually executes tasks.
_flask_app = None


def get_flask_app():
    """Return the Flask app used to wrap Celery task execution."""
    global _flask_app
    if _flask_app is None:
        from app import create_app

        _flask_app = create_app()
    return _flask_app


class FlaskTask(celery_app.Task):
    def __call__(self, *args, **kwargs):
        with get_flask_app().app_context():
            return self.run(*args, **kwargs)


celery_app.Task = FlaskTask

if __name__ == "__main__":
    celery_app.start()
