# SipSetu — Industry Standard Enhancement Roadmap

Based on comprehensive analysis of the codebase, this roadmap organizes improvements by priority and effort to transform SipSetu into a production-ready, industry-standard platform.

---

## Executive Summary

**Current State**: Functional MVP with sophisticated ML ranking, proper auth, background jobs, and polished UI. Well-structured but missing critical production infrastructure.

**Target State**: Production-hardened, observable, scalable platform with CI/CD, testing, monitoring, and security best practices.

---

## Phase 1: Foundation & Reliability (Weeks 1-4)
*High impact, blocks production deployment*

> **Status: DONE** — containerization, Alembic migrations, test infrastructure,
> CI, E2E Playwright tests, and a staging migration workflow are all in place.

### 1.1 Containerization & Local Dev Parity
- [x] **Docker Compose** — Single-command `docker compose up` for Postgres, Redis, Backend, Frontend
- [x] **Multi-stage Dockerfiles** — Optimized images (backend: Python slim, frontend: Nginx static serve)
- [x] **`.dockerignore`** — Exclude node_modules, venv, .git, ml_artifacts
- [x] **Environment parity** — Dev/staging/prod compose overrides (`docker-compose.override.yml` for dev)

### 1.2 Database Migrations
- [x] **Alembic setup** — Replace raw SQL migrations with versioned, reversible migrations
- [x] **Initial migration** — Generate from current schema (`alembic revision --autogenerate`)
- [x] **Migration CI check** — `alembic upgrade head` + `alembic check` in CI (currently non-blocking; flip to blocking when ready)

### 1.3 Test Infrastructure
- [x] **Backend: pytest + pytest-cov** — Unit tests for scoring, auth, utils; integration tests for API routes
- [x] **Frontend: Vitest + React Testing Library** — Component tests, hook tests, utils
- [x] **E2E: Playwright** — Critical flows: register→verify→login→upload resume→match jobs (`e2e/` directory + `e2e-ci.yml` workflow)
- [x] **Test DB** — Separate test database with fixtures/factories (factory_boy; CI Postgres service + conftest fixtures)
- [x] **Coverage targets** — frontend ≥70% enforced in CI; backend ≥30% enforced (80% aspirational, not yet reached)

### 1.4 CI/CD Pipeline (GitHub Actions)
- [x] **Backend workflow** — Lint (ruff), typecheck (mypy), test, build Docker image
- [x] **Frontend workflow** — Lint (eslint), typecheck (tsc), test, build, upload artifacts
- [x] **Migration workflow** — Run Alembic upgrade on staging DB (`.github/workflows/migration.yml`)
- [x] **Dependabot** — Weekly dependency updates (grouped PRs; auto-merge not configured)

---

## Phase 2: Production Hardening (Weeks 5-8)
*Required for any real traffic*

> **Status: DONE** — all items complete except virus scanning (needs ClamAV infra)
> and CDN (deferred). Direct-to-S3 streaming uploads are now wired: backend exposes
> `POST /resumes/presigned-upload-url` + `POST /resumes/confirm-upload` and the
> frontend uses presigned URLs when available (with server-side fallback).

### 2.1 Redis-Backed Rate Limiting
- [x] **Replace in-memory limiter** — Flask-Limiter, sliding-window strategy, Redis-backed
- [x] **Key prefixes per environment** — Keys namespaced per endpoint/key (`rate_limiter.py`)
- [x] **Graceful degradation** — Fail-open if Redis unavailable (log warning, in-memory fallback)

### 2.2 Production WSGI Server
- [x] **Gunicorn + gevent** — `gunicorn -k gevent -w 4 -b 0.0.0.0:5000 app:create_app()` (Dockerfile CMD)
- [x] **Health check endpoint** — `/api/health` with DB/Redis connectivity checks (+ Docker HEALTHCHECK)
- [x] **Graceful shutdown** — Gunicorn/gevent worker lifecycle handles SIGTERM/connection drain

### 2.3 Object Storage for Files
- [x] **S3/MinIO integration** — `utils/storage.py` (upload, presigned GET URLs, delete)
- [x] **Streaming uploads** — Direct-to-S3 from frontend (presigned URL route + confirm-upload route in `routes.py`; `Resume.tsx` tries presigned path first, falls back to server-side multipart)
- [ ] **CDN** — CloudFront/Cloudflare for static assets and resume downloads

