"""Enhanced candidate ranking model (v2).

Improves on the retired v1 model in four ways:

1. **Richer features (17)** — adds IDF-weighted skill specificity (rare
   skills matter more than generic ones), title similarity, seniority and
   education signals, and keyword density on top of the v1 coverage /
   experience / content features.

2. **Gradient boosting** — HistGradientBoostingRegressor (fast, handles
   non-linearities and missing values natively) replaces RandomForest.
   Grouped train/test split by job_id prevents leakage where candidates
   for the same job appear in both sets.

3. **Recruiter-feedback labels** — training targets are derived from the
   deterministic heuristic score, then *pulled* by real recruiter
   decisions: shortlisted applications get boosted toward a high label,
   rejected ones toward a low label. This teaches the model recruiter
   preferences instead of just re-learning the heuristic.

4. **Safe blending** — predictions are `alpha * model + (1-alpha) *
   heuristic`, where alpha ramps up with training rows. Small/weak
   models stay close to the deterministic heuristic; mature models get
   more influence. Scores stay on the 0-100 scale and never degrade
   below the heuristic on tiny datasets.
"""

from __future__ import annotations

import re
import threading
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from math import log, sqrt
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import GroupShuffleSplit

from models import Job, JobApplication, Ranking, Resume

MODEL_DIR = Path(__file__).resolve().parent / "ml_artifacts"
MODEL_PATH = MODEL_DIR / "candidate_ranker_v2.joblib"
MODEL_VERSION = "candidate-ranker-v2"
RELEVANCE_THRESHOLD = 60.0
MIN_TRAINING_ROWS = 15
MIN_DISTINCT_LABELS = 2
MAX_ALPHA = 0.8
ALPHA_RAMP_ROWS = 80.0  # alpha reaches MAX_ALPHA at this many training rows

# Seniority / education keywords used as soft signals.
SENIORITY_KEYWORDS = [
    "senior", "lead", "principal", "staff", "manager", "architect",
    "head of", "director", "vp", "vice president", "tech lead", "team lead",
]
EDUCATION_KEYWORDS = [
    "b.s.", "b.a.", "m.s.", "m.a.", "ph.d.", "phd", "bachelor", "master",
    "b.tech", "m.tech", "b.e.", "m.e.", "bsc", "msc", "bca", "mca",
    "degree", "university", "college",
]

# Human-readable labels + descriptions for the 17 features, used by the
# per-candidate explanation endpoint.
FEATURE_LABELS: dict[str, tuple[str, str]] = {
    "skills_coverage": ("Skill coverage", "Share of the job's required skills present on the resume"),
    "skills_jaccard": ("Skill similarity", "Overlap between resume and job skills (Jaccard index)"),
    "matched_skill_count": ("Matched skills", "Number of required skills the candidate has"),
    "missing_skill_count": ("Missing skills", "Required skills the candidate lacks"),
    "job_skill_count": ("Job skill count", "Total number of skills the job requires"),
    "resume_skill_count": ("Resume skill count", "Number of skills extracted from the resume"),
    "skill_specificity": ("Skill specificity", "Rare/technical skills weigh more than generic ones (IDF)"),
    "experience_years": ("Experience years", "Years of experience detected on the resume"),
    "target_experience_years": ("Target experience", "Years of experience the job asks for"),
    "experience_gap": ("Experience gap", "Absolute difference between candidate and target experience"),
    "experience_score": ("Experience fit", "How well the candidate's experience matches the job requirement"),
    "content_similarity": ("Content similarity", "Semantic overlap between resume and job description text"),
    "title_similarity": ("Title match", "Job-title keywords that appear in the resume"),
    "keyword_density": ("Keyword density", "Job-description keywords found in the resume"),
    "resume_word_count": ("Resume length", "Total word count of the resume text"),
    "seniority_hits": ("Seniority signals", "Senior/lead/manager keywords found in the resume"),
    "education_hits": ("Education signals", "Degree/university keywords found in the resume"),
}

_train_lock = threading.Lock()


@dataclass
class RankingBundle:
    model: Any
    vectorizer: TfidfVectorizer | None
    feature_names: list[str]
    trained_at: str
    metrics: dict[str, float]
    row_count: int
    job_count: int
    alpha: float
    n_features: int
    feature_means: list[float] | None = None


# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------


def _clean_text(value: str | None) -> str:
    return (value or "").strip()


def _skill_names(record) -> list[str]:
    return [s.skill_name.lower() for s in getattr(record, "skills", [])]


# IDF weights are derived from the jobs table, which changes only when
# jobs/skills change. Cache them and invalidate on training, so the hot
# scoring loop doesn't re-query all jobs for every (resume, job) pair.
_idf_cache: dict[str, float] | None = None
_idf_cache_jobs: int = -1


def _invalidate_idf_cache() -> None:
    global _idf_cache, _idf_cache_jobs
    _idf_cache = None
    _idf_cache_jobs = -1


def _job_text(job: Job) -> str:
    return " ".join(filter(None, [job.title or "", job.description or "", " ".join(_skill_names(job))])).strip()


def _resume_text(resume: Resume) -> str:
    return _clean_text(resume.raw_text) or " ".join(_skill_names(resume))


def _extract_experience_years(text: str | None) -> float | None:
    from routes_common import extract_experience_years as _rc_extract

    return _rc_extract(text)


def _target_experience_years(job: Job) -> float | None:
    from routes_common import experience_level_to_years as _rc_level_to_years

    return _rc_level_to_years(job.experience_level)


def _experience_score(candidate_years, target_years) -> float:
    from routes_common import calculate_experience_score as _rc_exp_score

    return _rc_exp_score(candidate_years, target_years)


def _skill_idf_weights() -> dict[str, float]:
    """IDF weights for skills across all jobs (cached).

    A skill required by few jobs (e.g. kubernetes) is more discriminative
    than one required by nearly everything (e.g. communication), so it
    should contribute more to the specificity score.
    """
    global _idf_cache, _idf_cache_jobs
    job_count = Job.query.count()
    if _idf_cache is not None and _idf_cache_jobs == job_count:
        return _idf_cache
    jobs = Job.query.all()
    n_jobs = max(len(jobs), 1)
    counts: Counter[str] = Counter()
    for job in jobs:
        for s in set(_skill_names(job)):
            counts[s] += 1
    _idf_cache = {s: log((n_jobs + 1) / (1.0 + c)) + 1.0 for s, c in counts.items()}
    _idf_cache_jobs = job_count
    return _idf_cache


def _specificity_score(resume_skills: list[str], job_skills: list[str], idf: dict[str, float]) -> float:
    """0-100 score weighting matched skills by rarity (IDF)."""
    if not job_skills:
        return 0.0
    job_idf = sum(idf.get(s, 1.0) for s in set(job_skills))
    if job_idf <= 0:
        return 0.0
    matched_idf = sum(idf.get(s, 1.0) for s in set(resume_skills) & set(job_skills))
    return round(min((matched_idf / job_idf) * 100.0, 100.0), 2)


def _title_similarity(resume_text: str, job: Job) -> float:
    """How many meaningful words from the job title appear in the resume."""
    title_words = [w for w in re.findall(r"[a-z0-9]+", (job.title or "").lower()) if len(w) > 2]
    if not title_words:
        return 0.0
    resume_lower = resume_text.lower()
    hits = sum(1 for w in set(title_words) if w in resume_lower)
    return round((hits / len(set(title_words))) * 100.0, 2)


def _keyword_density(resume_text: str, job: Job) -> float:
    """Fraction of the job description's distinct keywords in the resume."""
    desc = _clean_text(job.description)
    if not desc:
        return 0.0
    job_words = set(re.findall(r"[a-z0-9]{3,}", desc.lower()))
    if not job_words:
        return 0.0
    resume_lower = resume_text.lower()
    hits = sum(1 for w in job_words if w in resume_lower)
    return round(min((hits / len(job_words)) * 100.0, 100.0), 2)


def _keyword_hits(text: str, keywords: list[str]) -> int:
    lower = text.lower()
    return sum(1 for k in keywords if k in lower)


