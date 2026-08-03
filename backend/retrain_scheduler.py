"""Background scheduler that auto-retrains the ML ranking model.

Two triggers, checked on a poll loop:

1. **Nightly window** — once the UTC clock passes NIGHTLY_HOUR_UTC and
   at least a day has passed since the last successful training, the
   model is retrained so it absorbs any rankings/feedback collected
   during the day.

2. **New recruiter feedback** — when the number of shortlisted /
   rejected applications grows by at least MIN_FEEDBACK_DELTA since the
   last sweep, the model is retrained sooner. Those statuses are exactly
   what the training labels use to teach the model recruiter preferences.

All attempts are rate-limited to at most one per hour, so a burst of
feedback can't trigger a tight retrain loop. State (last attempt, last
successful training, feedback count) is persisted to a small JSON file
inside `ml_artifacts/` (gitignored) so the trigger logic survives
restarts.

The thread is a daemon with its own app context, matching the interview
reminder scheduler, so it works with `python app.py` and most WSGI
servers without extra infrastructure.
"""

import json
import logging
import threading
import time
from datetime import datetime, timedelta

from models import db, JobApplication
from ranking_ml import MODEL_DIR, train_ranking_model

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 300  # check every 5 minutes
NIGHTLY_HOUR_UTC = 3
MIN_FEEDBACK_DELTA = 1       # retrain when this many new feedback rows appear
ATTEMPT_COOLDOWN = timedelta(hours=1)   # max one attempt per hour
NIGHTLY_COOLDOWN = timedelta(days=1)    # nightly retrains at most once a day
STATE_PATH = MODEL_DIR / "retrain_state.json"

FEEDBACK_STATUSES = ("shortlisted", "rejected")

_started = False
_lock = threading.Lock()


def start_retrain_scheduler(app):
    """Start the retrain thread exactly once per process."""
    global _started
    with _lock:
        if _started:
            return
        _started = True

    thread = threading.Thread(
        target=_run_loop,
        args=(app,),
        daemon=True,
        name="ranking-model-retrain-scheduler",
    )
    thread.start()
    logger.info(
        "Ranking model retrain scheduler started (polling every %ss)",
        POLL_INTERVAL_SECONDS,
    )


def _run_loop(app):
    while True:
        try:
            with app.app_context():
                _maybe_retrain()
        except Exception:
            logger.exception("Ranking model retrain sweep failed")
        time.sleep(POLL_INTERVAL_SECONDS)


# ---------------------------------------------------------------------------
# State persistence
# ---------------------------------------------------------------------------


def _load_state() -> dict:
    try:
        if STATE_PATH.exists():
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        logger.exception("Failed to read retrain state")
    return {}


def _save_state(state: dict) -> None:
    try:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception:
        logger.exception("Failed to write retrain state")


# ---------------------------------------------------------------------------
# Trigger logic
# ---------------------------------------------------------------------------


def _feedback_count() -> int:
    """Number of applications with recruiter feedback (shortlisted/rejected)."""
    return (
        db.session.query(db.func.count(JobApplication.application_id))
        .filter(JobApplication.status.in_(FEEDBACK_STATUSES))
        .scalar()
        or 0
    )


def _parse_iso(value: str | None):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _should_retrain(state: dict) -> str | None:
    """Return a human-readable reason if a retrain is warranted, else None."""
    now = datetime.utcnow()

    # Rate-limit all attempts to one per hour.
    last_attempt = _parse_iso(state.get("last_attempt_at"))
    if last_attempt and now - last_attempt < ATTEMPT_COOLDOWN:
        return None

    last_trained = _parse_iso(state.get("last_trained_at"))

    # Never trained successfully → try once (no-ops until enough rows exist).
    if last_trained is None:
        return "no model trained yet"

    # Feedback trigger: new shortlist/reject rows since the last sweep.
    last_feedback = int(state.get("last_feedback_count", -1))
    current_feedback = _feedback_count()
    if last_feedback >= 0 and (current_feedback - last_feedback) >= MIN_FEEDBACK_DELTA:
        return f"{current_feedback - last_feedback} new recruiter feedback rows"

    # Nightly trigger: past the window hour and at least a day since training.
    if now.hour >= NIGHTLY_HOUR_UTC and (now - last_trained) >= NIGHTLY_COOLDOWN:
        return "nightly window reached"

    return None


def _maybe_retrain() -> None:
    state = _load_state()
    reason = _should_retrain(state)
    if not reason:
        return

    result = train_ranking_model()
    trained = bool(result.get("trained"))
    logger.info(
        "Auto-retrain attempt (%s): trained=%s rows=%s",
        reason,
        trained,
        result.get("row_count"),
    )

    state["last_attempt_at"] = datetime.utcnow().isoformat()
    state["last_feedback_count"] = _feedback_count()
    if trained:
        state["last_trained_at"] = datetime.utcnow().isoformat()
        state["last_result"] = {
            "trained": True,
            "row_count": result.get("row_count"),
            "job_count": result.get("job_count"),
            "alpha": result.get("alpha"),
            "metrics": result.get("metrics"),
        }
    else:
        state["last_result"] = {"trained": False, "message": result.get("message")}
    _save_state(state)