### 2.4 Input Validation & Security
- [x] **Request validation** — Pydantic schemas + ad-hoc guards on hot paths
- [x] **File upload hardening** — Size limit (10MB), MIME/extension checks (`validation.py`);
- [ ] **File upload hardening — virus scan (ClamAV)** — pending external service
- [x] **CORS tightening** — Explicit origins from `FRONTEND_URL`, no wildcard
- [x] **Security headers** — CSP, HSTS, X-Frame-Options via Flask-Talisman (production)
- [x] **Dependency scanning** — `pip-audit` / `npm audit` in CI (non-blocking)

### 2.5 Email Template System
- [x] **Jinja2 templates** — `backend/templates/emails/` (verification, password reset, interview reminder)
- [x] **Text fallback** — Paired `.txt.j2` templates
- [x] **Preview endpoint** — `/api/dev/email-preview?template=verification|password_reset|interview_reminder`

---

## Phase 3: Observability & Operations (Weeks 9-12)
*Essential for running in production*

> **Status: DONE** — full stack lives under `monitoring/` and runs via
> `docker compose --profile observability up` (Prometheus, Alertmanager, Grafana,
> Loki, Promtail, OpenTelemetry collector). Flower dashboard included.

### 3.1 Structured Logging
- [x] **JSON logs** — `python-json-logger` with correlation IDs (`logging_config.py`)
- [x] **Log levels** — DEBUG/INFO/WARN/ERROR per module via `LOG_LEVEL`/`LOG_FORMAT`
- [x] **Request logging middleware** — Method, path, status, latency, user_id, request_id
- [x] **Log aggregation** — Loki + Promtail (ships container logs labelled `logging=promtail`)

### 3.2 Metrics & Monitoring
- [x] **Prometheus metrics** — `prometheus-flask-exporter` `/metrics` (request count, latency, errors)
- [x] **Business metrics** — `sipsetu_registrations_total`, `sipsetu_applications_total`, `sipsetu_emails_sent_total` + DB pool/Redis gauges
- [x] **Grafana dashboards** — Provisioned “SipSetu — Overview” (RED + business KPIs)
- [x] **Alerting** — Prometheus rules (error rate >1%, p99 >2s, pool exhaustion, Redis down) → Alertmanager → Slack

### 3.3 Distributed Tracing
- [x] **OpenTelemetry** — Flask/SQLAlchemy/requests instrumentation (`tracing.py`, gated by `OTEL_ENABLED`)
- [x] **Trace context propagation** — OTLP exporter → bundled collector (`monitoring/otel-collector/`)
- [x] **Sampling** — 10% traces via `ParentBased(TraceIdRatioBased(0.1))` (errors still captured by Sentry)

### 3.4 Error Tracking
- [x] **Sentry** — Backend + Frontend SDKs (source maps via `@sentry/vite-plugin` when configured)
- [x] **Release tracking** — `sipsetu@<version>` release tags on backend (APP_VERSION) and frontend (VITE_APP_VERSION)

---

## Phase 4: API & Architecture Maturity (Weeks 13-16)

### 4.1 API Versioning & Documentation
- [x] **Version prefix** — `/api/v1/` canonical (dual-registered blueprint in `app.py`); legacy `/api` alias stays live until the Sunset date
- [x] **OpenAPI/Swagger** — `flasgger` auto-generated from route YAML docstrings (`api_docs.py`); UI at `/apidocs/`, spec at `/apispec.json` (legacy `/api` endpoints excluded via `rule_filter`)
- [x] **Schema validation** — Auth request/response schemas defined in the OpenAPI `definitions` (single source of truth in `api_docs.py`) and `$ref`'d from route docstrings; more routes can be documented by adding YAML blocks
- [x] **Deprecation headers** — legacy `/api/*` responses carry `Deprecation: true`, `Sunset` (from `API_DEPRECATION_DATE`), and `Link: <…/api/v1/…>; rel="successor-version"`