def build_feature_dict(
    resume: Resume,
    job: Job,
    vectorizer: TfidfVectorizer | None,
    idf: dict[str, float],
) -> dict[str, float]:
    resume_skills = _skill_names(resume)
    job_skills = _skill_names(job)

    resume_set = set(resume_skills)
    job_set = set(job_skills)
    matched = resume_set & job_set
    union = resume_set | job_set

    resume_text = _resume_text(resume)
    job_text = _job_text(job)

    content_sim = 0.0
    if vectorizer and resume_text and job_text:
        try:
            matrix = vectorizer.transform([resume_text, job_text]).toarray()
            content_sim = float(cosine_similarity(matrix[0:1], matrix[1:2])[0, 0]) * 100
        except Exception:
            pass

    candidate_years = _extract_experience_years(resume_text)
    target_years = _target_experience_years(job)

    return {
        "skills_coverage": round((len(matched) / len(job_set)) * 100.0, 2) if job_set else 0.0,
        "skills_jaccard": round((len(matched) / len(union)) * 100.0, 2) if union else 0.0,
        "matched_skill_count": float(len(matched)),
        "missing_skill_count": float(len(job_set - resume_set)),
        "job_skill_count": float(len(job_set)),
        "resume_skill_count": float(len(resume_set)),
        "skill_specificity": _specificity_score(resume_skills, job_skills, idf),
        "experience_years": float(candidate_years or 0.0),
        "target_experience_years": float(target_years or 0.0),
        "experience_gap": float(abs((candidate_years or 0.0) - (target_years or 0.0))) if target_years is not None else float(candidate_years or 0.0),
        "experience_score": float(_experience_score(candidate_years, target_years)),
        "content_similarity": float(content_sim),
        "title_similarity": _title_similarity(resume_text, job),
        "keyword_density": _keyword_density(resume_text, job),
        "resume_word_count": float(len(resume_text.split())),
        "seniority_hits": float(_keyword_hits(resume_text, SENIORITY_KEYWORDS)),
        "education_hits": float(_keyword_hits(resume_text, EDUCATION_KEYWORDS)),
    }


def _feature_order() -> list[str]:
    return [
        "skills_coverage",
        "skills_jaccard",
        "matched_skill_count",
        "missing_skill_count",
        "job_skill_count",
        "resume_skill_count",
        "skill_specificity",
        "experience_years",
        "target_experience_years",
        "experience_gap",
        "experience_score",
        "content_similarity",
        "title_similarity",
        "keyword_density",
        "resume_word_count",
        "seniority_hits",
        "education_hits",
    ]


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------


def _training_label(ranking: Ranking) -> float:
    """Heuristic score pulled toward recruiter decisions.

    shortlisted → push toward ≥85, rejected → push toward ≤25.
    pending / unknown → keep the heuristic score as-is.
    """
    base = float(ranking.matching_score or 0.0)

    application = (
        JobApplication.query.filter_by(
            job_id=ranking.job_id, applicant_id=ranking.resume.applicant_id
        ).first()
        if ranking.resume and ranking.job
        else None
    )
    status = application.status if application else None

    if status == "shortlisted":
        return round(max(base, 85.0), 2)
    if status == "rejected":
        return round(min(base, 25.0), 2)
    return base


def _ndcg_at_k(y_true: np.ndarray, y_pred: np.ndarray, k: int = 5) -> float:
    if y_true.size == 0:
        return 0.0
    order = np.argsort(y_pred)[::-1][:k]
    ideal_order = np.argsort(y_true)[::-1][:k]

    def _dcg(values: np.ndarray) -> float:
        total = 0.0
        for idx, value in enumerate(values):
            total += float(value) / log(idx + 2)
        return total

    dcg = _dcg(y_true[order])
    idcg = _dcg(y_true[ideal_order])
    return dcg / idcg if idcg > 0 else 0.0


def _precision_recall_mrr_at_k(y_true: np.ndarray, y_pred: np.ndarray, k: int = 5):
    if y_true.size == 0:
        return 0.0, 0.0, 0.0
    order = np.argsort(y_pred)[::-1][:k]
    relevance = y_true[order] >= RELEVANCE_THRESHOLD
    precision = float(np.sum(relevance)) / min(k, len(y_true))
    recall = float(np.sum(relevance)) / max(1, int(np.sum(y_true >= RELEVANCE_THRESHOLD)))
    reciprocal_rank = 0.0
    for idx, is_rel in enumerate(relevance, start=1):
        if is_rel:
            reciprocal_rank = 1.0 / idx
            break
    return precision, recall, reciprocal_rank


