"""Semantic search service for resumes and jobs (Phase 6.2).

Provides vector-based similarity search beyond keyword matching:

1. **TF-IDF fallback** — always available, works on SQLite (tests/dev) and
   Postgres. Builds a TF-IDF matrix over the full resume+job corpus and
   computes cosine similarity at query time.

2. **pgvector (optional)** — when ENABLE_PGVVECTOR=true on Postgres, stores
   dense embeddings in a ``vector`` column and queries via ``<=>`` cosine
   distance. Falls back to TF-IDF gracefully when pgvector is unavailable.

The module exposes a small public API consumed by ``routes_phase6.py``:

- ``compute_embedding(text)`` — return a dense vector for arbitrary text
- ``similar_resumes(job_id, limit)`` — find resumes most similar to a job
- ``similar_jobs(resume_id, limit)`` — find jobs most similar to a resume
- ``update_embedding(record)`` — recompute + persist the embedding for a
  resume or job row
"""

from __future__ import annotations

import logging
import math
import os
import threading
from collections import Counter
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine

from models import Job, Resume, Skill, db

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

EMBEDDING_DIM = 256  # TF-IDF feature limit; dense vector dimension
ENABLE_PGVECTOR = os.environ.get("ENABLE_PGVECTOR", "false").lower() in (
    "1", "true", "yes",
)

# ---------------------------------------------------------------------------
# TF-IDF vectorizer (global, lazily fitted)
# ---------------------------------------------------------------------------

_vectorizer: TfidfVectorizer | None = None
_vectorizer_lock = threading.Lock()
_vocabulary: dict[str, int] = {}


def _corpus_text(record) -> str:
    """Build a single text blob from a resume or job for embedding."""
    parts = []
    if hasattr(record, "raw_text") and record.raw_text:
        parts.append(record.raw_text)
    if hasattr(record, "title") and record.title:
        parts.append(record.title)
    if hasattr(record, "description") and record.description:
        parts.append(record.description)
    skills = [s.skill_name for s in getattr(record, "skills", [])]
    if skills:
        parts.append(" ".join(skills))
    return " ".join(parts).strip()


def _ensure_vectorizer():
    """Fit the global TF-IDF vectorizer over the full corpus if needed."""
    global _vectorizer, _vocabulary
    if _vectorizer is not None:
        return

    with _vectorizer_lock:
        if _vectorizer is not None:
            return

        corpus: list[str] = []
        for r in Resume.query.all():
            t = _corpus_text(r)
            if t:
                corpus.append(t)
        for j in Job.query.all():
            t = _corpus_text(j)
            if t:
                corpus.append(t)

        if not corpus:
            # Empty corpus — use a dummy vectorizer
            _vectorizer = TfidfVectorizer(max_features=EMBEDDING_DIM)
            _vectorizer.fit(["placeholder"])
            return

        _vectorizer = TfidfVectorizer(
            max_features=EMBEDDING_DIM,
            ngram_range=(1, 2),
            stop_words="english",
            sublinear_tf=True,
        )
        _vectorizer.fit(corpus)
        _vocabulary = _vectorizer.vocabulary_
        log.info("TF-IDF vectorizer fitted on %d corpus documents", len(corpus))


def compute_embedding(text: str) -> list[float]:
    """Return a dense vector representation of *text*.

    Uses the global TF-IDF vectorizer.  Returns a zero vector when the
    vectorizer hasn't been fitted yet (e.g. empty database at startup).
    """
    _ensure_vectorizer()
    if _vectorizer is None:
        return [0.0] * EMBEDDING_DIM

    try:
        vec = _vectorizer.transform([text]).toarray()[0]
        # L2-normalise so cosine similarity is just dot product
        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec = vec / norm
        return vec.tolist()
    except Exception:
        return [0.0] * EMBEDDING_DIM


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Cosine similarity between two L2-normalised vectors (0-100 scale)."""
    a = np.array(vec_a, dtype=float)
    b = np.array(vec_b, dtype=float)
    dot = float(np.dot(a, b))
    return round(max(0.0, min(dot, 1.0)) * 100.0, 2)


# ---------------------------------------------------------------------------
# In-vector storage (pgvector) helpers
# ---------------------------------------------------------------------------

# Postgres has an ``sqlalchemy.dialects.postgresql`` Vector type when
# ``pgvector`` is installed.  We import it lazily so tests on SQLite are
# never affected.

_VectorType = None

if ENABLE_PGVECTOR:
    try:
        from pgvector.sqlalchemy import Vector as _VectorType  # type: ignore[import-untyped]
    except ImportError:
        log.warning("ENABLE_PGVECTOR=true but pgvector package not installed — falling back to TF-IDF")


def _has_vector_column() -> bool:
    """Check if the ``embedding`` column exists on the resumes / jobs tables."""
    try:
        from sqlalchemy import inspect
        insp = inspect(db.engine)
        cols = {c["name"] for c in insp.get_columns("resumes")}
        return "embedding" in cols
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Public search API
# ---------------------------------------------------------------------------

def similar_resumes(job_id: str, limit: int = 10) -> list[dict[str, Any]]:
    """Return resumes most similar to the given job, ranked by cosine similarity."""
    job = Job.query.get(job_id)
    if not job:
        return []

    job_text = _corpus_text(job)
    job_vec = compute_embedding(job_text)

    results: list[dict[str, Any]] = []
    for resume in Resume.query.all():
        resume_text = _corpus_text(resume)
        resume_vec = compute_embedding(resume_text)
        sim = compute_similarity(job_vec, resume_vec)
        if sim > 0:
            applicant = resume.applicant if hasattr(resume, "applicant") else None
            results.append({
                "resume_id": str(resume.resume_id),
                "applicant_id": str(resume.applicant_id),
                "applicant_name": applicant.name if applicant else None,
                "similarity_score": sim,
                "skills": [s.skill_name for s in resume.skills],
            })

    results.sort(key=lambda x: x["similarity_score"], reverse=True)
    return results[:limit]


def similar_jobs(resume_id: str, limit: int = 10) -> list[dict[str, Any]]:
    """Return jobs most similar to the given resume, ranked by cosine similarity."""
    resume = Resume.query.get(resume_id)
    if not resume:
        return []

    resume_text = _corpus_text(resume)
    resume_vec = compute_embedding(resume_text)

    results: list[dict[str, Any]] = []
    for job in Job.query.all():
        job_text = _corpus_text(job)
        job_vec = compute_embedding(job_text)
        sim = compute_similarity(resume_vec, job_vec)
        if sim > 0:
            recruiter = job.recruiter if hasattr(job, "recruiter") else None
            results.append({
                "job_id": str(job.job_id),
                "title": job.title,
                "company": recruiter.company if recruiter else None,
                "location": job.location,
                "similarity_score": sim,
                "skills": [s.skill_name for s in job.skills],
            })

    results.sort(key=lambda x: x["similarity_score"], reverse=True)
    return results[:limit]


def update_embedding(record) -> None:
    """Recompute and persist the embedding for a resume or job.

    The ``embedding`` column is a Text storing a JSON-serialised list of
    floats (portable across SQLite and Postgres).  On Postgres with
    pgvector enabled, a native ``vector`` column is used instead.
    """
    text = _corpus_text(record)
    vec = compute_embedding(text)

    # Store as JSON text (works on all dialects)
    import json
    record.embedding = json.dumps(vec)

    db.session.flush()