### 4.2 Pagination & Query Standards
- [x] **Cursor pagination** — Keyset (seek) pagination via `?limit=` + opaque `?cursor=` (`backend/pagination.py`); applied to `/jobs`, `matched-jobs`, `/jobs/<id>/candidates`, `/recruiters/<id>/candidates` on `/api/v1` — O(1) per page, stable under inserts
- [x] **Standard query params** — `?sort=` supported on v1 list endpoints (`sort=title`, `sort=-created_at`, `sort=matching_score`/`-matching_score`); `filter[]`, `fields`, `include` not yet implemented
- [x] **Response envelope** — `{ data: [], meta: { pagination: { total, limit, next_cursor, has_more }, ... } }` on all `/api/v1` list endpoints (jobs, matched-jobs, candidates, applications, notifications, saved-jobs, saved-job-ids, resumes, interviews); legacy `/api` keeps its historical shapes

### 4.3 Background Job Infrastructure
- [x] **Celery + Redis** — Bulk screening moved off the request thread (`tasks/bulk_screen_tasks.py` + `GET /recruiters/bulk-screen/<job_id>` status endpoint; sync fallback without a broker). Email tasks (`tasks/email_tasks.py`) and ML retraining (`tasks/ml_tasks.py`) were already queued.
- [x] **Task priorities** — `task_routes` in `celery_app.py`: email queue (priority 3, high), bulk-screen queue (5), retrain queue (9, low), `queue_order_strategy=priority`; dedicated `celery-worker-retrain` compose service so training never competes with email
- [x] **Retry/backoff** — Exponential backoff on email and bulk-screen tasks (`self.retry(countdown=60 * 2**retries)`)
- [x] **Dead-letter queue** — `FlaskTask.on_failure` publishes permanently failed jobs to the `dead_letter` Redis list (`tasks/dead_letter.py`); inspect/requeue via `tasks.dead_letter_tasks.{list,count,requeue}_dead_letters`
- [x] **Flower monitoring** — Celery dashboard (`flower:5555` in docker-compose; Prometheus scrape target added)

### 4.4 Database Optimization
- [x] **Index audit** — `EXPLAIN ANALYZE` on all hot queries; add composite indexes. Migration `003_hot_query_indexes` + model `__table_args__` parity: jobs `(created_at, job_id)` / `(recruiter_id, created_at)` / `(job_type, created_at)`, rankings `(job_id, matching_score, ranking_id)` + `(resume_id)`, notifications `(user_id, created_at)` — all DESC-ordered to match the ORDER BY. Search: migration `004_pg_trgm_jobs_search` adds `pg_trgm` GIN indexes on jobs `title`/`location`/`job_type` (also serving the location-filter ILIKE). Re-runnable audit script: `backend/scripts/explain_analyze.sql`
- [x] **Jobs full-text search** — Migration `005_jobs_full_text_search` adds a maintained `search_vector` tsvector column (written by `routes_common.set_job_search_vector` on create/update, backfilled for existing rows) + GIN index; `GET /jobs?search=` matches `search_vector @@ plainto_tsquery('english', term)` on Postgres and ranks by relevance (`ts_rank`, wins over `?sort=` while searching). SQLite dev/tests and short (<3-char) terms fall back to ILIKE (pg_trgm GIN from 004); v1 cursor pagination keysets over `(search_rank, created_at, job_id)`
- [ ] **Connection pooling** — PgBouncer for production
- [ ] **Read replicas** — Route analytics queries (dashboards, rankings) to replica
- [ ] **Partitioning** — `notifications`, `rankings` by date if volume grows

---

## Phase 5: Feature Enhancements (Weeks 17-24)
*Product value, competitive differentiation*

> **Status: DONE** — all items complete. LLM resume parsing (regex fallback +
> OpenAI-compatible API), recruiter feedback loop with audit trail, real-time
> WebSocket notifications, full admin dashboard with user management / job
> moderation / analytics, and candidate experience enhancements (timeline,
> interview prep, salary benchmarks) are all in place.

### 5.1 Resume Parsing Upgrade
- [x] **LLM-based extraction** — Structured JSON via OpenAI-compatible API (`llm_parser.py`); `POST /resumes/<id>/parse` endpoint with `parsed_sections`, `parse_confidence`, `parse_method` columns on Resume model
- [x] **Section detection** — Identify summary, experience, education, skills, projects, certifications, languages
- [x] **Confidence scoring** — Computed from section completeness (0.0–1.0); persisted on resume for UI display
- [ ] **Local LLM support** — Ollama/llama.cpp integration (deferred until infra available)