def _grouped_ranking_metrics(group_ids: list[str], y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    grouped: dict[str, list[int]] = {}
    for index, gid in enumerate(group_ids):
        grouped.setdefault(gid, []).append(index)

    ndcg, prec, rec, mrr = [], [], [], []
    for indices in grouped.values():
        gt = y_true[indices]
        if gt.size < 2:
            continue
        pr = y_pred[indices]
        k = min(5, gt.size)
        ndcg.append(_ndcg_at_k(gt, pr, k))
        p, r, mr = _precision_recall_mrr_at_k(gt, pr, k)
        prec.append(p)
        rec.append(r)
        mrr.append(mr)

    return {
        "ndcg_at_5": round(float(np.mean(ndcg)) if ndcg else 0.0, 4),
        "precision_at_5": round(float(np.mean(prec)) if prec else 0.0, 4),
        "recall_at_5": round(float(np.mean(rec)) if rec else 0.0, 4),
        "mrr_at_5": round(float(np.mean(mrr)) if mrr else 0.0, 4),
    }


def train_ranking_model(random_state: int = 42) -> dict[str, Any]:
    with _train_lock:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)

        rankings = (
            Ranking.query.filter(Ranking.matching_score.isnot(None))
            .filter(Ranking.resume.has())
            .filter(Ranking.job.has())
            .all()
        )
        if len(rankings) < MIN_TRAINING_ROWS:
            return {
                "trained": False,
                "message": f"Not enough ranked resume/job pairs to train. Need at least {MIN_TRAINING_ROWS}, got {len(rankings)}.",
                "row_count": len(rankings),
            }

        idf = _skill_idf_weights()

        # Fit a global TF-IDF vectorizer over the whole corpus (used for
        # content similarity at both train and predict time).
        corpus = []
        for ranking in rankings:
            rt = _resume_text(ranking.resume)
            jt = _job_text(ranking.job)
            if rt:
                corpus.append(rt)
            if jt:
                corpus.append(jt)
        vectorizer = None
        if len(corpus) >= 2:
            vectorizer = TfidfVectorizer(max_features=2500, ngram_range=(1, 2), stop_words="english")
            vectorizer.fit(corpus)

        feature_names = _feature_order()
        rows = [build_feature_dict(r.resume, r.job, vectorizer, idf) for r in rankings]
        X = np.array([[row[name] for name in feature_names] for row in rows], dtype=float)
        y = np.array([_training_label(r) for r in rankings], dtype=float)
        groups = [str(r.job_id) for r in rankings]

        unique_labels = len(np.unique(y))
        if unique_labels < MIN_DISTINCT_LABELS:
            return {
                "trained": False,
                "message": "Training targets need at least two distinct values.",
                "row_count": len(rankings),
            }

        # Grouped split: candidates from the same job stay together so we
        # measure generalization to *unseen jobs* rather than memorization.
        splitter = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=random_state)
        try:
            train_idx, test_idx = next(splitter.split(X, y, groups))
            evaluation = "performed"
        except ValueError:
            train_idx, test_idx = np.arange(len(X)), np.arange(0)
            evaluation = "skipped"

        X_train, y_train = X[train_idx], y[train_idx]
        X_test, y_test = X[test_idx], y[test_idx]

        # Adapt to dataset size: tiny datasets get shallow leaves and no
        # early stopping (a 2-sample validation split is too noisy).
        n_train = len(X_train)
        model = HistGradientBoostingRegressor(
            max_iter=400,
            learning_rate=0.05,
            max_depth=6,
            min_samples_leaf=max(2, n_train // 10),
            l2_regularization=1.0,
            early_stopping=n_train >= 30,
            validation_fraction=0.15,
            n_iter_no_change=25,
            random_state=random_state,
        )
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test) if len(X_test) else y_train
        metrics = {
            "rmse": round(sqrt(mean_squared_error(y_test, y_pred)), 4) if len(X_test) else 0.0,
            "mae": round(mean_absolute_error(y_test, y_pred), 4) if len(X_test) else 0.0,
            "r2": round(r2_score(y_test, y_pred), 4) if len(X_test) else 0.0,
        }
        if len(X_test):
            metrics.update(_grouped_ranking_metrics([groups[i] for i in test_idx], y_test, y_pred))

        alpha = round(min(MAX_ALPHA, max(0.1, len(rankings) / ALPHA_RAMP_ROWS)), 2)
        n_jobs = len({str(r.job_id) for r in rankings})

        # Training-set feature means, used by the explanation endpoint as the
        # "average candidate" baseline for per-feature attribution.
        feature_means = [float(np.mean(X[:, i])) for i in range(X.shape[1])]

        joblib.dump(
            {
                "model": model,
                "vectorizer": vectorizer,
                "feature_names": feature_names,
                "trained_at": datetime.utcnow().isoformat(),
                "metrics": metrics,
                "row_count": len(rankings),
                "job_count": n_jobs,
                "alpha": alpha,
                "feature_means": feature_means,
                "model_version": MODEL_VERSION,
            },
            MODEL_PATH,
        )

        _invalidate_idf_cache()

        return {
            "trained": True,
            "message": "Ranking model trained successfully.",
            "row_count": len(rankings),
            "job_count": n_jobs,
            "model_version": MODEL_VERSION,
            "model_path": str(MODEL_PATH),
            "alpha": alpha,
            "n_features": len(feature_names),
            "evaluation": evaluation,
            "metrics": metrics,
        }


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------


