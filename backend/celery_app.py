"""Celery configuration for SipSetu background tasks."""

import os
from celery import Celery
from celery.schedules import crontab

from config import settings

# Import create_app to create Flask app context
from app import create_app

# Create Flask app context for Celery
flask_app = create_app()
flask_app = create_app()

celery_app = Celery(
    "sipsetu",
    broker=settings.CELERY_BROKER_URL or settings.REDIS_URL or "redis://localhost:6379/0",
    backend=settings.CELERY_RESULT_BACKEND or settings.REDIS_URL or "redis://localhost:6379/0",
    include=[
        "tasks.email_tasks",
        "tasks.ml_tasks",
        "tasks.reminder_tasks",
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

# Flask app context for tasks
class FlaskTask(celery_app.Task):
    def __call__(self, *args, **kwargs):
        with flask_app.app_context():
            return self.run(*args, **kwargs)

celery_app.Task = FlaskTask

if __name__ == "__main__":
    celery_app.start()