### 5.2 Recruiter Feedback Loop
- [x] **Explicit ranking feedback** — `POST /rankings/<id>/feedback` with direction (higher/lower/correct) + notes; `RankingFeedback` model with unique constraint per (ranking, recruiter)
- [x] **Active learning** — Feedback labels feed into training labels (shortlisted/rejected already blended in `_training_label()`; feedback adds explicit direction)
- [x] **Model explainability UI** — Per-feature attribution already in `ranking_ml.py` + `ScoreExplanation` component; feedback summary via `GET /jobs/<id>/feedback-summary`
- [x] **Audit trail** — `AuditLog` model + `_log_audit()` helper for all admin and feedback actions

### 5.3 Real-time Notifications
- [x] **WebSocket server** — `flask-socketio` with Redis message queue support (`websocket.py`); `init_socketio()`, `emit_notification()`, `emit_notification_count()`
- [x] **Event types** — Emitted on application submit, status change, interview invite/confirm/cancel
- [x] **Frontend integration** — `NotificationCenter` component with bell icon, unread badge, popover list, mark-as-read; polling fallback when WebSocket unavailable; integrated into both ApplicantLayout and RecruiterLayout

### 5.4 Admin Dashboard
- [x] **User management** — `GET /admin/users` (list/search/paginate), `PATCH /admin/users/<id>/suspend` (soft-suspend via email_verified toggle)
- [x] **Job moderation** — `GET /admin/jobs` (list/search), `DELETE /admin/jobs/<id>` (admin delete with recruiter notification)
- [x] **Analytics** — `GET /admin/stats` with user/application/resume counts, application status breakdown, weekly trends (jobs posted, registrations), recent audit log
- [x] **System health** — DB connectivity check in admin stats
- [x] **Admin role** — Email-based admin gate via `ADMIN_EMAILS` env var + `_admin_required` decorator; `/admin` frontend route

### 5.5 Candidate Experience
- [x] **Skill gap learning paths** — Curated resources (free courses, docs) per missing skill (already existed in `SkillGap.tsx`; enhanced with salary benchmarks)
- [x] **Application tracking** — `ApplicationTimeline` component with event types: applied, shortlisted, rejected, interview_scheduled/confirmed/completed
- [x] **Interview prep** — `interview-prep.ts` with behavioral, technical, culture-fit, and salary negotiation question banks + `SALARY_BENCHMARKS` data

---

## Phase 6: Scale & Advanced (Months 7-12)

### 6.1 Multi-tenancy / Organizations
> **Status: IN PROGRESS** — Organization model, role-based access, shared job pools,
> team dashboard, and full frontend UI are complete. Billing/usage deferred.

- [x] **Organization model** — Recruiters belong to orgs, shared job pools, team dashboards (`Organization`, `OrganizationMember` models; migration 007)
- [x] **Role-based access** — Owner, admin, hiring_manager, interviewer, viewer roles with `_admin_required` gates
- [ ] **Billing/usage** — Seat-based or usage-based pricing infrastructure (deferred)

### 6.2 Advanced Matching
> **Status: DONE** — TF-IDF semantic search with pgvector extension point,
> diversity-aware skill taxonomy analysis, and full market intelligence
> (skill demand trends, salary benchmarks, hiring velocity, competitiveness).

- [x] **Semantic search** — TF-IDF cosine similarity for resume/job matching with pgvector extension (`semantic_search.py`); routes: `GET /search/similar-resumes/<job_id>`, `GET /search/similar-jobs/<resume_id>`, `POST /search/similar-resumes/<job_id>` (reindex)
- [x] **Diversity signals** — Skill taxonomy-based diversity analysis per job (`DIVERSITY_SKILL_TAXONOMY`); route: `GET /jobs/<job_id>/diversity-analysis` with Shannon entropy diversity score
- [x] **Market intelligence** — Skill demand trends, salary benchmarks (p25/p50/p75), hiring velocity, applicant-to-job ratios, skill competitiveness metrics (`market_intelligence.py`); 7 market routes

