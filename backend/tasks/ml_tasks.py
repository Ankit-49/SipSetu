"""ML tasks for Celery."""

from celery_app import celery_app
from ranking_ml import train_ranking_model


@celery_app.task(bind=True, max_retries=1, default_retry_delay=300)
def retrain_ranking_model(self):
    """Retrain the ranking model asynchronously."""
    try:
        result = train_ranking_model()
        return result
    except Exception as exc:
        # Don't retry training failures aggressively - they're often data issues
        raise self.retry(exc=exc, countdown=3600)  # Retry in 1 hour


@celery_app.task(bind=True)
def explain_ranking_task(self, resume_id: str, job_id: str):
    """Generate ranking explanation asynchronously."""
    try:
        from models import Job, Resume
        from ranking_ml import explain_ranking_score

        resume = Resume.query.get(resume_id)
        job = Job.query.get(job_id)

        if not resume or not job:
            return {"error": "Resume or job not found"}

        return explain_ranking_score(resume, job)
    except Exception as exc:
        raise self.retry(exc=exc)