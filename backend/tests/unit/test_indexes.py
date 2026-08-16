"""Unit tests for Phase 4.4 hot-query composite indexes.

The model-level ``__table_args__`` indexes are created by ``db.create_all()``
in dev/sqlite and must mirror the Postgres indexes added by alembic migration
003 (``003_hot_query_indexes``) — these tests pin that parity.
"""


def _indexes(app, table):
    from models import db

    with app.app_context():
        inspector = __import__("sqlalchemy").inspect(db.engine)
        return {i["name"]: i["column_names"] for i in inspector.get_indexes(table)}


def test_jobs_hot_query_indexes(app):
    names = _indexes(app, "jobs")
    assert "ix_jobs_created_at_id" in names      # default list + keyset pagination
    assert "ix_jobs_recruiter_created" in names  # recruiter's job list/dashboard
    assert "ix_jobs_type_created" in names       # job-type browsing


def test_rankings_hot_query_indexes(app):
    names = _indexes(app, "rankings")
    assert "ix_rankings_job_score" in names  # candidate lists (job_id, score desc, id)
    assert "ix_rankings_resume" in names     # ranking regeneration by resume


def test_notifications_hot_query_index(app):
    names = _indexes(app, "notifications")
    assert "ix_notifications_user_created" in names  # per-user feed, newest first


def test_index_columns_match_query_patterns(app):
    job_idx = _indexes(app, "jobs")
    assert job_idx["ix_jobs_created_at_id"] == ["created_at", "job_id"]
    assert job_idx["ix_jobs_recruiter_created"] == ["recruiter_id", "created_at"]

    ranking_idx = _indexes(app, "rankings")
    assert ranking_idx["ix_rankings_job_score"] == ["job_id", "matching_score", "ranking_id"]

    notif_idx = _indexes(app, "notifications")
    assert notif_idx["ix_notifications_user_created"] == ["user_id", "created_at"]
