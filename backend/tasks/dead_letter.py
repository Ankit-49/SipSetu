"""Dead-letter queue for permanently failed Celery tasks (Phase 4.3).

When a task exhausts its retries (or fails without retry logic), the task
base class (``FlaskTask.on_failure`` in ``celery_app.py``) publishes a
record to a plain Redis list named ``dead_letter``. No worker consumes that
queue — the records are JSON payloads describing the failed task, and are
meant to be inspected and requeued by an operator:

    celery -A celery_app call tasks.dead_letter_tasks.list_dead_letters
    celery -A celery_app call tasks.dead_letter_tasks.requeue_dead_letters

Requires a configured ``REDIS_URL``; without one the helpers degrade to
no-ops so dev/test environments are unaffected.
"""

import json
import logging
from datetime import datetime

from config import settings

DEAD_LETTER_QUEUE = "dead_letter"

logger = logging.getLogger(__name__)


def get_redis_client():
    """Return a Redis client for the DLQ, or None when Redis is not configured."""
    url = settings.REDIS_URL
    if not url:
        return None
    import redis

    return redis.from_url(url, socket_connect_timeout=2, socket_timeout=2)


def publish_dead_letter(app, task_name, task_id, args, kwargs, exc, traceback_text=None):
    """Record a permanently failed task in the dead-letter queue.

    ``app`` is the Celery app (used only for context; the write goes straight
    to Redis). Returns True when the record was persisted.
    """
    client = get_redis_client()
    if client is None:
        logger.warning(
            "No Redis configured — skipping dead-letter publish for %s", task_name
        )
        return False

    payload = {
        "task": task_name,
        "task_id": task_id,
        "args": list(args or ()),
        "kwargs": dict(kwargs or {}),
        "error": str(exc)[:2000],
        "traceback": (traceback_text or "")[-4000:],
        "failed_at": datetime.utcnow().isoformat() + "Z",
    }
    try:
        client.lpush(DEAD_LETTER_QUEUE, json.dumps(payload))
        return True
    except Exception:
        logger.exception("Failed to publish dead letter for %s", task_name)
        return False


def list_dead_letters(limit=100):
    """Return the current dead-letter queue contents (newest first)."""
    client = get_redis_client()
    if client is None:
        return []
    try:
        raw_items = client.lrange(DEAD_LETTER_QUEUE, 0, limit - 1)
    except Exception:
        logger.exception("Failed to list dead letters")
        return []
    result = []
    for raw in raw_items:
        try:
            result.append(json.loads(raw))
        except (TypeError, ValueError):
            continue
    return result


def count_dead_letters():
    """Return the number of records in the dead-letter queue."""
    client = get_redis_client()
    if client is None:
        return 0
    try:
        return client.llen(DEAD_LETTER_QUEUE)
    except Exception:
        logger.exception("Failed to count dead letters")
        return 0


def requeue_dead_letters(app, limit=100):
    """Re-enqueue up to ``limit`` failed jobs from the dead-letter queue.

    Records are consumed FIFO and re-dispatched with ``app.send_task`` using
    their original task name, args, kwargs, and task id (so tracing stays
    intact). Returns a summary dict.
    """
    client = get_redis_client()
    if client is None:
        return {"requeued": 0, "remaining": 0, "error": "No Redis configured"}

    requeued = 0
    remaining = 0
    for _ in range(limit):
        raw = client.rpop(DEAD_LETTER_QUEUE)
        if raw is None:
            break
        try:
            payload = json.loads(raw)
            app.send_task(
                payload["task"],
                args=payload.get("args") or [],
                kwargs=payload.get("kwargs") or {},
                task_id=payload.get("task_id"),
            )
            requeued += 1
        except Exception:
            # Never lose a record on a bad payload — push it back and stop.
            client.lpush(DEAD_LETTER_QUEUE, raw)
            logger.exception("Failed to requeue dead letter, returned it to the DLQ")
            break
    try:
        remaining = client.llen(DEAD_LETTER_QUEUE)
    except Exception:
        remaining = 0
    return {"requeued": requeued, "remaining": remaining}
