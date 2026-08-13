"""Celery task for asynchronous bulk resume screening (Phase 4.3).

The ``POST /recruiters/bulk-screen`` endpoint persists the uploaded PDFs to
a shared temp directory, records a ``BulkScreenJob`` row, and enqueues
``process_bulk_screen_job``. The worker parses each PDF and updates the job's
progress checkpoint after every file so the status endpoint can report live
progress. When no broker is configured the API falls back to calling
``run_bulk_screen_job`` inline (identical results, synchronous response).
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import uuid

from celery_app import celery_app
from routes_common import bulk_screen_job_dir

logger = logging.getLogger(__name__)


def run_bulk_screen_job(job_id: str) -> dict:
    """Process a queued ``BulkScreenJob`` and persist results.

    Safe to call directly (synchronous fallback from the API, which runs
    inside the request app context) or from the Celery worker (which wraps
    it in the Flask app context). Returns a small status dict.
    """
    from models import BulkScreenJob, db

    try:
        job = BulkScreenJob.query.get(uuid.UUID(str(job_id)))
    except (ValueError, AttributeError, TypeError):
        job = None
    if not job:
        return {"status": "failed", "error": "Job not found"}

    if job.status in ("completed", "failed"):
        return {"status": job.status, "error": job.error}

    from routes_common import screen_resume_file

    job.status = "running"
    job.error = None
    job.processed_files = 0
    job.results = None
    db.session.commit()

    job_skills = json.loads(job.job_skills or "[]")
    job_title = job.job_title or ""
    job_desc = job.job_desc or ""
    files = json.loads(job.file_paths or "[]")
    results = []

    try:
        for index, entry in enumerate(files, start=1):
            path = entry.get("path")
            filename = entry.get("filename") or os.path.basename(path or "resume.pdf")
            try:
                with open(path, "rb") as fh:
                    file_bytes = fh.read()
                results.append(screen_resume_file(
                    file_bytes,
                    filename,
                    job_skills,
                    job_title,
                    job_desc,
                    job.target_experience_years,
                    job.job_experience_level,
                ))
            except Exception as e:
                results.append({
                    "filename": filename, "candidate_name": filename,
                    "match_score": 0.0, "error": f"Error reading file: {e!s}",
                })
            # Progress checkpoint — lets the status endpoint report live progress.
            job.processed_files = index
            db.session.commit()

        results.sort(
            key=lambda x: (x.get("skills_score", 0), x.get("experience_years") or -1,
                           x.get("experience_score", 0), x.get("content_score", 0),
                           x.get("match_score", 0)),
            reverse=True,
        )

        job.results = json.dumps(results)
        job.status = "completed"
        db.session.commit()

        # Temp files are no longer needed once results are persisted.
        shutil.rmtree(bulk_screen_job_dir(job_id), ignore_errors=True)
        return {"status": "completed", "total": len(results)}
    except Exception:
        db.session.rollback()
        raise


def mark_bulk_screen_failed(job_id: str, message) -> None:
    """Persist a terminal failure on the job (used after retries are exhausted)
    and drop the temp PDFs so they don't accumulate."""
    from models import BulkScreenJob, db

    try:
        job = BulkScreenJob.query.get(uuid.UUID(str(job_id)))
    except (ValueError, AttributeError, TypeError):
        job = None
    if job and job.status != "completed":
        job.status = "failed"
        job.error = str(message)[:2000]
        db.session.commit()
    shutil.rmtree(bulk_screen_job_dir(job_id), ignore_errors=True)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def process_bulk_screen_job(self, job_id: str) -> dict:
    """Celery entrypoint for bulk resume screening with exponential backoff."""
    try:
        return run_bulk_screen_job(job_id)
    except Exception as exc:
        if self.request.retries >= self.max_retries:
            mark_bulk_screen_failed(job_id, exc)
            raise
        raise self.retry(exc=exc, countdown=min(60 * (2 ** self.request.retries), 600))
