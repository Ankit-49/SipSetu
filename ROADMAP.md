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
> and CI are all in place. Remaining: E2E Playwright coverage and a
> deploy/migration workflow for staging (see "Deployment" in the summary).

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
- [ ] **E2E: Playwright** — Critical flows: register→verify→login→upload resume→match jobs
- [x] **Test DB** — Separate test database with fixtures/factories (factory_boy; CI Postgres service + conftest fixtures)
- [x] **Coverage targets** — frontend ≥70% enforced in CI; backend ≥30% enforced (80% aspirational, not yet reached)

### 1.4 CI/CD Pipeline (GitHub Actions)
- [x] **Backend workflow** — Lint (ruff), typecheck (mypy), test, build Docker image
- [x] **Frontend workflow** — Lint (eslint), typecheck (tsc), test, build, upload artifacts
- [ ] **Migration workflow** — Run Alembic upgrade on staging DB
- [x] **Dependabot** — Weekly dependency updates (grouped PRs; auto-merge not configured)

---

## Phase 2: Production Hardening (Weeks 5-8)
*Required for any real traffic*

> **Status: DONE** — all items complete except virus scanning (needs ClamAV infra)
> and direct-to-S3 streaming uploads / CDN (deferred, `storage.py` already exposes
> presigned upload URLs).

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
- [ ] **Streaming uploads** — Direct-to-S3 from frontend (helper `get_presigned_upload_url` exists; wire into routes)
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
> Loki, Promtail, OpenTelemetry collector).

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
- [ ] **Task priorities** — High (email), Low (retrain) via `task_routes` queues
- [x] **Retry/backoff** — Exponential backoff on email and bulk-screen tasks (`self.retry(countdown=60 * 2**retries)`)
- [ ] **Dead-letter queue** — Failed jobs land in a DLQ for inspection/requeue
- [ ] **Flower monitoring** — Celery dashboard

### 4.4 Database Optimization
- [ ] **Index audit** — `EXPLAIN ANALYZE` on all hot queries; add composite indexes
- [ ] **Connection pooling** — PgBouncer for production
- [ ] **Read replicas** — Route analytics queries (dashboards, rankings) to replica
- [ ] **Partitioning** — `notifications`, `rankings` by date if volume grows

---

## Phase 5: Feature Enhancements (Weeks 17-24)
*Product value, competitive differentiation*

### 5.1 Resume Parsing Upgrade
- [ ] **LLM-based extraction** — Structured JSON (skills, experience, education, projects) via OpenAI/Claude or local LLM
- [ ] **Section detection** — Identify summary, experience, education, skills, projects
- [ ] **Confidence scoring** — Flag low-confidence extractions for review

### 5.2 Recruiter Feedback Loop
- [ ] **Explicit ranking feedback** — "This candidate should be higher/lower"
- [ ] **Active learning** — Prioritize uncertain predictions for human review
- [ ] **Model explainability UI** — Show feature contributions per candidate (already in `ranking_ml.py`)

### 5.3 Real-time Notifications
- [ ] **WebSocket server** — `socket.io` or native WebSockets with Redis pub/sub
- [ ] **Event types** — New match, application status change, interview scheduled, message
- [ ] **Frontend integration** — Toast + notification center with unread count

### 5.4 Admin Dashboard
- [ ] **User management** — List, search, suspend, impersonate
- [ ] **Job moderation** — Flag/remove inappropriate postings
- [ ] **Analytics** — Funnel (visit → register → apply → hire), match quality, model performance
- [ ] **System health** — DB size, queue depths, error rates, storage usage

### 5.5 Candidate Experience
- [ ] **Skill gap learning paths** — Curated resources (free courses, docs) per missing skill
- [ ] **Application tracking** — Timeline view with recruiter actions
- [ ] **Interview prep** — Company-specific questions, salary benchmarks

---

## Phase 6: Scale & Advanced (Months 7-12)

### 6.1 Multi-tenancy / Organizations
- [ ] **Organization model** — Recruiters belong to orgs, shared job pools, team dashboards
- [ ] **Role-based access** — Admin, hiring manager, interviewer, viewer
- [ ] **Billing/usage** — Seat-based or usage-based pricing infrastructure

### 6.2 Advanced Matching
- [ ] **Semantic search** — Vector embeddings (pgvector) for resume/job similarity beyond keywords
- [ ] **Diversity signals** — Optional demographic-aware ranking (compliance mode)
- [ ] **Market intelligence** — Skill demand trends, salary benchmarks by region

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