def load_ranking_bundle() -> RankingBundle | None:
    if not MODEL_PATH.exists():
        return None
    try:
        payload = joblib.load(MODEL_PATH)
        if int(payload.get("row_count", 0)) < MIN_TRAINING_ROWS:
            MODEL_PATH.unlink(missing_ok=True)
            return None
        means = payload.get("feature_means")
        return RankingBundle(
            model=payload["model"],
            vectorizer=payload.get("vectorizer"),
            feature_names=payload["feature_names"],
            trained_at=payload["trained_at"],
            metrics=payload.get("metrics", {}),
            row_count=int(payload.get("row_count", 0)),
            job_count=int(payload.get("job_count", 0)),
            alpha=float(payload.get("alpha", 0.5)),
            n_features=len(payload["feature_names"]),
            feature_means=(
                [float(v) for v in means]
                if isinstance(means, list) and len(means) == len(payload["feature_names"])
                else None
            ),
        )
    except Exception:
        # A corrupt/partial artifact (e.g. interrupted dump mid-write) would
        # otherwise block loading forever. Remove it so the next retrain can
        # rebuild a clean model; scoring falls back to the heuristic meanwhile.
        MODEL_PATH.unlink(missing_ok=True)
        return None


def get_ranking_model_status() -> dict[str, Any]:
    bundle = load_ranking_bundle()
    return {
        "available": bundle is not None,
        "model_version": MODEL_VERSION if bundle else None,
        "model_path": str(MODEL_PATH),
        "trained_at": bundle.trained_at if bundle else None,
        "row_count": bundle.row_count if bundle else 0,
        "job_count": bundle.job_count if bundle else 0,
        "alpha": bundle.alpha if bundle else None,
        "n_features": bundle.n_features if bundle else None,
        "metrics": bundle.metrics if bundle else {},
        "min_training_rows": MIN_TRAINING_ROWS,
    }


