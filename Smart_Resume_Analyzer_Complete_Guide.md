# Smart Resume Analyzer — Complete Project Guide

> **Team:** 5 members · CS 4th Semester · **Timeline:** 7–8 weeks  
> **Stack:** Python · Flask · spaCy · PostgreSQL (Supabase) · Bootstrap  
> **Document covers:** MVP description, PRD, roadmap, code structure, workflow, database design, and Supabase migration

---

## Table of Contents

1. [MVP Description](#1-mvp-description)
2. [Recommended Tech Stack](#2-recommended-tech-stack)
3. [Functional Requirements](#3-functional-requirements)
4. [Non-Functional Requirements](#4-non-functional-requirements)
5. [Out of Scope for MVP](#5-out-of-scope-for-mvp)
6. [Project Roadmap — 8 Weeks](#6-project-roadmap--8-weeks)
7. [Team Roles & Responsibilities](#7-team-roles--responsibilities)
8. [Risk Register](#8-risk-register)
9. [MVP Success Criteria](#9-mvp-success-criteria)
10. [System Architecture](#10-system-architecture)
11. [Application Workflow](#11-application-workflow)
12. [Database Design](#12-database-design)
13. [Code Structure](#13-code-structure)
14. [Supabase / PostgreSQL Migration](#14-supabase--postgresql-migration)
15. [Tips for a 4th Semester Team](#15-tips-for-a-4th-semester-team)

---

## 1. MVP Description

The **Smart Resume Analyzer** is a web-based application that bridges the gap between job applicants and recruiters using Natural Language Processing (NLP). It analyzes, scores, and improves resumes automatically. The platform serves two user groups from a single system — each seeing a view tailored to their needs.

> **Core value proposition:** Upload a resume → Get instant AI-driven feedback on skill match, formatting, and keyword gaps — for both the person submitting *and* the person reviewing it.

### 1.1 For Job Applicants

- Upload their resume (PDF or DOCX)
- Get a match score against a job description they paste in
- See which keywords are missing from their resume
- Receive actionable suggestions to improve their resume
- View a readability and formatting quality score

### 1.2 For Recruiters

- Upload multiple resumes at once for a job posting
- Get a ranked list of candidates by relevance score
- See a per-candidate skill match summary
- Filter/sort candidates by skills, experience level, or score
- Export the ranked list as a CSV report

### 1.3 Shared Features

- Simple login system (applicant or recruiter role)
- Dashboard to view past analyses and history
- Skill extraction from resume using NLP (spaCy library)
- Clean, beginner-friendly web interface

---

## 2. Recommended Tech Stack

Chosen for beginner-friendliness and availability of tutorials for 4th semester CS students.

| Layer | Technology | Why This? |
|---|---|---|
| Backend | Python + Flask | Simple routing, easy to learn, tons of tutorials |
| Frontend | HTML + CSS + Bootstrap | No React complexity; looks professional quickly |
| NLP Library | spaCy + NLTK | Pre-built models for skill/keyword extraction |
| PDF Parsing | PyMuPDF (fitz) | Reliable text extraction from PDF resumes |
| Database | PostgreSQL via Supabase | Hosted, shared across team, free tier available |
| Authentication | Flask-Login | Simple session-based auth, well documented |
| File Upload | Flask file upload + OS module | Built into Flask, no extra services needed |
| Report Export | Python `csv` module | Built-in, zero dependencies for CSV export |
| ORM | SQLAlchemy | Abstracts database — swap SQLite ↔ PostgreSQL without changing route code |

---

## 3. Functional Requirements

### 3.1 User Authentication

- User registration with role selection (Applicant / Recruiter)
- Login and logout with session management
- Basic password hashing using `werkzeug` (built into Flask)
- Redirect to role-specific dashboard after login

### 3.2 Resume Upload & Parsing

- Support PDF and DOCX file uploads (max 5MB)
- Extract text content using PyMuPDF and `python-docx`
- Parse sections: Contact Info, Education, Skills, Experience, Summary
- Store parsed resume data in the database linked to the user

### 3.3 Job Description Input

- Text area for applicant or recruiter to paste a job description
- Extract required skills/keywords from the JD automatically
- Store JD alongside the analysis result

### 3.4 Resume Scoring Engine

| Score Component | How It's Calculated |
|---|---|
| **Keyword Match Score** | % of JD keywords that appear in the resume |
| **Skill Gap Report** | List of JD keywords not found in the resume |
| **Experience Level** | Detected as junior/mid/senior based on years mentioned |
| **Format Score** | Checks section completeness, length, readability |
| **Overall Score** | Weighted composite: match×0.7 + format×0.3 (0–100) |

### 3.5 Applicant Dashboard

- Overall match score with color-coded indicator (red / yellow / green)
- Missing keywords as a tag list
- Improvement suggestions (pre-written, based on what's missing)
- History of past analyses

### 3.6 Recruiter Dashboard

- Upload multiple resumes in a batch for a single job description
- Ranked table of candidates with their scores
- Click any candidate to see their detailed skill breakdown
- Filter candidates by minimum score threshold
- Export ranked list to CSV

---

## 4. Non-Functional Requirements

### Performance
- Single resume analysis completes in under 10 seconds
- Batch upload of up to 20 resumes supported
- Page load times under 3 seconds

### Security
- Uploaded files stored in a non-public directory
- Input sanitization to prevent script injection
- Passwords stored as hashed values only (werkzeug)

### Usability
- No user manual required — interface is self-explanatory
- Works on Chrome/Firefox on desktop
- Mobile-responsive layout using Bootstrap grid

### Maintainability
- Modular codebase — separate files for auth, scoring, upload
- Inline code comments for every function
- README with setup instructions for all team members

---

## 5. Out of Scope for MVP

The following features are intentionally excluded to keep the project deliverable within 7–8 weeks:

- AI-generated resume rewriting
- LinkedIn / Indeed integration
- Email notifications
- Resume builder / editor
- Payment system
- Admin panel
- Mobile app
- Multi-language support
- ATS simulation
- Interview scheduling

> These can be added as future enhancements after the MVP is complete.

---

## 6. Project Roadmap — 8 Weeks

### Phase 1 — Setup & Foundation (Weeks 1–2)

| Week | Tasks | Owner |
|---|---|---|
| **Week 1** | Set up GitHub repo and agree on branching strategy | All members |
| | Install Python, Flask, spaCy, PostgreSQL environment on all machines | All members |
| | Design the database schema (Users, Resumes, Analyses, Jobs tables) | All members |
| | Build project folder structure (`routes/`, `models/`, `utils/`, `templates/`) | All members |
| | Create shared Trello or Notion board for task tracking | All members |
| **Week 2** | Build user registration and login pages (HTML forms) | M1: Auth Lead |
| | Implement Flask-Login authentication with hashed passwords | M1: Auth Lead |
| | Create SQLAlchemy models (User, Resume, JobDescription) | M2: DB Lead |
| | Role-based routing: redirect applicants vs recruiters to different dashboards | M1 + M2 |
| | Basic layout template with Bootstrap navbar | M2: Frontend |

### Phase 2 — Core Engine (Weeks 3–4)

| Week | Tasks | Owner |
|---|---|---|
| **Week 3** | Build file upload functionality (PDF + DOCX) with validation | M4: Upload Lead |
| | Implement resume text extraction using PyMuPDF and python-docx | M3: NLP Lead |
| | Parse extracted text into sections (Skills, Education, Experience) | M3: NLP Lead |
| | Store raw and parsed resume data in the database | M4: Upload Lead |
| | Write unit tests for the parser with 5 sample resumes | M3 + M4 |
| **Week 4** | Build keyword extraction function using spaCy NLP pipeline | M3: NLP Lead |
| | Implement keyword matching between resume and job description | M3: NLP Lead |
| | Calculate match score (keyword overlap percentage) | M5: Scoring Lead |
| | Detect missing keywords (JD keywords not found in resume) | M5: Scoring Lead |
| | Implement experience level detection (regex on year mentions) | M3: NLP Lead |
| | Calculate resume format score (section completeness, length) | M5: Scoring Lead |

### Phase 3 — Dashboards & UI (Weeks 5–6)

| Week | Tasks | Owner |
|---|---|---|
| **Week 5** | Build Applicant Dashboard: score display, missing keywords list | M2 + M5 |
| | Add color-coded score indicator (red <50, yellow 50–75, green >75) | M2: Frontend |
| | Show improvement suggestions based on gaps | M5: Scoring Lead |
| | Display resume analysis history for logged-in applicant | M2 + M5 |
| | Connect all applicant flows end-to-end and test | M5 |
| **Week 6** | Build Recruiter Dashboard: batch upload, candidate ranking table | M1: Recruiter UI |
| | Implement sortable/filterable candidate table | M1: Recruiter UI |
| | Build candidate detail view (skill breakdown per resume) | M1 |
| | Add minimum score filter | M1 |
| | Implement CSV export of ranked candidate list | M4: Export Lead |
| | Cross-browser testing and mobile responsiveness check | All members |

### Phase 4 — Testing & Polish (Weeks 7–8)

| Week | Tasks | Owner |
|---|---|---|
| **Week 7** | Full end-to-end testing with real resumes (10+ samples) | All members |
| | Fix bugs found in testing | All members |
| | Improve scoring accuracy based on test results | M3 + M5 |
| | Add basic error handling (bad file format, empty JD, etc.) | All members |
| | Peer review all code — merge to main branch | All members |
| **Week 8** | Final UI polish: spacing, fonts, color consistency | M2: Frontend |
| | Write project README and setup documentation | M2: Docs |
| | Prepare demo script and test data for presentation | All members |
| | Record a 3-minute demo video (optional but recommended) | All members |
| | Deploy on PythonAnywhere or Railway (free tier) | M4 |
| | Final presentation rehearsal and submission | All members |

---

## 7. Team Roles & Responsibilities

Each member leads a domain but everyone codes. Rotate code reviews every Friday.

| Member | Role Title | Key Responsibilities |
|---|---|---|
| **M1** | Auth & Recruiter UI | User auth, login/register pages, recruiter dashboard, batch upload |
| **M2** | Frontend & Docs | All HTML templates, Bootstrap layout, CSS, README documentation |
| **M3** | NLP & Parsing | spaCy pipeline, text extraction, keyword & skill extraction |
| **M4** | File Handling & DB | Upload validation, SQLAlchemy models, database migrations, CSV export |
| **M5** | Scoring Engine | Match score formula, gap detection, suggestions logic, applicant dashboard |

---

## 8. Risk Register

| Risk | Impact | Mitigation Plan |
|---|---|---|
| NLP accuracy is low for some resumes | High | Start with keyword matching first (simpler), tune spaCy model with sample data |
| Team member falls behind or drops out | High | Weekly standups every Monday; no module has a single point of failure |
| PDF parsing fails for scanned resumes | Medium | State "text-based PDFs only" in UI; add helpful error message |
| Scope creep (adding too many features) | High | PRD is the source of truth; new features go to backlog, not into MVP |
| Git conflicts during collaboration | Medium | Each member works on a separate feature branch; merge only on Fridays |
| Deployment issues in Week 8 | Medium | Test PythonAnywhere deployment by Week 6 so issues can be fixed early |
| Supabase free tier pauses after inactivity | Low | Restore from Supabase dashboard (takes ~30 seconds); won't affect active dev |

---

## 9. MVP Success Criteria

### Must Have (Pass/Fail)

- [ ] Applicant can upload a PDF resume and get a score
- [ ] Recruiter can upload 5+ resumes and see a ranked list
- [ ] Login system works with two roles (applicant / recruiter)
- [ ] Keyword gap report is visible on dashboard
- [ ] CSV export works for recruiter
- [ ] App runs without crashes during a 10-minute demo

### Nice to Have (Bonus)

- [ ] Score accuracy above 70% on 10 test resumes
- [ ] Mobile-responsive layout
- [ ] Deployed on PythonAnywhere (public URL)
- [ ] Demo video recorded
- [ ] Unit test coverage for scoring module
- [ ] Processing time under 5 seconds per resume

---

## 10. System Architecture

The system is organized in 4 horizontal layers. Each layer only talks to the layer directly below it — the frontend never touches the database directly, and the NLP utils never touch the routes.

```
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND  (Jinja2 HTML + Bootstrap)                            │
│  Login/Register │ Applicant Dashboard │ Recruiter Dashboard     │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP requests
┌──────────────────────────▼──────────────────────────────────────┐
│  BACKEND  (Flask Routes)                                        │
│  auth.py │ applicant.py │ recruiter.py │ export.py              │
└──────────────────────────┬──────────────────────────────────────┘
                           │ function calls
┌──────────────────────────▼──────────────────────────────────────┐
│  NLP ENGINE  (Python utils)                                     │
│  parser.py │ extractor.py │ scorer.py │ suggestions.py          │
└──────────────────────────┬──────────────────────────────────────┘
                           │ SQLAlchemy ORM
┌──────────────────────────▼──────────────────────────────────────┐
│  DATABASE  (PostgreSQL via Supabase)                            │
│  users │ resumes │ job_descriptions │ analyses                  │
└─────────────────────────────────────────────────────────────────┘
```

**Key design principle:** The NLP utils (`utils/`) are completely stateless — they are pure Python functions that take text in and return data out. They never touch the database. The Flask routes handle all database reading and writing. This separation makes testing and debugging much easier.

---

## 11. Application Workflow

Both the applicant and recruiter flows converge at the same NLP Scoring Engine (step 5). Write the scoring logic once — both user types benefit.

```
APPLICANT FLOW                          RECRUITER FLOW
──────────────                          ──────────────
① User logs in (role = applicant)       ① User logs in (role = recruiter)
         │                                       │
② Upload 1 resume + paste JD            ② Upload many resumes + paste JD
         │                                       │
③ Validate file (type, size)            ③ Validate all files (loop)
         │                                       │
④ Parse resume text                     ④ Parse each resume
   (PyMuPDF / python-docx)                 (same parser, loop)
         │                                       │
         └──────────────┬────────────────────────┘
                        │
              ⑤ NLP SCORING ENGINE (shared)
                 1. Extract keywords (spaCy)
                 2. Match vs JD keywords
                 3. Calculate scores + gap list
                        │
         ┌──────────────┴────────────────────────┐
         │                                       │
⑥ Save result to DB               ⑥ Save all results to DB
   (Analyses table)                   (bulk insert)
         │                                       │
⑦ Render Applicant Dashboard       ⑦ Render Recruiter Dashboard
   Score · gaps · suggestions          Ranked table · CSV export
         │                                       │
⑧ Session ends / logout            ⑧ Session ends / logout
```

---

## 12. Database Design

### Entity Relationship Overview

```
USERS ──< RESUMES ──< ANALYSES >── JOB_DESCRIPTIONS >── USERS
```

- One user can upload many resumes
- One user can create many job descriptions  
- One analysis always links one resume to one job description (the pivot table)

### Table Definitions (PostgreSQL / Supabase)

#### `users`

| Column | Type | Notes |
|---|---|---|
| `id` | `SERIAL PRIMARY KEY` | Auto-incrementing |
| `username` | `VARCHAR(80)` | Unique |
| `email` | `VARCHAR(120)` | Unique |
| `password_hash` | `VARCHAR(256)` | werkzeug hashed |
| `role` | `VARCHAR(20)` | `'applicant'` or `'recruiter'` |
| `created_at` | `TIMESTAMPTZ` | UTC, auto-set |

#### `resumes`

| Column | Type | Notes |
|---|---|---|
| `id` | `SERIAL PRIMARY KEY` | |
| `user_id` | `INTEGER` | FK → `users.id` |
| `file_name` | `VARCHAR(255)` | Original filename |
| `file_path` | `VARCHAR(512)` | Server-side storage path |
| `raw_text` | `TEXT` | Extracted full text |
| `experience_level` | `VARCHAR(20)` | `'junior'`, `'mid'`, `'senior'` |
| `uploaded_at` | `TIMESTAMPTZ` | UTC, auto-set |

#### `job_descriptions`

| Column | Type | Notes |
|---|---|---|
| `id` | `SERIAL PRIMARY KEY` | |
| `user_id` | `INTEGER` | FK → `users.id` |
| `job_title` | `VARCHAR(255)` | |
| `jd_text` | `TEXT` | Full pasted JD |
| `extracted_keywords` | `JSONB` | Python list stored natively |
| `created_at` | `TIMESTAMPTZ` | UTC, auto-set |

#### `analyses`

| Column | Type | Notes |
|---|---|---|
| `id` | `SERIAL PRIMARY KEY` | |
| `resume_id` | `INTEGER` | FK → `resumes.id` |
| `jd_id` | `INTEGER` | FK → `job_descriptions.id` |
| `match_score` | `NUMERIC(5,2)` | e.g. `78.50` |
| `format_score` | `NUMERIC(5,2)` | |
| `overall_score` | `NUMERIC(5,2)` | Weighted composite |
| `missing_keywords` | `JSONB` | List of missing skills |
| `matched_keywords` | `JSONB` | List of matched skills |
| `suggestions` | `JSONB` | List of tip strings |
| `analyzed_at` | `TIMESTAMPTZ` | UTC, auto-set |

> **Why `JSONB` over `TEXT`?** With PostgreSQL's `JSONB` type, you assign Python lists directly — `analysis.missing_keywords = ["Python", "SQL"]` — and SQLAlchemy handles serialization. No more `json.dumps()` before saving and `json.loads()` after reading. You can also query inside JSONB fields natively.

> **Why `NUMERIC(5,2)` over `Float`?** Exact decimal precision. A score of `78.50` stays `78.50`, not `78.49999999`.

---

## 13. Code Structure

### Recommended Folder Layout

```
smart-resume-analyzer/
│
├── run.py                      # Entry point — creates Flask app and starts server
├── config.py                   # Secret key, DB URI, upload folder (loads from .env)
├── .env                        # Credentials — NEVER commit to GitHub
├── .gitignore                  # Includes .env, uploads/, __pycache__/, *.db
├── requirements.txt            # All pip dependencies
│
├── uploads/                    # Saved resume files — gitignored, not in repo
│
└── app/
    ├── __init__.py             # App factory: create_app(), registers blueprints + DB
    │
    ├── models/
    │   ├── user.py             # User model: fields, set_password(), check_password()
    │   ├── resume.py           # Resume model: file path, raw text, experience level
    │   ├── job_description.py  # JD model: text, JSONB extracted keywords
    │   └── analysis.py        # Analysis model: all scores, JSONB keyword lists
    │
    ├── routes/
    │   ├── auth.py             # /register, /login, /logout
    │   ├── applicant.py        # /dashboard, /upload, /analyze, /history
    │   └── recruiter.py        # /batch-upload, /rank, /candidate/<id>, /export-csv
    │
    ├── utils/
    │   ├── parser.py           # extract_text(file_path) → str
    │   ├── extractor.py        # extract_keywords(), extract_skills(), detect_xp_level()
    │   ├── scorer.py           # calculate_match(), get_missing(), score_format(), overall_score()
    │   └── suggestions.py      # generate_suggestions(missing_kw, score) → list[str]
    │
    └── templates/
        ├── base.html           # Navbar, Bootstrap CDN, flash message block
        ├── auth/
        │   ├── login.html
        │   └── register.html   # Form with role radio button
        ├── applicant/
        │   ├── dashboard.html  # Score bar, missing keyword tags, suggestions, history
        │   └── upload.html     # Resume file upload + JD paste textarea
        └── recruiter/
            ├── dashboard.html  # Sortable candidate table, filter input, export button
            └── candidate.html  # Individual candidate skill breakdown
```

### File-by-File Responsibility

#### `run.py`
Entry point. Imports `create_app()` from `app/__init__.py` and starts the dev server.
```python
from app import create_app
app = create_app()
if __name__ == '__main__':
    app.run(debug=True)
```

#### `config.py`
Loads environment variables from `.env`. Contains all configuration constants.
```python
import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB
```

#### `app/__init__.py`
Flask app factory. Creates the app, initializes extensions, registers blueprints, and creates database tables on first run.
```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from app.routes.auth import auth_bp
    from app.routes.applicant import applicant_bp
    from app.routes.recruiter import recruiter_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(applicant_bp)
    app.register_blueprint(recruiter_bp)

    with app.app_context():
        db.create_all()  # creates all tables in Supabase on first run

    return app
```

#### `utils/parser.py`
Pure function — takes a file path, returns extracted plain text. No database access.
```python
import fitz  # PyMuPDF
import docx

def extract_text(file_path: str) -> str:
    if file_path.endswith('.pdf'):
        doc = fitz.open(file_path)
        return ' '.join(page.get_text() for page in doc)
    elif file_path.endswith('.docx'):
        doc = docx.Document(file_path)
        return ' '.join(para.text for para in doc.paragraphs)
    else:
        raise ValueError('Unsupported file type')
```

#### `utils/extractor.py`
Runs spaCy NLP pipeline to extract keywords and detect experience level.
```python
import spacy
import re

nlp = spacy.load('en_core_web_sm')

def extract_keywords(text: str) -> list[str]:
    doc = nlp(text.lower())
    return list({chunk.text for chunk in doc.noun_chunks if len(chunk.text) > 2})

def extract_skills(text: str, skill_list: list[str]) -> list[str]:
    text_lower = text.lower()
    return [skill for skill in skill_list if skill.lower() in text_lower]

def detect_experience_level(text: str) -> str:
    years = re.findall(r'(\d+)\+?\s+years?', text.lower())
    if years:
        max_years = max(int(y) for y in years)
        if max_years >= 5: return 'senior'
        if max_years >= 2: return 'mid'
    return 'junior'
```

#### `utils/scorer.py`
Core scoring logic. All pure functions — no database, no Flask imports.
```python
def calculate_match(resume_kw: list, jd_kw: list) -> float:
    if not jd_kw:
        return 0.0
    matched = set(resume_kw) & set(jd_kw)
    return round(len(matched) / len(jd_kw) * 100, 2)

def get_missing(resume_kw: list, jd_kw: list) -> list:
    return list(set(jd_kw) - set(resume_kw))

def score_format(text: str) -> float:
    score = 0
    sections = ['experience', 'education', 'skills', 'summary', 'contact']
    for section in sections:
        if section in text.lower():
            score += 20
    return min(score, 100)

def overall_score(match: float, fmt: float) -> float:
    return round(match * 0.7 + fmt * 0.3, 2)
```

#### `utils/suggestions.py`
Maps missing keywords to human-readable improvement tips.
```python
KEYWORD_TIPS = {
    'python': 'Add Python projects to your experience section or list it under skills.',
    'sql': 'Mention any database work or SQL queries you have written.',
    'git': 'Add version control experience — even personal GitHub projects count.',
    # ... extend this dict with more keywords
}

def generate_suggestions(missing_kw: list, score: float) -> list[str]:
    tips = [KEYWORD_TIPS[kw] for kw in missing_kw if kw in KEYWORD_TIPS]
    if score < 50:
        tips.append('Your overall match is low — try tailoring this resume specifically for this job.')
    if not tips:
        tips.append('Good match! Consider quantifying your achievements with numbers.')
    return tips
```

#### Route files

**`routes/auth.py`** — handles `/register`, `/login`, `/logout`

**`routes/applicant.py`** — key endpoints:
- `POST /upload` — validate file, save to disk, call `extract_text()`, store `Resume` in DB
- `POST /analyze` — call `scorer.py` functions, store `Analysis`, redirect to dashboard
- `GET /dashboard` — query latest `Analysis` for current user, render template
- `GET /history` — list all past analyses for this user

**`routes/recruiter.py`** — key endpoints:
- `POST /batch-upload` — loop over uploaded files, parse and score each, bulk insert
- `GET /rank` — fetch all analyses for a JD, sort by `overall_score DESC`, render table
- `GET /candidate/<id>` — show one candidate's full breakdown
- `GET /export-csv` — stream CSV download using Python's built-in `csv` module

---

## 14. Supabase / PostgreSQL Migration

### What Changes vs What Stays the Same

| File | Status | What to do |
|---|---|---|
| `requirements.txt` | **Change** | Add `psycopg2-binary` and `python-dotenv` |
| `config.py` | **Change** | Load `DATABASE_URL` from `.env` instead of hardcoded SQLite path |
| `models/analysis.py` | **Change** | Use `JSONB` type for keyword lists, `NUMERIC` for scores |
| `.env` | **New** | Create this file with Supabase connection string — never commit |
| `.gitignore` | **Change** | Add `.env` to gitignore immediately |
| `routes/auth.py` | No change | SQLAlchemy abstracts the database |
| `routes/applicant.py` | No change | |
| `routes/recruiter.py` | No change | |
| `utils/` (all files) | No change | Pure Python functions, no DB awareness |
| `templates/` (all HTML) | No change | |

### Setting Up Supabase

1. Go to [supabase.com](https://supabase.com) and create a free account
2. Create a new project (choose a region close to Nepal — Singapore is closest)
3. Go to **Settings → Database → Connection String → URI**
4. Copy the connection string — it looks like: `postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres`
5. Paste it into your `.env` file

### Environment File

```bash
# .env — share this privately with teammates, NEVER commit to GitHub
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
SECRET_KEY=replace-this-with-a-long-random-string-like-abc123xyz789
UPLOAD_FOLDER=uploads
```

### Updated `requirements.txt`

```
flask==3.0.0
flask-login==0.6.3
flask-sqlalchemy==3.1.1
psycopg2-binary==2.9.9
python-dotenv==1.0.0
spacy==3.7.2
pymupdf==1.23.8
python-docx==1.1.0
werkzeug==3.0.1
```

### Updated Analysis Model (JSONB)

```python
from app import db
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timezone

class Analysis(db.Model):
    __tablename__ = 'analyses'

    id            = db.Column(db.Integer, primary_key=True)
    resume_id     = db.Column(db.Integer, db.ForeignKey('resumes.id'), nullable=False)
    jd_id         = db.Column(db.Integer, db.ForeignKey('job_descriptions.id'), nullable=False)
    match_score   = db.Column(db.Numeric(5, 2))
    format_score  = db.Column(db.Numeric(5, 2))
    overall_score = db.Column(db.Numeric(5, 2))

    # JSONB: store Python lists directly — no json.dumps() needed
    missing_keywords  = db.Column(JSONB)
    matched_keywords  = db.Column(JSONB)
    suggestions       = db.Column(JSONB)

    analyzed_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
```

### One-Time Setup Commands

```bash
# 1. Install new dependencies
pip install psycopg2-binary python-dotenv flask-sqlalchemy flask-login

# 2. Create uploads folder (gitignored)
mkdir uploads

# 3. Download spaCy language model
python -m spacy download en_core_web_sm

# 4. Run app once to auto-create all tables in Supabase
python run.py

# 5. Verify: open Supabase dashboard → Table Editor
#    You should see: users, resumes, job_descriptions, analyses
```

### Team Collaboration with Supabase

> **Important:** Only ONE person runs `db.create_all()` the first time to create the tables. After that, all 5 members connect to the same Supabase project using the same `.env` credentials — share it over WhatsApp or Discord privately, never over GitHub.

Each team member's local setup:
```
1. Clone the repo from GitHub
2. Create a .env file in the project root
3. Paste in the shared DATABASE_URL and SECRET_KEY
4. pip install -r requirements.txt
5. python run.py  ← connects to the shared Supabase DB
```

### Supabase Free Tier Notes

- Database **pauses after 1 week of inactivity** — restore from the Supabase dashboard (takes ~30 seconds)
- Free tier allows: 500MB database, 1GB file storage, unlimited API requests
- This won't affect you during active development weeks
- For final deployment, consider upgrading to the Pro tier ($25/month) or deploying on Railway/Render instead

---

## 15. Tips for a 4th Semester Team

### Getting Started Fast

Don't spend Week 1 learning spaCy. Build the login page and file upload first — visible progress keeps the team motivated. Add NLP in Week 3 once the skeleton is working.

### First Install Commands

```bash
pip install flask flask-login flask-sqlalchemy spacy pymupdf python-docx werkzeug psycopg2-binary python-dotenv fpdf2
python -m spacy download en_core_web_sm
```

### Git Branching Strategy

```
main          ← stable, working code only
  └── dev     ← integration branch, merge here daily
        ├── feature/auth-m1
        ├── feature/nlp-m3
        ├── feature/scoring-m5
        ├── feature/upload-m4
        └── feature/frontend-m2
```

Never push directly to `main`. Every Friday, merge `dev` → `main` after team review.

### 5 Common Mistakes to Avoid

1. **Don't use global variables for user session data** — use Flask-Login's `current_user`
2. **Don't commit the `/uploads` folder to GitHub** — add it to `.gitignore` on day one
3. **Don't build everything in one file (`app.py`)** — split into modules from day one
4. **Don't skip the database schema design** — changing it midway costs hours of debugging
5. **Don't assume all PDFs are readable** — always handle parsing exceptions with `try/except`

### Debugging Checklist

When something isn't working, check in this order:
1. Is the `.env` file present and has the correct `DATABASE_URL`?
2. Is the virtual environment activated? (`source venv/bin/activate`)
3. Are all pip packages installed? (`pip install -r requirements.txt`)
4. Did `db.create_all()` run? (check Supabase Table Editor)
5. Is the spaCy model downloaded? (`python -m spacy download en_core_web_sm`)
6. Check Flask's terminal output — error messages are printed there

### Score Weighting Formula

```python
# In utils/scorer.py
WEIGHTS = {
    'keyword_match': 0.70,   # Most important — did you use the right words?
    'format_score':  0.30,   # Secondary — is the resume well-structured?
}

def overall_score(match: float, fmt: float) -> float:
    return round(match * WEIGHTS['keyword_match'] + fmt * WEIGHTS['format_score'], 2)
```

Adjust the weights based on testing. If format matters more for your use case, try `0.60 / 0.40`.

---

## Quick Reference Card

| What you need | Where to look |
|---|---|
| Add a new page | Create `templates/new_page.html`, add route in appropriate `routes/*.py` |
| Change scoring logic | Edit `utils/scorer.py` only — nothing else needs to change |
| Add a new keyword tip | Add entry to `KEYWORD_TIPS` dict in `utils/suggestions.py` |
| Add a database column | Edit the model in `models/`, then run `db.create_all()` or use Flask-Migrate |
| Debug a 500 error | Check the Flask terminal output — full traceback is printed there |
| Connect to DB in Supabase UI | supabase.com → your project → Table Editor |
| Check who is logged in | `from flask_login import current_user` then use `current_user.role` |
| Protect a route (login required) | Add `@login_required` decorator above the route function |

---

*Document compiled from project planning session — Smart Resume Analyzer, CS 4th Semester Team of 5*
