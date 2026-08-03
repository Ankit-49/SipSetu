-- ============================================================================
-- SipSetu — Database Schema
-- ============================================================================
-- Run this against a fresh PostgreSQL database:
--   createdb sipsetu
--   psql -d sipsetu -f migrations/001_tables.sql
--
-- Requires the uuid-ossp extension (usually bundled with PostgreSQL).
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;

-- ============================================================================
-- USERS (base table; Applicant & Recruiter inherit via polymorphic FK)
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    user_id       UUID        DEFAULT uuid_generate_v4() NOT NULL PRIMARY KEY,
    email         VARCHAR(255)                            NOT NULL,
    name          VARCHAR(255),
    password_hash VARCHAR(255)                            NOT NULL,
    role          VARCHAR(20)                             NOT NULL
                    CHECK (role IN ('applicant', 'recruiter')),
    phone         VARCHAR(20),
    location      VARCHAR(255),
    profile_image TEXT,
    email_verified BOOLEAN   DEFAULT FALSE,
    created_at    TIMESTAMP  DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT users_email_key UNIQUE (email)
);

-- ============================================================================
-- APPLICANTS  (inherits users via user_id FK)
-- ============================================================================

CREATE TABLE IF NOT EXISTS applicants (
    user_id UUID NOT NULL PRIMARY KEY
        REFERENCES users(user_id) ON DELETE CASCADE
);

-- ============================================================================
-- RECRUITERS  (inherits users via user_id FK)
-- ============================================================================

CREATE TABLE IF NOT EXISTS recruiters (
    user_id UUID NOT NULL PRIMARY KEY
        REFERENCES users(user_id) ON DELETE CASCADE,
    company  VARCHAR(255),
    job_title VARCHAR(255)
);

-- ============================================================================
-- JOBS
-- ============================================================================