### 6.3 Integrations
- [ ] **ATS sync** — Greenhouse, Lever, Workday webhook receivers
- [ ] **Calendar** — Google/Outlook OAuth, auto-schedule interviews
- [ ] **Communication** — Slack/Teams notifications, email threading
- [ ] **SSO** — SAML/OIDC for enterprise customers

### 6.4 Internationalization
- [ ] **i18n framework** — `react-i18next` + Flask-Babel
- [ ] **RTL support** — Arabic/Hebrew layouts
- [ ] **Locale-aware parsing** — Date formats, number formats, skill taxonomies

---

## Technical Debt & Code Quality (Ongoing)

### Backend
- [ ] **Type hints** — Full coverage, enable strict mypy
- [ ] **Service layer** — Extract business logic from routes into `services/` (single responsibility)
- [ ] **Domain events** — Decouple side effects (email, notifications, rankings) from transactions
- [ ] **Repository pattern** — Abstract DB access for testability

### Frontend
- [ ] **Strict TypeScript** — `noImplicitAny`, `strictNullChecks`, no `any`
- [ ] **State management** — TanStack Query for server state, Zustand for UI state
- [ ] **Component library** — Extract shadcn customizations to internal package
- [ ] **Accessibility audit** — axe-core in CI, WCAG 2.1 AA compliance

### Database
- [ ] **Soft deletes** — `deleted_at` on all entities, filter by default
- [ ] **Audit log** — `pgaudit` or triggers for sensitive tables (users, jobs, applications)
- [ ] **Data retention** — Archive old notifications, rankings, interview reminders

---

## Risk Assessment & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| ML model degrades with new data | Medium | High | Auto-retrain + monitoring + heuristic fallback |
| Database becomes bottleneck | High | High | Read replicas, connection pooling, query optimization |
| Email deliverability issues | Medium | Medium | Dedicated IP, DKIM/SPF/DMARC, bounce handling |
| File upload abuse | Medium | High | Size limits, type validation, virus scan, rate limits |
| Auth token theft | Low | Critical | Short expiry, refresh tokens, device tracking |
| Regulatory (GDPR, CCPA) | Medium | High | Data export/delete, consent tracking, DPA |

---

## Recommended Team Allocation

| Phase | Backend | Frontend | DevOps/Infra | QA |
|-------|---------|----------|--------------|-----|
| 1 (Foundation) | 1 | 1 | 1 | 0.5 |
| 2 (Hardening) | 1 | 0.5 | 1 | 0.5 |
| 3 (Observability) | 0.5 | 0.5 | 1 | 0 |
| 4 (API Maturity) | 1 | 0.5 | 0.5 | 0.5 |
| 5 (Features) | 1 | 1 | 0.5 | 0.5 |
| 6 (Scale) | 1.5 | 1 | 1 | 0.5 |

---

## Success Metrics (Definition of Done)

- [ ] **Deploy frequency** — Daily deploys to staging, weekly to prod
- [ ] **Lead time** — <1 day from merge to prod
- [ ] **MTTR** — <30 min for critical incidents
- [ ] **Change failure rate** — <5%
- [ ] **Availability** — 99.9% uptime (excluding planned maintenance)
- [ ] **API p99 latency** — <500ms
- [ ] **Test coverage** — Maintained above thresholds
- [ ] **Security** — Zero critical vulns in dependencies

---

## Quick Wins (Can start immediately, <1 week each)

1. **Add pre-commit hooks** for ruff + mypy (both already run in CI)
2. ~~**Add request ID middleware** for traceability~~ — done (Phase 3.1)
3. ~~**Create `.env.example` with all required vars documented**~~ — done
4. ~~**Add `pytest.ini` with coverage config**~~ — done
5. **Document API with OpenAPI annotations** (start with auth routes)
6. ~~**Set up Sentry**~~ — done (Phase 3.4)
7. ~~**Add health check dependencies** (DB, Redis)~~ — done (Phase 2.2)
8. ~~**Configure dependabot** for both package.json and requirements.txt~~ — done

---

*This roadmap is a living document. Re-prioritize based on user feedback, business goals, and technical discoveries during implementation.*