def explain_ranking_score(resume: Resume, job: Job) -> dict[str, Any]:
    """Per-feature attribution for a (resume, job) pair.

    Uses mean-shift attribution: for each of the 17 features, the model's
    prediction with the candidate's actual value is compared against the
    prediction with that feature replaced by its training-set mean (the
    "average candidate" baseline). A positive contribution means the
    feature pushed the score up; a negative one dragged it down.

    Falls back to the deterministic heuristic sub-scores (skills /
    experience / content) when no trained model exists, so the UI can
    still explain the score in every case.
    """
    bundle = load_ranking_bundle()

    heuristic: dict[str, float] = {}
    try:
        from routes_common import heuristic_breakdown

        heuristic = heuristic_breakdown(resume, job)
    except Exception:
        pass

    if not bundle:
        return {
            "available": False,
            "model_score": None,
            "blended_score": None,
            "alpha": None,
            "heuristic": heuristic,
            "contributions": [],
        }

    try:
        idf = _skill_idf_weights()
        feature_dict = build_feature_dict(resume, job, bundle.vectorizer, idf)
        names = bundle.feature_names
        means = bundle.feature_means
        values = np.array([[feature_dict.get(n, 0.0) for n in names]], dtype=float)
        base_pred = float(bundle.model.predict(values)[0])

        contributions = []
        for i, name in enumerate(names):
            variant = values.copy()
            variant[0, i] = means[i] if means and i < len(means) else 0.0
            variant_pred = float(bundle.model.predict(variant)[0])
            delta = base_pred - variant_pred  # positive → pushed score up
            label, desc = FEATURE_LABELS.get(name, (name, ""))
            contributions.append({
                "feature": name,
                "label": label,
                "description": desc,
                "value": round(feature_dict.get(name, 0.0), 2),
                "baseline": round(means[i], 2) if means and i < len(means) else 0.0,
                "contribution": round(delta, 2),
                "direction": "up" if delta > 0.5 else ("down" if delta < -0.5 else "neutral"),
            })

        contributions.sort(key=lambda c: abs(c["contribution"]), reverse=True)

        try:
            from routes_common import calculate_heuristic_score

            heuristic_score = float(calculate_heuristic_score(resume, job) or 0.0)
        except Exception:
            heuristic_score = (
                heuristic.get("skills_score", 0.0) * 0.70
                + heuristic.get("experience_score", 0.0) * 0.15
                + heuristic.get("content_score", 0.0) * 0.15
            )

        blended = (bundle.alpha * base_pred) + ((1.0 - bundle.alpha) * heuristic_score)

        return {
            "available": True,
            "model_score": round(float(np.clip(base_pred, 0.0, 100.0)), 2),
            "blended_score": round(float(np.clip(blended, 0.0, 100.0)), 2),
            "alpha": bundle.alpha,
            "heuristic": heuristic,
            "contributions": contributions,
        }
    except Exception as exc:
        return {
            "available": False,
            "model_score": None,
            "blended_score": None,
            "alpha": None,
            "heuristic": heuristic,
            "contributions": [],
            "error": str(exc),
        }


def explain_bulk_resume(
    raw_text: str,
    resume_skills: list[str],
    job_title: str,
    job_skills: list[str],
    job_description: str = "",
    job_experience_level: str | None = None,
) -> dict[str, Any]:
    """Explain a score for an ad-hoc resume (bulk screening).

    Bulk screening parses PDFs in-memory without creating DB rows, so a
    lightweight stand-in object is built from the extracted text/skills to
    reuse the same feature pipeline as persisted resumes.
    """
    from types import SimpleNamespace

    resume = SimpleNamespace(
        raw_text=raw_text,
        skills=[SimpleNamespace(skill_name=s) for s in resume_skills],
    )
    job = SimpleNamespace(
        title=job_title,
        description=job_description,
        skills=[SimpleNamespace(skill_name=s) for s in job_skills],
        experience_level=job_experience_level,
    )
    return explain_ranking_score(resume, job)


def predict_ranking_score(resume: Resume, job: Job) -> float:
    """Blended score: alpha * model + (1 - alpha) * heuristic.

    Falls back to the deterministic heuristic when no valid model exists
    or inference fails.
    """
    from routes_common import calculate_heuristic_score

    bundle = load_ranking_bundle()

    # Always compute the heuristic as the safety anchor.
    try:
        heuristic = float(calculate_heuristic_score(resume, job) or 0.0)
    except Exception:
        heuristic = 0.0

    if not bundle:
        return heuristic

    try:
        idf = _skill_idf_weights()
        feature_dict = build_feature_dict(resume, job, bundle.vectorizer, idf)
        feature_values = np.array(
            [[feature_dict.get(name, 0.0) for name in bundle.feature_names]],
            dtype=float,
        )
        predicted = float(bundle.model.predict(feature_values)[0])
        predicted = float(np.clip(predicted, 0.0, 100.0))
    except Exception:
        return heuristic

    blended = (bundle.alpha * predicted) + ((1.0 - bundle.alpha) * heuristic)
    return round(float(np.clip(blended, 0.0, 100.0)), 2)


if __name__ == "__main__":
    from app import create_app

    app = create_app()
    with app.app_context():
        result = train_ranking_model()
        print(result)