CREATE TABLE IF NOT EXISTS jobs (
    job_id           UUID        DEFAULT uuid_generate_v4() NOT NULL PRIMARY KEY,
    recruiter_id     UUID                                    NOT NULL
        REFERENCES recruiters(user_id) ON DELETE CASCADE,
    title            VARCHAR(255)                            NOT NULL,
    description      TEXT,
    location         VARCHAR(255),
    job_type         VARCHAR(50),    -- full-time, part-time, contract, etc.
    experience_level VARCHAR(50),    -- fresher, 1-3, 3-5, 5+, etc.
    salary_min       DOUBLE PRECISION,
    salary_max       DOUBLE PRECISION,
    created_at       TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SKILLS
-- ============================================================================

CREATE TABLE IF NOT EXISTS skills (
    skill_id   UUID        DEFAULT uuid_generate_v4() NOT NULL PRIMARY KEY,
    skill_name VARCHAR(100)                            NOT NULL,

    CONSTRAINT skills_skill_name_key UNIQUE (skill_name)
);

-- ============================================================================
-- JUNCTION: JOB <-> SKILLS  (many-to-many)
-- ============================================================================

CREATE TABLE IF NOT EXISTS job_skills (
    job_id   UUID NOT NULL
        REFERENCES jobs(job_id)   ON DELETE CASCADE,
    skill_id UUID NOT NULL
        REFERENCES skills(skill_id) ON DELETE CASCADE,

    PRIMARY KEY (job_id, skill_id)
);

-- ============================================================================
-- RESUMES
-- ============================================================================

CREATE TABLE IF NOT EXISTS resumes (
    resume_id    UUID        DEFAULT uuid_generate_v4() NOT NULL PRIMARY KEY,
    applicant_id UUID                                    NOT NULL
        REFERENCES applicants(user_id) ON DELETE CASCADE,
    raw_text     TEXT,
    file_path    VARCHAR(500),
    uploaded_at  TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- JUNCTION: RESUME <-> SKILLS  (many-to-many)
-- ============================================================================

CREATE TABLE IF NOT EXISTS resume_skills (
    resume_id UUID NOT NULL
        REFERENCES resumes(resume_id) ON DELETE CASCADE,
    skill_id  UUID NOT NULL
        REFERENCES skills(skill_id)   ON DELETE CASCADE,

    PRIMARY KEY (resume_id, skill_id)
);

-- ============================================================================
-- JOB APPLICATIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS job_applications (
    application_id UUID        DEFAULT uuid_generate_v4() NOT NULL PRIMARY KEY,
    job_id         UUID                                    NOT NULL
        REFERENCES jobs(job_id) ON DELETE CASCADE,
    applicant_id   UUID                                    NOT NULL
        REFERENCES applicants(user_id) ON DELETE CASCADE,
    applied_at     TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    status         VARCHAR(20) DEFAULT 'pending'           NOT NULL
        CHECK (status IN ('pending', 'shortlisted', 'rejected')),

    CONSTRAINT uq_job_applicant_application UNIQUE (job_id, applicant_id)
);

-- ============================================================================
-- RANKINGS
-- ============================================================================

CREATE TABLE IF NOT EXISTS rankings (
    ranking_id     UUID  DEFAULT uuid_generate_v4() NOT NULL PRIMARY KEY,
    job_id         UUID                               NOT NULL
        REFERENCES jobs(job_id)     ON DELETE CASCADE,
    resume_id      UUID                               NOT NULL
        REFERENCES resumes(resume_id) ON DELETE CASCADE,
    matching_score DOUBLE PRECISION,
    candidate_rank INTEGER
);

-- ============================================================================
-- EMAIL VERIFICATION TOKENS
-- ============================================================================

CREATE TABLE IF NOT EXISTS email_verification_tokens (
    token_id   UUID        DEFAULT uuid_generate_v4() NOT NULL PRIMARY KEY,
    user_id    UUID                                    NOT NULL
        REFERENCES users(user_id) ON DELETE CASCADE,
    token      VARCHAR(255)                            NOT NULL,
    expires_at TIMESTAMP                               NOT NULL,
    used       BOOLEAN     DEFAULT FALSE,
    created_at TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT email_verification_tokens_token_key UNIQUE (token)
);

CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_token
    ON email_verification_tokens(token);

-- ============================================================================
-- PASSWORD RESET TOKENS
-- ============================================================================

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    token_id   UUID        DEFAULT uuid_generate_v4() NOT NULL PRIMARY KEY,
    user_id    UUID                                    NOT NULL
        REFERENCES users(user_id) ON DELETE CASCADE,
    token      VARCHAR(255)                            NOT NULL,
    expires_at TIMESTAMP                               NOT NULL,
    used       BOOLEAN     DEFAULT FALSE,
    created_at TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT password_reset_tokens_token_key UNIQUE (token)
);

CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_token
    ON password_reset_tokens(token);

-- ============================================================================
-- SAVED JOBS
-- ============================================================================

CREATE TABLE IF NOT EXISTS saved_jobs (
    saved_job_id  UUID        DEFAULT uuid_generate_v4() NOT NULL PRIMARY KEY,
    applicant_id  UUID                                    NOT NULL
        REFERENCES applicants(user_id) ON DELETE CASCADE,
    job_id        UUID                                    NOT NULL
        REFERENCES jobs(job_id)       ON DELETE CASCADE,
    created_at    TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_applicant_saved_job UNIQUE (applicant_id, job_id)
);

-- ============================================================================
-- INTERVIEWS
-- ============================================================================

CREATE TABLE IF NOT EXISTS interviews (
    interview_id    UUID        DEFAULT uuid_generate_v4() NOT NULL PRIMARY KEY,
    job_id          UUID                                    NOT NULL
        REFERENCES jobs(job_id)       ON DELETE CASCADE,
    applicant_id    UUID                                    NOT NULL
        REFERENCES applicants(user_id) ON DELETE CASCADE,
    recruiter_id    UUID                                    NOT NULL
        REFERENCES recruiters(user_id) ON DELETE CASCADE,
    scheduled_at    TIMESTAMP                               NOT NULL,
    duration_minutes INTEGER     DEFAULT 60,
    status          VARCHAR(20) DEFAULT 'pending'           NOT NULL
        CHECK (status IN ('pending', 'confirmed', 'completed', 'cancelled', 'declined')),
    notes           TEXT,
    meeting_link    VARCHAR(500),
    created_at      TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SKILL PROGRESS  (applicant's learning tracker for skill gaps)
-- ============================================================================

CREATE TABLE IF NOT EXISTS skill_progress (
    progress_id  UUID        DEFAULT uuid_generate_v4() NOT NULL PRIMARY KEY,
    applicant_id UUID                                    NOT NULL
        REFERENCES applicants(user_id) ON DELETE CASCADE,
    skill_name   VARCHAR(100)                            NOT NULL,
    status       VARCHAR(20) DEFAULT 'learning'          NOT NULL
        CHECK (status IN ('learning', 'learned')),
    created_at   TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_applicant_skill_progress UNIQUE (applicant_id, skill_name)
);

-- ============================================================================
-- NOTIFICATIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS notifications (
    notification_id UUID        DEFAULT uuid_generate_v4() NOT NULL PRIMARY KEY,
    user_id         UUID                                    NOT NULL
        REFERENCES users(user_id) ON DELETE CASCADE,
    title           VARCHAR(255)                            NOT NULL,
    message         TEXT                                    NOT NULL,
    type            VARCHAR(50) DEFAULT 'info' NOT NULL
        CHECK (type IN ('info', 'success', 'warning', 'shortlisted', 'rejected')),
    is_read         BOOLEAN     DEFAULT FALSE,
    related_job_id  UUID
        REFERENCES jobs(job_id) ON DELETE SET NULL,
    created_at      TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
);
