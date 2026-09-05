# SipSetu — Complete Project Documentation

**Tagline:**  No skill left behind.

[![Backend CI](https://github.com/Ankit-49/SipSetu/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/Ankit-49/SipSetu/actions/workflows/backend-ci.yml)
[![Frontend CI](https://github.com/Ankit-49/SipSetu/actions/workflows/frontend-ci.yml/badge.svg)](https://github.com/Ankit-49/SipSetu/actions/workflows/frontend-ci.yml)
[![Codecov](https://codecov.io/gh/Ankit-49/SipSetu/branch/main/graph/badge.svg)](https://codecov.io/gh/Ankit-49/SipSetu)

SipSetu is an AI-powered recruitment platform that bridges job seekers and recruiters. It uses skill-based matching, resume analysis, and intelligent candidate ranking to connect talent with opportunity.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Tech Stack](#2-tech-stack)
3. [Project Structure](#3-project-structure)
4. [Setup & Installation](#4-setup--installation)
5. [Backend Deep Dive](#5-backend-deep-dive)
   - [5.1 App Factory & Config](#51-app-factory--config)
   - [5.2 Database Models](#52-database-models)
   - [5.3 Database Schema (SQL)](#53-database-schema-sql)
   - [5.4 Authentication & Authorization](#54-authentication--authorization)
   - [5.5 API Routes](#55-api-routes)
   - [5.6 Scoring & Ranking Pipeline](#56-scoring--ranking-pipeline)
   - [5.7 Rate Limiting](#57-rate-limiting)
   - [5.8 Email Utilities](#58-email-utilities)
6. [Frontend Deep Dive](#6-frontend-deep-dive)
   - [6.1 Entry Point & Routing](#61-entry-point--routing)
   - [6.2 Auth Context & API Client](#62-auth-context--api-client)
   - [6.3 Pages](#63-pages)
   - [6.4 UI Components](#64-ui-components)
   - [6.5 Styling](#65-styling)
7. [Complete API Reference](#7-complete-api-reference)
8. [Scoring Algorithm](#8-scoring-algorithm)
9. [Rate Limiting Rules](#9-rate-limiting-rules)
10. [Known Limitations](#10-known-limitations)
11. [Future Roadmap](#11-future-roadmap)

---

## 1. Architecture Overview

```mermaid
graph TB
    subgraph Frontend["Frontend &#40;React SPA :5173&#41;"]
        React["React App<br/>Vite + TypeScript"]
        AuthCtx["AuthContext<br/>JWT in localStorage"]
        Axios["Axios Client<br/>Bearer Token Interceptor"]
    end

    subgraph Backend["Backend &#40;Flask API :5000&#41;"]
        Routes["routes.py<br/>Blueprint /api/*"]
        Auth["auth_middleware.py<br/>JWT Validation"]
        RateLimit["rate_limiter.py<br/>Sliding Window"]
        Scoring["routes_common.py<br/>Coverage-based scoring"]
        Email("utils/email.py<br/>SMTP Sender")
    end

    subgraph Database["PostgreSQL"]
        DB["&#40;sipsetu&#41;<br/>15 tables"]
    end

    React --> Axios
    Axios -->|"HTTP + JSON"| Routes
    Routes --> Auth
    Auth --> RateLimit
    Routes --> Scoring
    Routes --> Email
    Routes --> DB
    Scoring --> Model
```

The system follows a standard two-tier architecture:

- **Frontend:** React 18 single-page application built with Vite 6, TypeScript, Tailwind CSS v4, shadcn/ui, and Framer Motion.
- **Backend:** Flask REST API with SQLAlchemy ORM, JWT authentication, and an optional scikit-learn gradient-boosted candidate ranker.
- **Database:** PostgreSQL 15+ with the `uuid-ossp` extension.

Authentication is stateless via JWT tokens stored in `localStorage`. File uploads (PDF resumes) are parsed server-side with PyMuPDF.

---

## 2. Tech Stack

### Backend

| Technology | Version | Purpose |
|---|---|---|
| Python | 3.11+ | Runtime (CI uses 3.11) |
| Flask | 3.0.3 | Web framework |
| Flask-SQLAlchemy | 3.1.1 | ORM |
| Flask-CORS | 4.0.0 | Cross-origin requests |
| SQLAlchemy | 2.0.29 | Database toolkit |
| Alembic | 1.12+ | Versioned database migrations |
| psycopg2-binary | 2.9.9 | PostgreSQL driver |
| PyJWT | 2.8.0 | JWT encode/decode |
| bcrypt | 4.1+ | Password hashing |
| scikit-learn | 1.3.2 | Candidate ranking model + TF-IDF content similarity |
| numpy | 1.24.3 | Numerical operations |
| joblib | 1.3.2 | Model persistence (ml_artifacts) |
| PyMuPDF (fitz) | 1.22.0 | PDF text extraction |
| python-docx | 1.0+ | DOCX text extraction |
| fpdf2 | 2.8+ | PDF generation |
| python-dotenv | 1.2.2 | Environment variables |
| Werkzeug | 3.0.2 | Password hashing / security |
| gunicorn | 21.2+ | Production WSGI server |
| gevent | 23.9+ | Gunicorn async workers |
| redis | 5.0+ | Cache / rate-limit / Celery broker |
| celery | 5.3+ | Background task queue |
| flask-limiter | 3.5+ | Redis-backed rate limiting |
| flask-talisman | 1.1+ | Security headers (production only) |
| pydantic | 2.5+ | Request/response schema validation |
| pydantic-settings | 2.1+ | Typed settings from env |
| boto3 | 1.34+ | S3/MinIO object storage |
| prometheus-flask-exporter | 0.23+ | Prometheus `/metrics` endpoint |
| python-json-logger | 2.0+ | Structured JSON logging |
| pytest | 7.4+ | Unit/integration tests |
| pytest-cov | 4.1+ | Test coverage |

### Frontend

| Technology | Version | Purpose |
|---|---|---|
| React | 18.3.1 | UI framework |
| TypeScript | 5.4+ | Type safety |
| Node.js | 22+ | Runtime (engines requirement) |
| Vite | 6.3.5 | Build tool |
| Tailwind CSS | 4.1.12 | Utility-first CSS |
| React Router | 7.18.2 | Client-side routing |
| motion (Framer Motion) | 12.23.24 | Animations |
| Axios | 1.16.0 | HTTP client |
| shadcn/ui | — | Primitive UI components (Radix-based) |
| Lucide React | 0.487.0 | Icon library |
| Recharts | 2.15.2 | Charts |
| react-hook-form | 7.55.0 | Form management |
| Sonner | 2.0.3 | Toast notifications |
| react-day-picker | 8.10.1 | Date/calendar picker (v8 API) |
| cmdk | 1.1.1 | Command palette |
| input-otp | 1.4.2 | OTP input |
| canvas-confetti | 1.9.4 | Celebration effects |
| Vitest | 1.4+ | Unit/component tests |
| React Testing Library | 14.2+ | Component test utilities |

---

## 3. Project Structure

```
SipSetu/
├── .github/
│   └── workflows/
│       ├── backend-ci.yml             # Backend CI: ruff, mypy, pytest, docker build
│       └── frontend-ci.yml            # Frontend CI: eslint, tsc, vitest, build, docker
│   └── dependabot.yml                 # Weekly dependency updates
│
├── backend/
│   ├── app.py                  # Flask app factory, CORS, logging, rate limiter, Talisman, health
│   ├── config.py               # Typed configuration class (pydantic-settings)
│   ├── models.py               # SQLAlchemy ORM models (15 tables)
│   ├── routes.py               # All API endpoints (auth, jobs, resumes, etc.)
│   ├── routes_common.py        # Shared helpers: scoring, formatting, ranking
│   ├── auth_middleware.py      # JWT creation, decoding, require_auth/role decorators
│   ├── rate_limiter.py         # Redis-backed rate limiter with in-memory fallback
│   ├── ranking_ml.py           # Optional gradient-boosted ML ranking model
│   ├── retrain_scheduler.py    # Background auto-retrain daemon thread
│   ├── reminders.py            # Interview reminder scheduler
│   ├── logging_config.py       # JSON logging setup + request logging middleware
│   ├── tracing.py              # Optional OpenTelemetry setup (OTEL_ENABLED=true)
│   ├── validation.py           # File upload validation (size, MIME, extension)
│   ├── schemas.py              # Pydantic request/response schemas
│   ├── celery_app.py           # Celery application (broker/result backend, task_routes, DLQ hook)
│   ├── tasks/                  # Celery tasks: email (high pri), ML/retrain (low pri), reminders, bulk-screen, dead-letter ops
│   ├── utils/
│   │   ├── email.py            # SMTP email sender (dev fallback to console)
│   │   ├── parser.py           # Resume text parsing helpers
│   │   └── storage.py          # Local / S3 / MinIO file storage abstraction
│   ├── migrations/             # Alembic migration versions
│   ├── tests/                  # pytest: conftest, unit/, integration/
│   ├── alembic.ini             # Alembic config
│   ├── pytest.ini              # pytest + coverage config
│   ├── ruff.toml               # Ruff linter config
│   ├── Dockerfile              # Multi-stage (base → production gunicorn)
│   ├── requirements.txt        # Python dependencies
│   └── .env.example            # Environment variable template
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx            # React entry point
│   │   ├── app/
│   │   │   ├── App.tsx         # Root component with AuthProvider + RouterProvider
│   │   │   ├── routes.tsx      # All route definitions (createBrowserRouter)
│   │   │   └── context/
│   │   │       └── AuthContext.tsx  # Auth state, login/register/logout
│   │   ├── components/
│   │   │   ├── ui/             # shadcn/ui primitives (60+ components)
│   │   │   ├── ApplicantLayout.tsx  # Sidebar + header for applicants
│   │   │   ├── RecruiterLayout.tsx  # Sidebar + header for recruiters
│   │   │   ├── ProtectedRoute.tsx   # Role-based gate
│   │   │   ├── SipSetuLogo.tsx      # Animated brand logo
│   │   │   ├── NotificationBell.tsx # Notification dropdown
│   │   │   └── VisualBackground.tsx # Animated background component
│   │   ├── pages/
│   │   │   ├── LandingPage.tsx       # Public landing with stats, features
│   │   │   ├── LoginPage.tsx         # Login form
│   │   │   ├── RegisterPage.tsx      # Registration form
│   │   │   ├── ForgotPasswordPage.tsx # Password reset flow
│   │   │   ├── VerifyEmailPage.tsx   # OTP verification form
│   │   │   ├── PreviewPage.tsx       # Public preview
│   │   │   ├── not-found.tsx         # 404 page
│   │   │   ├── applicant/
│   │   │   │   ├── Dashboard.tsx     # Stats, top matches, interviews
│   │   │   │   ├── JobMatches.tsx    # Ranked job list with filters
│   │   │   │   ├── MyApplications.tsx # Applied jobs with status
│   │   │   │   ├── Profile.tsx       # Edit profile
│   │   │   │   ├── Resume.tsx        # Upload/manage resume
│   │   │   │   ├── SavedJobs.tsx     # Bookmarked jobs
│   │   │   │   └── SkillGap.tsx      # Missing skills analysis
│   │   │   └── recruiter/
│   │   │       ├── Dashboard.tsx     # Stats, top candidates, interviews
│   │   │       ├── ManageJobs.tsx    # CRUD job postings
│   │   │       ├── PostJob.tsx       # Create job form
│   │   │       ├── Candidates.tsx    # Ranked candidate list
│   │   │       ├── BulkScreening.tsx # Upload PDFs for mass scoring
│   │   │       └── Profile.tsx       # Edit profile
│   │   ├── styles/
│   │   │   ├── globals.css     # Custom scrollbar, animations, glass morphism
│   │   │   ├── index.css       # Imports tailwind.css + theme.css + globals.css
│   │   │   ├── tailwind.css    # Tailwind directives
│   │   │   ├── theme.css       # CSS variables (color palette)
│   │   │   └── fonts.css       # @font-face declarations
│   │   ├── hooks/
│   │   │   ├── use-toast.ts    # Sonner toast wrapper
│   │   │   ├── use-mobile.tsx  # Mobile detection hook
│   │   │   └── use-password-strength.ts
│   │   ├── lib/
│   │   │   ├── api.ts          # Axios instance with JWT interceptors
│   │   │   └── utils.ts        # cn() utility (clsx + tailwind-merge)
│   │   └── test/setup.ts       # Vitest global setup (ResizeObserver, etc.)
│   ├── index.html
│   ├── vite.config.ts
│   ├── package.json
│   ├── nginx.conf              # Production Nginx config (SPA + API proxy)
│   ├── Dockerfile              # Multi-stage (builder → nginx production)
│   ├── .dockerignore
│   └── components.json         # shadcn/ui configuration
│
├── migrations/
│   └── 001_tables.sql          # Original PostgreSQL schema (baseline)
│
├── monitoring/                 # Observability stack (Phase 3)
│   ├── prometheus/             #   prometheus.yml + alerts.yml
│   ├── alertmanager/           #   alertmanager.yml (Slack routing)
│   ├── grafana/                #   provisioning + dashboards/sipsetu-overview.json
│   ├── loki/                   #   loki-config.yml (log aggregation)
│   ├── promtail/               #   promtail-config.yml (docker log shipping)
│   └── otel-collector/         #   OpenTelemetry collector config
├── docker-compose.yml          # Postgres, Redis, backend, frontend, celery; observability profile
├── docker-compose.override.yml # Dev overrides (hot-reload, dev servers)
├── Readme.md                   # This file
├── ROADMAP.md                  # Long-term enhancement roadmap
├── Smart_Resume_Analyzer_Complete_Guide.md  # Detailed guide
└── tsconfig.json
```

---

## 4. Setup & Installation

### Prerequisites

- Python 3.11+
- Node.js 22+
- PostgreSQL 15+
- npm or pnpm
- Docker + Docker Compose (optional, for containerized setup)

### Option A — Docker Compose (recommended)

```bash
# Development (Postgres + Redis + backend + frontend hot-reload)
docker compose up

# Production (Nginx-served frontend + gunicorn backend + celery worker/beat)
docker compose --profile production up

# Observability stack (Prometheus, Grafana, Alertmanager, Loki, Promtail, OTel collector)
docker compose --profile observability up
```

With the observability profile running:

| Tool | URL | Notes |
|---|---|---|
| Prometheus | `http://localhost:9090` | Scrapes `/metrics`, alert rules in `monitoring/prometheus/alerts.yml` |
| Grafana | `http://localhost:3000` | Provisioned dashboard “SipSetu — Overview” (RED + business KPIs), Loki log datasource |
| Alertmanager | `http://localhost:9093` | Slack notifications — set `SLACK_WEBHOOK_URL` first |
| Loki | `http://localhost:3100` | Log aggregation backend (Promtail ships container logs) |

Set `SLACK_WEBHOOK_URL` in your `.env` to receive alerts; set `OTEL_ENABLED=true`
on the backend to ship OpenTelemetry traces to the bundled collector.

The `docker-compose.override.yml` automatically wires development overrides
(hot-reload servers, dev database).

### Option B — Manual setup

#### Backend

```bash
cd backend
python -m venv venv
# Windows: .\venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Edit with your credentials
```

#### Database

```bash
# Create the database
psql -U postgres -c "CREATE DATABASE sipsetu;"

# Run the baseline schema
psql -d sipsetu -U postgres -f migrations/001_tables.sql

# OR use versioned Alembic migrations (preferred for schema changes)
cd backend
alembic upgrade head
```

#### Start

```bash
# Terminal 1: Backend
cd backend
python app.py    # Starts on http://localhost:5000

# Terminal 2: Frontend
cd frontend
npm install
npm run dev      # Starts on http://localhost:5173
```

### Testing

```bash
# Backend (38 unit tests, sqlite in-memory)
cd backend
pytest tests/unit --cov=. --cov-fail-under=30

# Frontend (14 tests)
cd frontend
npm run test

# Lint / type checks
cd backend && ruff check .            # backend
cd backend && mypy --strict --ignore-missing-imports .  # non-blocking
cd frontend && npm run lint           # eslint
cd frontend && npx tsc --noEmit       # TypeScript
```

### Environment Variables (`backend/.env`)

| Variable | Default | Required |
|---|---|---|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/sipsetu` | Yes |
| `JWT_SECRET_KEY` | `sipsetu-dev-jwt-secret-change-in-production` | Yes |
| `FRONTEND_URL` | `http://localhost:5173` | Yes (CORS) |
| `REDIS_URL` | `redis://localhost:6379/0` | For rate limiter / Celery |
| `DB_POOL_SIZE` / `DB_MAX_OVERFLOW` / `DB_POOL_RECYCLE` | `10` / `20` / `300` | Pool tuning |
| `ENVIRONMENT` | `development` | Enables Talisman only in `production` |
| `SMTP_HOST` | — | For email sending |
| `SMTP_PORT` | — | For email sending |
| `SMTP_USER` | — | For email sending |
| `SMTP_PASSWORD` | — | For email sending |
| `SMTP_USE_TLS` | `true` | For email sending |
| `SMTP_FROM` | `noreply@sipsetu.com` | For email sending |
| `STORAGE_PROVIDER` | `local` | `local`, `s3`, or `minio` |
| `SENTRY_DSN` | — | Error tracking (optional) |
| `LOG_LEVEL` / `LOG_FORMAT` | `INFO` / `json` | Logging config |
| `ML_MODEL_DIR` / `ML_MIN_TRAINING_ROWS` / `ML_MAX_ALPHA` | `ml_artifacts` / `15` / `0.8` | ML ranking tuning |

---

## 5. Backend Deep Dive

### 5.1 App Factory & Config

**File:** `backend/app.py`

The `create_app()` factory function:

1. Loads `.env` via `python-dotenv`
2. Configures Flask with `Config` class + `DATABASE_URL` override from env
3. Initialises structured JSON logging and request-logging middleware (with request IDs)
4. Configures CORS with explicit origins from `FRONTEND_URL`
5. Initialises SQLAlchemy (`db.init_app(app)`) with Postgres pool options (skipped for SQLite)
6. Enables Flask-Talisman security headers (CSP, HSTS, secure cookies) when `ENVIRONMENT=production`
7. Initialises the Redis-backed rate limiter (flask-limiter), falling back to the in-memory limiter if Redis is unavailable
8. Registers the `api` blueprint twice — canonical `/api/v1` and the legacy `/api` alias (Phase 4.1 versioning; legacy responses carry `Deprecation`/`Sunset`/`Link` headers)
9. Runs `db.create_all()` to create any missing tables, plus safe `ALTER TABLE ADD COLUMN IF NOT EXISTS` migrations for late-added columns (status, profile_image, email_verified, phone, location, reminders_sent)
10. Registers a `/api/health` endpoint that verifies DB and Redis connectivity
11. Attaches request-ID generation and `X-Request-ID` response headers
12. When `SWAGGER_ENABLED` (default true), initialises Flasgger OpenAPI docs — UI at `/apidocs/`, spec at `/apispec.json` (documents `/api/v1` only)

**File:** `backend/config.py`

Typed settings class (pydantic-settings) reading from environment variables with sensible dev defaults. The `DATABASE_URL` default is `postgresql://postgres:postgres@localhost:5432/sipsetu`.

### 5.2 Database Models

**File:** `backend/models.py`

Uses SQLAlchemy ORM with **single-table inheritance** for users. There are 15 tables/entities:

| Model | Table | Key Fields | Notes |
|---|---|---|---|
| `User` | `users` | user_id (UUID PK), email, name, password_hash, role, phone, location, profile_image, email_verified, created_at | Base table; `role` drives polymorphic inheritance |
| `BulkScreenJob` | `bulk_screen_jobs` | job_id (UUID PK), recruiter_id, status (queued/running/completed/failed), total_files, processed_files, file_paths, job_title, job_skills, results, error | Async bulk resume screening (Celery); results stored as JSON text |
| `Applicant` | `applicants` | user_id (FK → users CASCADE) | Child of User; has resumes |
| `Recruiter` | `recruiters` | user_id (FK → users CASCADE), company, job_title | Child of User; has jobs |
| `Skill` | `skills` | skill_id (UUID PK), skill_name (unique) | Shared vocabulary across jobs and resumes |
| `Job` | `jobs` | job_id (UUID PK), recruiter_id, title, description, location, job_type, experience_level, salary_min, salary_max, created_at | Many-to-many with skills via `job_skills` |
| `Resume` | `resumes` | resume_id (UUID PK), applicant_id, raw_text, file_path, uploaded_at | Many-to-many with skills via `resume_skills` |
| `JobApplication` | `job_applications` | application_id, job_id, applicant_id, applied_at, status | Unique constraint on (job_id, applicant_id) |
| `Ranking` | `rankings` | ranking_id, job_id, resume_id, matching_score, candidate_rank | Stores computed match scores |
| `EmailVerificationToken` | `email_verification_tokens` | token_id, user_id, token (indexed), expires_at, used | 6-digit OTP, 10-min expiry |
| `PasswordResetToken` | `password_reset_tokens` | token_id, user_id, token (indexed), expires_at, used | 6-digit OTP, 10-min expiry |
| `SavedJob` | `saved_jobs` | saved_job_id, applicant_id, job_id, created_at | Unique constraint on (applicant_id, job_id) |
| `Interview` | `interviews` | interview_id, job_id, applicant_id, recruiter_id, scheduled_at, duration_minutes, status, notes, meeting_link | |
| `Notification` | `notifications` | notification_id, user_id, title, message, type, is_read, related_job_id | related_job uses ON DELETE SET NULL |

**Relationships:**

```mermaid
erDiagram
    User ||--o{ Applicant : "is one"
    User ||--o{ Recruiter : "is one"
    Applicant ||--o{ Resume : "has"
    Applicant ||--o{ JobApplication : "submits"
    Applicant ||--o{ SavedJob : "bookmarks"
    Applicant ||--o{ Interview : "attends"
    Recruiter ||--o{ Job : "posts"
    Recruiter ||--o{ Interview : "conducts"
    Job ||--o{ JobApplication : "receives"
    Job ||--o{ Ranking : "ranks"
    Job ||--o{ SavedJob : "saved by"
    Job ||--o{ Interview : "for"
    Job ||--o{ Notification : "triggers"
    Resume ||--o{ Ranking : "scored in"
    Resume }o--o{ Skill : "has"
    Job }o--o{ Skill : "requires"
    Notification }o--|| User : "belongs to"
    User ||--o{ EmailVerificationToken : "verifies"
    User ||--o{ PasswordResetToken : "resets"
    User ||--o{ Notification : "receives"
```
- `Job` ↔ `Skill`: Many-to-many via `job_skills` junction table
- `Resume` ↔ `Skill`: Many-to-many via `resume_skills` junction table
- `Applicant` → `Resume`: One-to-many
- `Job` → `Ranking`: One-to-many (CASCADE)
- `Job` → `JobApplication`: One-to-many
- All foreign keys use `ON DELETE CASCADE` except `notifications.related_job_id` which uses `ON DELETE SET NULL`

### 5.3 Database Schema (SQL)

**File:** `migrations/001_tables.sql`

A hand-written, re-runnable PostgreSQL schema (`CREATE TABLE IF NOT EXISTS`) covering all 15 tables. Includes:

- `uuid-ossp` extension for UUID generation
- Proper column types matching the SQLAlchemy models
- All foreign key constraints with `ON DELETE CASCADE` / `SET NULL`
- Unique constraints on `users.email`, `skills.skill_name`, `job_applications(job_id, applicant_id)`, `saved_jobs(applicant_id, job_id)`
- Unique + indexed `token` columns on `email_verification_tokens` and `password_reset_tokens`
- CHECK constraints on `role`, `status`, `type` columns

### 5.4 Authentication & Authorization

**File:** `backend/auth_middleware.py`

Three decorators enforce access control:

| Decorator | What it does | Returns |
|---|---|---|
| `@require_auth` | Validates Bearer JWT from `Authorization` header. Sets `g.current_user_id` and `g.current_user_role`. | 401 if missing/expired/invalid |
| `@require_role('applicant')` | Wraps `@require_auth` + checks role. | 403 if wrong role |
| `@_ownership_required` | Custom wrapper (in `routes.py`) that verifies the URL's `user_id`/`applicant_id`/`recruiter_id` matches the JWT subject. | 403 if mismatch |

**JWT Payload:**
```json
{
  "user_id": "uuid-string",
  "role": "applicant | recruiter",
  "exp": 1712345678,
  "iat": 1712259278
}
```

Tokens expire after 24 hours (configurable via `JWT_EXPIRATION_HOURS`).

### 5.5 API Routes

**File:** `backend/routes.py`

All routes are registered under the `api` Blueprint at **two prefixes** (Phase 4.1): the canonical `/api/v1` and the legacy `/api` alias. The legacy prefix is deprecated — responses carry `Deprecation: true`, a `Sunset` date, and a `Link: <…/api/v1/…>; rel="successor-version"` header (RFC 8594). Interactive OpenAPI docs live at **`/apidocs/`** (spec at `/apispec.json`); the auth endpoints carry request/response schemas and more can be documented by adding a `---` YAML block to the route docstring (schemas are defined in `backend/api_docs.py`).

On `/api/v1` every **list endpoint** uses the Phase 4.2 envelope: `{ "data": [...], "meta": { "pagination": { "total", "limit", "next_cursor", "has_more" }, ... } }`. The paginated ones (`/jobs`, `matched-jobs`, `/jobs/<id>/candidates`, `/recruiters/<id>/candidates`) use **keyset cursor pagination** (`?limit=` + opaque `?cursor=`, helpers in `backend/pagination.py`) and accept `?sort=` (`sort=title`, `sort=-created_at`, `sort=matching_score` / `-matching_score`). The legacy `/api` prefix keeps the historical response shapes for the deprecation window. The file is ~1400 lines and organises endpoints into sections:

#### Authentication

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | — | Register user, sends verification OTP |
| POST | `/auth/login` | — | Authenticate, returns JWT |
| POST | `/auth/logout` | — | Placeholder (stateless) |
| GET | `/auth/me` | `@require_auth` | Current user profile |
| POST | `/auth/verify-email` | — | Verify email with OTP (6-digit) |
| POST | `/auth/resend-verification` | `@require_auth` | Resend verification OTP |
| POST | `/auth/forgot-password` | — | Send password reset OTP |
| POST | `/auth/verify-reset-otp` | — | Verify reset OTP, get temp token |
| POST | `/auth/reset-password` | — | Set new password with temp token |

#### Profile

| Method | Path | Auth | Description |
|---|---|---|---|
| GET/PUT | `/profile/<user_id>` | Ownership | Read/update profile |

#### Jobs

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/jobs` | — | List jobs (filters: search, job_type, experience_level, location, salary, skill) |
| POST | `/jobs` | Recruiter | Create job posting |
| GET | `/jobs/<job_id>` | — | Single job details |
| PUT | `/jobs/<job_id>` | Owner (recruiter) | Update job |
| DELETE | `/jobs/<job_id>` | Owner (recruiter) | Delete job |
| POST | `/jobs/<job_id>/apply` | Applicant | Apply to a job |
| POST | `/jobs/<job_id>/save` | Applicant | Save/bookmark a job |
| DELETE | `/jobs/<job_id>/save` | Applicant | Unsave a job |

#### Resumes

| Method | Path | Auth | Description |
|---|---|---|---|
| GET/POST | `/resumes` | Applicant | List/create resumes |
| GET/PUT/DELETE | `/resumes/<resume_id>` | Owner | Read/update/delete resume |
| POST | `/resumes/upload-pdf` | Applicant | Upload PDF, extract text + skills |

#### Applicant

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/applicants/<id>/dashboard` | Ownership | Stats, top matches, interviews |
| GET | `/applicants/<id>/matched-jobs` | Ownership | All jobs ranked by match score |
| GET | `/applicants/<id>/applications` | Ownership | Applications with status + scores |
| GET | `/applicants/<id>/saved-jobs` | Ownership | Saved jobs with scores |
| GET | `/applicants/<id>/saved-job-ids` | Ownership | Just IDs (for bookmark state) |
| GET | `/applicants/<id>/skill-gap` | Ownership | Missing skills analysis |
| PUT | `/applicants/<id>/skill-progress` | Ownership | Update tracked skill progress |

#### Recruiter

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/recruiters/<id>/dashboard` | Ownership | Stats, top candidates, interviews |
| GET | `/recruiters/<id>/candidates` | Ownership | All candidates across jobs |
| GET | `/jobs/<job_id>/candidates` | Owner | Candidates for one job |
| POST | `/recruiters/bulk-screen` | Recruiter | Upload up to 50 PDFs, score vs job (queues a Celery job) |
| GET | `/recruiters/bulk-screen/<job_id>` | Owner | Poll bulk-screen job status/progress/results |
| PATCH | `/applications/<id>/status` | Recruiter | Update application status |
| GET | `/jobs/<job_id>/application-status/<applicant_id>` | Owner | Application status for one job |

#### Rankings

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/rankings/<id>/explain` | Owner | Feature contribution breakdown for a score |
| PUT | `/rankings/<id>` | Recruiter | Manually adjust a candidate ranking/score |

#### ML Ranking

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/ml/ranking/train` | Authenticated | Train/retrain the ML ranking model |
| GET | `/ml/ranking/status` | Authenticated | Model availability, metrics, blend alpha |

#### Applications

| Method | Path | Auth | Description |
|---|---|---|---|
| DELETE | `/applications/<id>` | Owner | Withdraw/delete an application |

#### Notifications

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/notifications/<user_id>` | Ownership | List notifications |
| PATCH | `/notifications/<id>/read` | Owner | Mark one read |
| PATCH | `/notifications/read-all/<user_id>` | Ownership | Mark all read |

#### Interviews

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/interviews` | Recruiter | Propose interview |
| PATCH | `/interviews/<id>/status` | Owner | Update status |
| PATCH | `/interviews/<id>/respond` | Applicant | Accept/decline interview |
| PATCH | `/interviews/<id>/cancel` | Owner | Cancel interview |
| GET | `/interviews/<user_id>` | Ownership | List interviews |

#### Public

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/public/preview` | — | Stats, recent jobs, top candidates |
| GET | `/health` | — | Health check |
| GET | `/dev/email-preview?template=verification` | — | Render an email template for review (dev only) |

### 5.6 Scoring & Ranking Pipeline

**Files:** `backend/routes_common.py` (shared helpers)

#### Scoring Flow

```mermaid
flowchart LR
    A["Resume Upload"] --> B["extract_skills_from_text"]
    B --> C["create_rankings_for_resume"]
    C --> D["calculate_ranking_score"]
    D --> H["Coverage score<br/>matched / job_skills × 100"]
    D --> J["Experience score<br/>from regex parsing"]
    D --> K["Content similarity<br/>TF-IDF cosine × 100"]
    H --> L["70% × skills + 15% × exp + 15% × content"]
    J --> L
    K --> L
    L --> M["Clip 0–100"]
    M --> N["Store in rankings table"]
```

1. An applicant uploads a resume or applies to a job
2. `create_rankings_for_job()` or `create_rankings_for_resume()` is called
3. These call `calculate_ranking_score(resume, job)`
4. `calculate_ranking_score()` computes the deterministic heuristic (skills coverage, experience, content similarity)


#### Registration Flow

```mermaid
sequenceDiagram
    actor User
    participant React as React App
    participant Api as Axios Client
    participant Backend as Flask API
    participant DB as PostgreSQL

    User->>React: Fill registration form
    React->>Api: api.post("/auth/register", {name, email, password, role})
    Api->>Backend: POST /api/auth/register<br/>Content-Type: application/json
    Backend->>Backend: Validate input
    Backend->>Backend: hash password (Werkzeug)
    Backend->>DB: INSERT user + applicant/recruiter
    Backend->>Backend: Generate 6-digit OTP
    Backend->>DB: INSERT email_verification_token {otp, expires}
    Backend->>Backend: send_verification_otp(email, otp)
    Note over Backend: If no SMTP configured,<br/>prints OTP to stderr
    Backend->>Backend: create_token(user_id, role)
    Backend-->>Api: 201 {token, user_id, role, email, email_verified}
    Api-->>React: Response data
    React->>React: localStorage.setItem("auth_token", token)
    React->>React: setUser({...})
    React-->>User: Redirect to /verify-email?email=...

    User->>React: Enter 6-digit OTP
    React->>Api: api.post("/auth/verify-email", {email, otp})
    Api->>Backend: POST /api/auth/verify-email
    Backend->>DB: SELECT user WHERE email = ...
    Backend->>DB: SELECT token WHERE user_id=... AND otp=... AND NOT used
    Backend->>DB: UPDATE token SET used=true
    Backend->>DB: UPDATE user SET email_verified=true
    Backend-->>Api: 200 {email_verified: true}
    Api-->>React: Success
    React-->>User: "Email Verified!" 🎉
```

#### Heuristic Score Formula

```
skills_score   = (intersection(job_skills, resume_skills) / len(job_skills)) × 100
experience_score = calculated from resume text vs job requirement
content_sim    = cosine_similarity(TF-IDF vectors of resume vs job text) × 100

combined_score = skills_score × 0.70 + experience_score × 0.15 + content_sim × 0.15
```

**Key guarantee:** If a candidate has **all** required job skills, `skills_score = 100`, so the minimum combined score is **70%** (even with zero experience and zero content similarity).

#### Experience Scoring

Experience years are extracted from resume text using regex patterns. Compared against the job's `experience_level` field which maps to years:
- `fresher` → 0
- `1-3` → 2
- `3-5` → 4
- `5+` → 5

If the candidate has more years than required, they score 100 on experience.

#### Bulk Screening

The `/recruiters/bulk-screen` endpoint follows the same scoring formula (coverage-based skills with 70/15/15 weights) but operates on uploaded PDF files rather than stored resumes. It returns per-file scores, matched/missing skills, and text snippets.

### 5.7 Rate Limiting

**File:** `backend/rate_limiter.py` (+ `app.py` for Flask-Limiter init)

A rate limiter that is **Redis-backed when available** (via Flask-Limiter with a sliding-window strategy) and **falls back to an in-memory store** for single-process development or when Redis is unavailable. Fail-open: if Redis connection fails, the limiter logs a warning and falls back rather than blocking requests.

| Endpoint | Limit | Window | Keyed By |
|---|---|---|---|
| `POST /auth/register` | 5 | 1 hour | IP address |
| `POST /auth/verify-email` | 5 | 10 minutes | Email |
| `POST /auth/resend-verification` | 3 | 15 minutes | User ID |
| `POST /auth/forgot-password` | 3 | 15 minutes | Email |

Returns `429 Too Many Requests` with a `retry_after` message when exceeded. A global default limit (`RATE_LIMIT_DEFAULT`, e.g. `200 per minute`) applies via Flask-Limiter in production.

### 5.8 Email Utilities

**File:** `backend/utils/email.py`

Sends emails via SMTP when configured in `.env`. **Falls back to printing to console stderr in development** (no SMTP required to run locally).

| Function | Purpose |
|---|---|
| `send_email(to, subject, html, text)` | Generic email sender (renders Jinja2 templates) |
| `send_password_reset_otp(to, otp, name)` | Password reset (6-digit code) |
| `send_verification_otp(to, otp, name)` | Email verification (6-digit code) |
| `send_interview_reminder(...)` | Interview reminder email |
| `render_email(template_name, **ctx)` | Render a template to (html, text) — used by the dev preview endpoint |

**Dev preview** — `GET /api/dev/email-preview?template=verification|password_reset|interview_reminder`
renders a template in the browser for visual review (disabled in production).

---

## 6. Frontend Deep Dive

### 6.1 Entry Point & Routing

**File:** `frontend/src/main.tsx` → `frontend/src/app/App.tsx` → `frontend/src/app/routes.tsx`

The app mounts with `React.StrictMode`, wraps in `AuthProvider`, then renders `<App />` which contains a `RouterProvider` with a `createBrowserRouter` configuration.

Routes are defined in `routes.tsx`:

| Path | Component | Access |
|---|---|---|
| `/` | LandingPage | Public |
| `/preview` | PreviewPage | Public |
| `/login` | LoginPage | Public |
| `/register` | RegisterPage | Public |
| `/forgot-password` | ForgotPasswordPage | Public |
| `/verify-email` | VerifyEmailPage | Public (pre-fills from `?email=` param) |
| `/applicant/*` | 7 sub-routes | Protected (applicant role) |
| `/recruiter/*` | 6 sub-routes | Protected (recruiter role) |
| `*` | NotFound | Public |

All protected routes use `ProtectedRoute` which checks the JWT role from `localStorage` and redirects to `/login` if unauthorized.

Each protected section has its own layout component providing a sidebar navigation, header, and content area:
- `ApplicantLayout` — for `/applicant/*`
- `RecruiterLayout` — for `/recruiter/*`

### 6.2 Auth Context & API Client

**File:** `frontend/src/app/context/AuthContext.tsx`

The `AuthProvider` wraps the entire app and exposes:
- `user` — current user object (or null)
- `loading` — true during session restoration on mount
- `login(email, password)` — authenticates, stores JWT + user data in localStorage
- `register(name, email, password, role)` — creates account, stores JWT
- `logout()` — clears all stored auth data
- `isAuthenticated` — boolean convenience

On mount, if a JWT exists in `localStorage`, the context calls `/auth/me` to validate and restore the session.

**File:** `frontend/src/lib/api.ts`

Axios instance configured with:
- `baseURL: http://localhost:5000/api`
- Request interceptor: attaches `Authorization: Bearer <token>` from localStorage
- Response interceptor: on 401, clears auth and redirects to `/login`

### 6.3 Pages

#### Public Pages

| Page | File | Description |
|---|---|---|
| **LandingPage** | `/pages/LandingPage.tsx` | Hero section with animated counters, feature cards, "How It Works" steps, live activity feed, CTA, footer |
| **LoginPage** | `/pages/LoginPage.tsx` | Email + password form with validation, error states, link to register/forgot-password |
| **RegisterPage** | `/pages/RegisterPage.tsx` | Name + email + password + role toggle, password strength indicator |
| **ForgotPasswordPage** | `/pages/ForgotPasswordPage.tsx` | 3-step flow: email → OTP → new password |
| **VerifyEmailPage** | `/pages/VerifyEmailPage.tsx` | 6-digit OTP input with auto-advance, resend button, success/error states |
| **PreviewPage** | `/pages/PreviewPage.tsx` | Public stats + recent jobs display |

#### Applicant Pages

| Page | File | Description |
|---|---|---|
| **Dashboard** | `/pages/applicant/Dashboard.tsx` | Skill count, resume strength, average match score, top 4 matched jobs, recent jobs carousel, upcoming interviews, missing skills, verification banner |
| **JobMatches** | `/pages/applicant/JobMatches.tsx` | All jobs ranked by match score, filters (search, location, type, experience, salary, skills), bookmark/apply actions, job detail dialog |
| **MyApplications** | `/pages/applicant/MyApplications.tsx` | Applied jobs with status badges (pending/shortlisted/rejected), match scores, applied date |
| **Profile** | `/pages/applicant/Profile.tsx` | Edit name, phone, location |
| **Resume** | `/pages/applicant/Resume.tsx` | Upload PDF or paste text, view extracted skills |
| **SavedJobs** | `/pages/applicant/SavedJobs.tsx` | Bookmarked jobs with match scores, apply/bookmark actions |
| **SkillGap** | `/pages/applicant/SkillGap.tsx` | Compare resume skills vs job requirements, readiness score, missing skills with priority labels |

#### Recruiter Pages

| Page | File | Description |
|---|---|---|
| **Dashboard** | `/pages/recruiter/Dashboard.tsx` | Active postings count, total candidates, top match score, top 3 candidates, recent jobs |
| **ManageJobs** | `/pages/recruiter/ManageJobs.tsx` | List all job postings with edit/delete actions |
| **PostJob** | `/pages/recruiter/PostJob.tsx` | Create job form with skills input |
| **Candidates** | `/pages/recruiter/Candidates.tsx` | All candidates ranked by score across all jobs, filter by job, status management |
| **BulkScreening** | `/pages/recruiter/BulkScreening.tsx` | Upload up to 50 PDFs, select a job or enter custom skills, view scored results |
| **Profile** | `/pages/recruiter/Profile.tsx` | Edit name, phone, location, company, job title |

### 6.4 UI Components

**File:** `frontend/src/components/ui/` (60+ shadcn/ui primitives)

The project uses shadcn/ui — a collection of unstyled, accessible React components built on Radix UI primitives and styled with Tailwind CSS v4. Key components:

| Category | Components |
|---|---|
| Feedback | `alert`, `badge`, `progress`, `skeleton`, `spinner`, `sonner` (toast), `toast` |
| Forms | `button`, `button-group`, `input`, `textarea`, `select`, `checkbox`, `radio-group`, `switch`, `slider`, `label`, `field`, `form` |
| Layout | `card`, `accordion`, `tabs`, `separator`, `scroll-area`, `resizable`, `aspect-ratio` |
| Navigation | `breadcrumb`, `menubar`, `navigation-menu`, `pagination`, `sidebar`, `tabs` |
| Overlay | `dialog`, `alert-dialog`, `drawer`, `sheet`, `popover`, `hover-card`, `tooltip` |
| Data | `table`, `command`, `calendar`, `carousel`, `chart` |
| Misc | `avatar`, `collapsible`, `context-menu`, `dropdown-menu`, `input-otp`, `kbd`, `toggle`, `toggle-group` |

Custom layout components:
- **`ApplicantLayout.tsx`** — Gradient sidebar with nav items, mobile hamburger, notification bell, profile section
- **`RecruiterLayout.tsx`** — Same structure, different nav items for recruiter flows
- **`ProtectedRoute.tsx`** — Role-checking wrapper that redirects to `/login` or shows 403
- **`SipSetuLogo.tsx`** — Brand text with gradient styling
- **`NotificationBell.tsx`** — Dropdown with unread count, mark-read, and mark-all-read
- **`VisualBackground.tsx`** — Animated gradient or particle background
- **`PasswordStrengthIndicator.tsx`** — Visual strength meter for registration

### 6.5 Styling

**Tailwind CSS v4** with CSS variables for the design system. Key tokens:

```css
:root {
  --color-primary: #F97316;      /* Orange */
  --color-primary-hover: #e8630e;
  --color-secondary: #1E3A5F;    /* Navy */
  --color-accent: #3B82F6;       /* Blue */
  --background: #ffffff;
  --foreground: #0f172a;
  --muted: #f1f5f9;
  --muted-foreground: #64748b;
  --border: #e2e8f0;
  --ring: #F97316;
  --radius: 0.5rem;
}
```

Custom animations defined in `globals.css`:
- `fade-in`, `slide-up`, `slide-down`, `scale-in` — page entry animations
- `pulse-soft` — gentle pulse
- `shimmer` — loading skeleton effect
- Glass-morphism utilities: `.glass`, `.glass-dark`

---

## 7. Complete API Reference

### Authentication

#### `POST /api/auth/register`

Register a new user.

```json
// Request
{ "name": "Jane", "email": "jane@example.com", "password": "securepass123", "role": "applicant" }

// Response 201
{ "message": "...", "token": "jwt...", "user_id": "...", "role": "applicant", "name": "Jane", "email": "jane@example.com", "email_verified": false }
```

#### `POST /api/auth/login`

```json
// Request
{ "email": "jane@example.com", "password": "securepass123" }

// Response 200
{ "message": "Login successful", "token": "jwt...", "user_id": "...", "role": "applicant", "name": "Jane", "email": "jane@example.com", "profile_image": null, "email_verified": false }
```

#### `POST /api/auth/verify-email`

```json
// Request
{ "email": "jane@example.com", "otp": "482931" }

// Response 200
{ "message": "Email verified successfully! You can now access all features.", "email_verified": true }
```

#### `POST /api/auth/forgot-password`

```json
// Request
{ "email": "jane@example.com" }

// Response 200
{ "message": "If that email is registered, an OTP has been sent." }
```

#### `POST /api/auth/verify-reset-otp`

```json
// Request
{ "email": "jane@example.com", "otp": "729104" }

// Response 200
{ "message": "OTP verified successfully.", "reset_token": "temp-token...", "email": "jane@example.com" }
```

#### `POST /api/auth/reset-password`

```json
// Request
{ "token": "temp-token...", "email": "jane@example.com", "password": "newSecurePass456" }

// Response 200
{ "message": "Password has been reset successfully. You can now sign in." }
```

### Jobs

#### `GET /api/jobs`

Query parameters: `page`, `per_page`, `search`, `job_type`, `experience_level`, `location`, `salary_min`, `salary_max`, `skill`, `recruiter_id`

```json
// Response 200
{
  "total": 12,
  "page": 1,
  "per_page": 20,
  "pages": 1,
  "jobs": [
    {
      "job_id": "uuid",
      "title": "Senior Frontend Developer",
      "description": "...",
      "location": "Remote",
      "job_type": "full-time",
      "experience_level": "3-5",
      "salary_min": 1200000,
      "salary_max": 1800000,
      "salary": "Rs.1200000-1800000 LPA",
      "recruiter_id": "uuid",
      "recruiter_name": "Acme Corp",
      "recruiter_company": "Acme Corp",
      "recruiter_profile_image": null,
      "created_at": "2026-07-26T11:03:33.213251",
      "skills": ["react", "typescript", "css"]
    }
  ]
}
```

#### `POST /api/jobs/<job_id>/apply`

```json
// Response 201
{ "message": "Job application saved successfully", "job_id": "...", "applicant_id": "...", "application_id": "...", "has_resume": true }
```

### Scoring

#### `GET /api/applicants/<id>/matched-jobs`

Returns all jobs ranked by match score against the applicant's latest resume. Supports same filters as `/api/jobs` plus `min_score`.

```json
{
  "total": 8,
  "page": 1,
  "per_page": 50,
  "pages": 1,
  "resume_id": "uuid",
  "matched_jobs": [
    {
      "job_id": "uuid",
      "title": "Senior Frontend Developer",
      "matching_score": 85.42,
      "applied": true,
      // ... plus all job fields from format_job()
    }
  ]
}
```

#### `POST /api/recruiters/bulk-screen`

Multipart form upload. Fields: `files` (PDFs, max 50), `job_id` (optional), `custom_title`, `custom_skills`, `custom_description`.

Returns per-file scores with matched/missing skills and text snippets.

---

## 8. Scoring Algorithm

The scoring system uses a **coverage-based** formula (not Jaccard similarity), meaning candidates are only scored on how many of the job's required skills they possess — extra skills don't penalize them.

### Full Formula

```
skills_score = (number of job skills present in resume / total job skills) × 100
              ↓
              Range: 0–100
              If all job skills matched: always 100

experience_score = compute from resume text vs job's experience level
                  ↓
                  Range: 0–100
                  If candidate years ≥ required years: 100

content_sim = cosine_similarity(TF-IDF of resume text, TF-IDF of job text) × 100
             ↓
             Range: 0–100

combined = skills_score × 0.70 + experience_score × 0.15 + content_sim × 0.15
           ↓
           Range: 0–99.99 (capped)
```

### Why Coverage Instead of Jaccard?

**Jaccard** = `intersection / union` penalizes candidates for having extra skills. Example:

> Job needs: Python, React, SQL (3 skills)
> Candidate knows: Python, React, SQL, Docker, AWS (5 skills)
> - **Jaccard:** 3/6 = **50%** ← unfairly low
> - **Coverage:** 3/3 = **100%** ← correct

### Guarantee

If a candidate has all required job skills, the minimum score is:

```
100 × 0.70 + 0 × 0.15 + 0 × 0.15 = 70%
```

Even with zero experience and zero text similarity.

### ML Ranking Model (Optional)

`backend/ranking_ml.py` provides an optional **gradient-boosted ranker** that
learns from historical ranked pairs and refines the heuristic above:

- **17 features** — skill coverage/Jaccard/specificity (IDF-weighted, so rare
  skills like *kubernetes* outweigh generic ones like *communication*),
  experience fit/gap, TF-IDF content similarity, title similarity, keyword
  density, resume length, seniority & education signals.
- **HistGradientBoostingRegressor** with early stopping, trained on a
  **grouped train/test split by job** so it generalizes to unseen jobs
  rather than memorizing per-job rankings.
- **Recruiter-feedback labels** — shortlisted applications are pulled toward
  a high target, rejected ones toward a low target, so the model learns
  recruiter preferences, not just the heuristic.
- **Safe blending** — predictions are `alpha × model + (1-alpha) × heuristic`
  (`alpha` ramps up to 0.8 as training rows grow), so scores stay on the
  0-100 scale and never degrade below the heuristic on small datasets.
- Training guard: requires ≥15 ranked pairs with ≥2 distinct labels.

**Trigger:** `POST /api/ml/ranking/train` (authenticated).
**Status:** `GET /api/ml/ranking/status` (authenticated) — reports model
availability, metrics (RMSE/MAE/R²/NDCG@5/precision@5/recall@5/MRR@5),
training rows, and the current blend `alpha`.

Without a trained model, `calculate_ranking_score()` falls back to the
coverage-based heuristic above, so the app works identically either way.

#### Auto-retrain (background job)

`backend/retrain_scheduler.py` starts a daemon thread (alongside the
interview-reminder scheduler) that retrains the model automatically, so no
manual `POST /api/ml/ranking/train` calls are needed:

- **Nightly** — once the UTC clock passes 3 AM and at least a day has passed
  since the last successful training.
- **New recruiter feedback** — when the count of shortlisted/rejected
  applications grows since the last sweep (even a single shortlist/reject
  triggers a retrain, since those statuses teach the model preferences).
- **First run** — attempts once on boot if no model has ever trained
  (no-ops until enough ranked pairs exist).

All attempts are rate-limited to **one per hour**, and state (last attempt,
last successful train, feedback count) is persisted to
`ml_artifacts/retrain_state.json` (gitignored) so triggers survive restarts.
If training fails the model keeps the previous artifact; scoring falls back
silently to the heuristic if the artifact is missing or corrupt.

---

## 9. Rate Limiting Rules

| Endpoint | Limit | Window | Key | Effect |
|---|---|---|---|---|
| `POST /auth/register` | 5 | 1 hour | IP | Prevents mass account creation |
| `POST /auth/verify-email` | 5 | 10 minutes | Email | Prevents OTP brute-force (1M combos, 5 tries/infeasible) |
| `POST /auth/resend-verification` | 3 | 15 minutes | User ID | Prevents email flooding |
| `POST /auth/forgot-password` | 3 | 15 minutes | Email | Prevents enumeration + spam |

All return `429 Too Many Requests`:
```json
{ "error": "Too many requests. Please try again in 47 seconds." }
```

**Note:** The rate limiter is **Redis-backed** (Flask-Limiter) for multi-worker production, with an automatic **in-memory fallback** for single-process development. It fails open if Redis is unavailable.

---

## 10. Known Limitations

1. **Partial test coverage** — 38 backend unit tests (routes_common, auth, rate limiter) and 14 frontend tests exist, but backend coverage is ~33% and integration tests are excluded from CI. Coverage thresholds: backend 30%, frontend via Vitest.
2. **Mypy non-strict** — `mypy --strict` reports warnings and is non-blocking in CI. Full strict typing is a known debt item.
3. **Email sending** — Falls back to console in development. Requires SMTP config for production.
4. **Single-process default** — The dev server is synchronous; production uses Gunicorn + gevent (Dockerfile default).
5. **Bulk screening is async** — `/recruiters/bulk-screen` queues a Celery job (`tasks/bulk_screen_tasks.py`) and the UI polls `GET /recruiters/bulk-screen/<job_id>`. Falls back to synchronous processing when no broker is configured.
5b. **Priority queues + dead-letter queue** — `task_routes` split work into `email` (high), `bulk_screen` (medium) and `retrain` (low) queues consumed by dedicated workers (see `docker-compose.yml`); a job that permanently fails is recorded in the `dead_letter` Redis list by `FlaskTask.on_failure` and can be inspected/requeued via `celery -A celery_app call tasks.dead_letter_tasks.{list,count,requeue}_dead_letters`.
6. **Profile images** — Stored as base64/URL text in the database, not on object storage.
7. **File upload size validation** — Size/MIME/extension checks exist (`validation.py`), but no virus scanning (ClamAV).
8. **Redis hard dependency for production features** — Rate limiting, Celery, and health checks degrade gracefully to dev fallbacks, but require Redis for production behavior.

---

## 11. Future Roadmap

### Done (Phase 1 — Foundation, Phase 2 — Hardening, Phase 3 — Observability)

- [x] **Docker Compose** — One-command `docker compose up` (Postgres, Redis, backend, frontend; production profile with Nginx + gunicorn + celery; observability profile with Prometheus/Grafana/Alertmanager/Loki)
- [x] **Alembic migrations** — Versioned schema migrations (`backend/migrations/`)
- [x] **Test suite** — pytest (backend) + Vitest/RTL (frontend)
- [x] **CI pipeline** — GitHub Actions for lint, typecheck, test, build, Docker (path-filtered `backend-ci.yml` / `frontend-ci.yml`)
- [x] **Redis-backed rate limiting** — Flask-Limiter with in-memory fallback
- [x] **Production WSGI server** — Gunicorn + gevent
- [x] **Object storage abstraction** — Local / S3 / MinIO via `utils/storage.py` (incl. presigned upload URLs)
- [x] **Request validation** — Pydantic schemas, file upload hardening (size/MIME/extension)
- [x] **Security headers** — Flask-Talisman (CSP, HSTS) in production
- [x] **Background jobs** — Celery worker/beat for email, ML retraining, reminders
- [x] **Structured logging** — JSON logs, per-module log levels, request-ID middleware (correlation IDs)
- [x] **Prometheus metrics** — `prometheus-flask-exporter` `/metrics` endpoint + business counters (registrations, applications, emails) + DB pool/Redis gauges
- [x] **Grafana dashboards** — Provisioned “SipSetu — Overview” (RED + business KPIs) via the observability profile
- [x] **Alerting** — Prometheus alert rules (error rate >1%, p99 >2s, pool exhaustion, Redis down) + Alertmanager → Slack
- [x] **Log aggregation** — Loki + Promtail (ships container logs labeled `logging=promtail`)
- [x] **Distributed tracing** — OpenTelemetry (Flask/SQLAlchemy/requests instrumentation, 10% sampling) behind `OTEL_ENABLED=true` + bundled OTel collector
- [x] **Error tracking** — Sentry (backend + frontend) with release tagging
- [x] **Email templates** — Jinja2 HTML + text templates for verification/reset/reminder emails, dev preview at `/api/dev/email-preview`
- [x] **Dependency scanning in CI** — `pip-audit` + `npm audit` (non-blocking)
- [x] **Migration drift check** — `alembic check` in CI
- [x] **Codecov badge** — Upload + display coverage badge

### Phase 4 (API & Architecture Maturity) — in progress

- [x] **API versioning** — Canonical `/api/v1` + deprecated legacy `/api` (RFC 8594 `Deprecation`/`Sunset`/`Link` headers)
- [x] **OpenAPI docs** — Flasgger UI at `/apidocs/`, spec at `/apispec.json` (auth schemas in `backend/api_docs.py`)
- [x] **Response envelope + cursor pagination** — `{ data, meta }` on all v1 list endpoints; keyset pagination via `?limit=` + `?cursor=` (`backend/pagination.py`); `?sort=` support
- [x] **Celery priority queues + DLQ** — `task_routes` (email high / bulk-screen medium / retrain low) with dedicated workers; permanently failed jobs land in the `dead_letter` Redis list, inspect/requeue via `tasks.dead_letter_tasks.*`
- [x] **Hot-query index audit** — Composite DESC indexes on `jobs`, `rankings`, `notifications` (migration `003_hot_query_indexes`, mirrors model `__table_args__`) + `pg_trgm` GIN indexes on `jobs` search columns (migration `004_pg_trgm_jobs_search`); re-run audit: `backend/scripts/explain_analyze.sql`
- [x] **Jobs full-text search** — `GET /jobs?search=` now uses Postgres `tsvector` full-text search (migration `005_jobs_full_text_search`: `search_vector` column + GIN index, backfilled) and ranks results by relevance (`ts_rank`); short terms and SQLite dev/tests fall back to ILIKE, backed by the pg_trgm GIN indexes

### Pending

- [ ] **Coverage raise** — Push backend coverage from ~33% toward 50%+
- [ ] **Virus scanning** — ClamAV for uploaded resumes (documented in Known Limitations)
- [ ] **Streaming uploads / CDN** — Direct-to-S3 client uploads and a CDN in front of static assets
- [ ] **Phase 4.4 remaining** — PgBouncer connection pooling, read replicas, partitioning

### Medium-term (3–6 months)

- [ ] **API versioning** — `/api/v1/` with deprecation policy
- [ ] **OpenAPI/Swagger docs** — Auto-generated from routes
- [ ] **Cursor pagination** — Replace offset/limit for large datasets
- [ ] **Real-time notifications** — WebSocket / SSE with Redis pub/sub
- [ ] **Admin dashboard** — User management, job moderation, analytics

### Long-term (6–12 months)

- [ ] **Resume parsing improvements** — NLP / LLM-based extraction (structured JSON)
- [ ] **Semantic search** — Vector embeddings (pgvector) for matching
- [ ] **Multi-language support** — i18n for international users
- [ ] **Calendar integration** — Google/Outlook sync for interviews
- [ ] **Multi-tenancy / organizations** — Recruiter teams, role-based access
- [ ] **Performance optimization** — Index audit, connection pooling, CDN

---

*© 2026 SipSetu. Documentation generated from source code.*
