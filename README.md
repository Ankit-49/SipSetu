# SipSetu

**No skill left behind.** AI-powered recruitment platform bridging job seekers and recruiters. Uses skill-based matching, resume analysis, and candidate ranking to connect talent with opportunity.

## Features

- **Role-based portals** — Dedicated dashboards for applicants and recruiters
- **Resume upload** — Upload your resume for AI-powered skill extraction
- **Intelligent job matching** — Jobs ranked by an ML-backed scoring pipeline with heuristic fallback
- **Skill gap analysis** — Identify missing skills for your target roles with learning resources
- **Candidate ranking** — Recruiters see applicants auto-scored against job requirements
- **Profile management** — Manage personal info, company details, and preferences

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3, Flask, SQLAlchemy, PostgreSQL |
| Frontend | React 18, TypeScript, Vite 6, Tailwind CSS v4 |
| UI | shadcn/ui, Radix UI, Lucide Icons, Framer Motion |
| Tooling | Axios, React Router v7, Recharts, Lottie |

## Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 15+
- npm or pnpm

## Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd SipSetu
```

### 2. Backend setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# macOS / Linux:
# source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
```

> **Important:** Edit `.env` and replace the placeholder values with your own PostgreSQL credentials (password, host, port). The example file uses `YOUR_PASSWORD_HERE` — do not commit real credentials.

```bash
# Create the database in PostgreSQL
# psql -U postgres -c "CREATE DATABASE sipsetu;"

# Initialize database tables
python -c "from app import create_app; from models import db; app = create_app(); app.app_context().push(); db.create_all()"

# Apply additional schema migrations
python update_db.py

# Start the backend server
python app.py
```

The backend starts at **http://127.0.0.1:5000**. Verify with a health check:

```bash
curl http://127.0.0.1:5000/api/health
# {"status": "healthy"}
```

### 3. Frontend setup

Open a new terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend starts at **http://localhost:5173**.

### 4. Open the app

Navigate to **http://localhost:5173** in your browser. Register as a Job Seeker or Recruiter to explore the platform.

## Project Structure

```
SipSetu/
├── backend/
│   ├── app.py                # Flask app factory & configuration
│   ├── models.py             # SQLAlchemy models (User, Applicant, Recruiter,
│   │                         #   Job, Resume, Skill, Ranking)
│   ├── routes.py             # API endpoints (auth, jobs, resumes, profiles)
│   ├── requirements.txt      # Python dependencies
│   ├── update_db.py          # Schema migration helper script
│   ├── test_login.py         # Manual login test script
│   ├── .env                  # Environment variables (gitignored)
│   └── .env.example          # Environment variable template
├── frontend/
│   ├── src/
│   │   ├── app/              # App entry point, router, shared components
│   │   ├── components/       # shadcn/ui components & layout wrappers
│   │   ├── pages/            # Route pages
│   │   │   ├── applicant/    # Dashboard, Resume, JobMatches, SkillGap, Profile
│   │   │   └── recruiter/    # Dashboard, PostJob, Candidates, Profile
│   │   ├── styles/           # Global CSS, Tailwind, theme, fonts
│   │   └── imports/          # Lottie animation assets
│   ├── index.html
│   ├── vite.config.ts
│   └── package.json
├── migrations/
│   └── 001_tables.sql        # PostgreSQL schema dump
├── tsconfig.json
└── README.md
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/auth/register` | Register a new user |
| POST | `/api/auth/login` | Log in and retrieve user info |
| GET | `/api/jobs` | List all job postings |
| POST | `/api/jobs` | Create a new job posting |
| POST | `/api/resumes` | Upload resume text for an applicant |
| GET | `/api/profile/<user_id>` | Get user profile details |
| PUT | `/api/profile/<user_id>` | Update user profile |
| GET | `/api/ml/ranking/status` | Inspect the trained ranking model and its metrics |
| POST | `/api/ml/ranking/train` | Train the ranking model from stored resume/job pairs |

## Known Limitations

This is an early-stage build (approx. 30-35% toward production readiness). Key limitations:

- **ML is bootstrapped from existing ranking scores** — The first training run learns from historical `matching_score` values stored in the database. Replace those with recruiter feedback or hire/shortlist labels for a production-grade model.
- **No JWT authentication** — Auth state is stored in `localStorage` (user_id, user_role) with no server-side token validation. This is not secure for production.
- **Hardcoded demo data** — Many pages (candidates, stats, skill gaps) use static mock arrays instead of live API data.
- **Resume file upload** — Resumes accept raw text only; multipart file upload is not implemented.
- **No pagination** — List endpoints return all records without pagination.
- **No test suite** — Only one manual test script exists (`test_login.py`).

## License

© 2026 SipSetu Inc.
