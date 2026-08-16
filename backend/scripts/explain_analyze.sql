-- ============================================================================
-- Phase 4.4 — Hot-query EXPLAIN ANALYZE audit
-- ============================================================================
-- Run against the staging/production Postgres to verify the composite indexes
-- added by migration 003 (003_hot_query_indexes) are actually used.
--
--   psql "$DATABASE_URL" -f backend/scripts/explain_analyze.sql
--
-- For each query: look at the plan. With the new index you should see an
-- "Index Scan" (or "Index Only Scan") with the index name in the plan and
-- "Index Cond" showing the filter. If you see "Seq Scan", the planner judged
-- the table too small to bother, or the predicate doesn't match the index
-- prefix — adjust and re-check.
--
-- Substitute real values for the :params (they are psql variables so you can
-- run this file as-is with psql; use \set or replace the placeholders).

-- ---------------------------------------------------------------------------
-- 1. GET /jobs — public list, default sort (ORDER BY created_at DESC)
--    Expect: Index Scan using ix_jobs_created_at_id (backward)
-- ---------------------------------------------------------------------------
EXPLAIN ANALYZE
SELECT job_id, title, created_at
FROM jobs
ORDER BY created_at DESC, job_id DESC
LIMIT 20;

-- ---------------------------------------------------------------------------
-- 2. GET /jobs?v1 cursor page (keyset seek on created_at + job_id)
--    Expect: Index Scan using ix_jobs_created_at_id with an Index Cond
-- ---------------------------------------------------------------------------
EXPLAIN ANALYZE
SELECT job_id, title, created_at
FROM jobs
WHERE (created_at, job_id) < (:created_at, :job_id)
ORDER BY created_at DESC, job_id DESC
LIMIT 20;

-- ---------------------------------------------------------------------------
-- 3. GET /jobs?recruiter_id=X (Manage Jobs / Bulk Screening)
--    Expect: Index Scan using ix_jobs_recruiter_created
-- ---------------------------------------------------------------------------
EXPLAIN ANALYZE
SELECT job_id, title, created_at
FROM jobs
WHERE recruiter_id = :recruiter_id
ORDER BY created_at DESC
LIMIT 100;

-- ---------------------------------------------------------------------------
-- 4. GET /jobs?job_type=full-time (browse by type)
--    Expect: Index Scan using ix_jobs_type_created
-- ---------------------------------------------------------------------------
EXPLAIN ANALYZE
SELECT job_id, title, created_at
FROM jobs
WHERE job_type = 'full-time'
ORDER BY created_at DESC
LIMIT 20;

-- ---------------------------------------------------------------------------
-- 5. GET /jobs/:id/candidates and GET /recruiters/:id/candidates
--    Expect: Index Scan using ix_rankings_job_score with an Index Cond on
--    job_id and matching_score (>=) — and no explicit Sort step.
-- ---------------------------------------------------------------------------
EXPLAIN ANALYZE
SELECT ranking_id, resume_id, matching_score, candidate_rank
FROM rankings
WHERE job_id = :job_id AND matching_score >= 0
ORDER BY matching_score DESC, ranking_id DESC
LIMIT 50;

-- ---------------------------------------------------------------------------
-- 6. Ranking regeneration after a resume change (WHERE resume_id IN ...)
--    Expect: Index Scan using ix_rankings_resume
-- ---------------------------------------------------------------------------
EXPLAIN ANALYZE
SELECT ranking_id, job_id, matching_score
FROM rankings
WHERE resume_id = :resume_id;

-- ---------------------------------------------------------------------------
-- 7. GET /notifications/:user_id (feed, newest first, capped at 50)
--    Expect: Index Scan using ix_notifications_user_created
-- ---------------------------------------------------------------------------
EXPLAIN ANALYZE
SELECT notification_id, title, is_read, created_at
FROM notifications
WHERE user_id = :user_id
ORDER BY created_at DESC
LIMIT 50;

-- ---------------------------------------------------------------------------
-- 8. Unread badge / mark-all-read (WHERE user_id = ? AND is_read = false)
--    Covered by the ix_notifications_user_created prefix (user_id) — the
--    per-user segment is small enough that the is_read filter is cheap.
-- ---------------------------------------------------------------------------
EXPLAIN ANALYZE
SELECT count(*)
FROM notifications
WHERE user_id = :user_id AND is_read = false;

-- ============================================================================
-- Known non-indexable paths (noted in the audit):
--   * GET /jobs?search=... uses ILIKE '%term%' — a btree index cannot help a
--     leading-wildcard LIKE. If this becomes hot, add pg_trgm GIN indexes or
--     full-text search (tsvector).
--   * The v1 matched-jobs endpoint scores every job in Python (Job.query.all()
--     + in-memory ranking) — index help is limited until scoring moves to SQL
--     or a precomputed ranking table is queried instead.
-- ============================================================================
