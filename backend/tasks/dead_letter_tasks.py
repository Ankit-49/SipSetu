"""Operational tasks for the dead-letter queue (Phase 4.3).

These run on a normal worker (default queue) and give operators a way to
inspect and recover failed jobs:

    celery -A celery_app call tasks.dead_letter_tasks.count_dead_letters
    celery -A celery_app call tasks.dead_letter_tasks.list_dead_letters --args='[10]'
    celery -A celery_app call tasks.dead_letter_tasks.requeue_dead_letters --args='[100]'
"""

from celery_app import celery_app
from tasks.dead_letter import (
    count_dead_letters,
    list_dead_letters,
    requeue_dead_letters,
)


@celery_app.task(name="tasks.dead_letter_tasks.count_dead_letters")
def count_dead_letters_task():
    """Return the number of records currently in the dead-letter queue."""
    return count_dead_letters()


@celery_app.task(name="tasks.dead_letter_tasks.list_dead_letters")
def list_dead_letters_task(limit: int = 100):
    """Return the current dead-letter queue contents (newest first)."""
    return list_dead_letters(limit=limit)


@celery_app.task(name="tasks.dead_letter_tasks.requeue_dead_letters")
def requeue_dead_letters_task(limit: int = 100):
    """Re-enqueue up to ``limit`` failed jobs from the dead-letter queue."""
    return requeue_dead_letters(celery_app, limit=limit)
