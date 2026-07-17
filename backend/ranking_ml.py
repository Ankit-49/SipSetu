from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from math import log2, sqrt
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split

from models import Job, Ranking, Resume

EXPERIENCE_LEVEL_TO_YEARS = {
    "fresher": 0.0,
    "1-3": 2.0,
    "3-5": 4.0,
    "5+": 5.0,
}

MODEL_DIR = Path(__file__).resolve().parent / "ml_artifacts"
MODEL_PATH = MODEL_DIR / "candidate_ranker.joblib"
MODEL_VERSION = "candidate-ranker-v1"
RELEVANCE_THRESHOLD = 60.0


@dataclass
class RankingBundle:
    model: Any
    vectorizer: TfidfVectorizer | None
    feature_names: list[str]
    trained_at: str
    metrics: dict[str, float]
    row_count: int


def _clean_text(value: str | None) -> str:
    return (value or "").strip()


def extract_experience_years(text: str | None) -> float | None:
    if not text:
        return None

    import re

    patterns = [
        r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?|yr\.?)\s*(?:of\s*)?(?:experience|exp\.?)",
        r"(?:experience|exp\.?)\s*(?:of\s*)?(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?|yr\.?)",
     
    ]

    detected_years = []
    for pattern in patterns:
        for match in re.findall(pattern, text, flags=re.IGNORECASE):
            try:
                detected_years.append(float(match))
            except ValueError:
                continue

    return round(max(detected_years), 1) if detected_years else None


def experience_level_to_years(experience_level: str | None) -> float | None:
    if not experience_level:
        return None
    return EXPERIENCE_LEVEL_TO_YEARS.get(str(experience_level).strip().lower())


def calculate_experience_score(candidate_years: float | None, target_years: float | None) -> float:
    if candidate_years is None:
        return 0.0

    if target_years is None:
        return min(candidate_years * 12.0, 100.0)

    if target_years <= 0:
        return 100.0 if candidate_years <= 1 else max(0.0, 100.0 - ((candidate_years - 1) * 12.0))

    if candidate_years >= target_years:
        return 100.0

    return round(max(0.0, (candidate_years / target_years) * 100.0), 2)


def _skill_names(record) -> list[str]:
    return [skill.skill_name.lower() for skill in getattr(record, "skills", [])]


def _pair_text(resume: Resume, job: Job) -> tuple[str, str]:
    resume_text = _clean_text(resume.raw_text) or " ".join(_skill_names(resume))
    job_text = " ".join(filter(None, [job.title or "", job.description or "", " ".join(_skill_names(job))]))
    return resume_text, job_text.strip()


def _content_similarity(resume_text: str, job_text: str, vectorizer: TfidfVectorizer | None) -> float:
    if not vectorizer or not resume_text or not job_text:
        return 0.0

    matrix = vectorizer.transform([resume_text, job_text]).toarray()
    similarity = cosine_similarity(matrix[0:1], matrix[1:2])
    return float(similarity[0, 0])


def build_feature_dict(resume: Resume, job: Job, vectorizer: TfidfVectorizer | None = None) -> dict[str, float]:
    resume_skills = _skill_names(resume)
    job_skills = _skill_names(job)

    resume_set = set(resume_skills)
    job_set = set(job_skills)
    intersection = resume_set.intersection(job_set)
    union = resume_set.union(job_set)

    candidate_years = extract_experience_years(resume.raw_text or "")
    target_years = experience_level_to_years(job.experience_level)
    experience_score = calculate_experience_score(candidate_years, target_years)
    resume_text, job_text = _pair_text(resume, job)

    return {
        "skills_overlap_count": float(len(intersection)),
        "skills_jaccard": float(len(intersection) / len(union)) if union else 0.0,
        "resume_skill_count": float(len(resume_set)),
        "job_skill_count": float(len(job_set)),
        "experience_years": float(candidate_years or 0.0),
        "target_experience_years": float(target_years or 0.0),
        "experience_gap": float(abs((candidate_years or 0.0) - (target_years or 0.0))) if target_years is not None else float(candidate_years or 0.0),
        "experience_score": float(experience_score),
        "resume_text_length": float(len(resume_text.split())),
        "job_text_length": float(len(job_text.split())),
        "content_similarity": _content_similarity(resume_text, job_text, vectorizer),
    }


def _feature_order() -> list[str]:
    return [
        "skills_overlap_count",
        "skills_jaccard",
        "resume_skill_count",
        "job_skill_count",
        "experience_years",
        "target_experience_years",
        "experience_gap",
        "experience_score",
        "resume_text_length",
        "job_text_length",
        "content_similarity",
    ]


def _feature_matrix(rows: list[dict[str, float]], feature_names: list[str]) -> np.ndarray:
    return np.array([[row[name] for name in feature_names] for row in rows], dtype=float)


def _heuristic_score(resume: Resume, job: Job) -> float:
    resume_skills = _skill_names(resume)
    job_skills = _skill_names(job)

    if not job_skills or not resume_skills:
        return 0.0

    resume_set = set(resume_skills)
    job_set = set(job_skills)
    if not job_set:
        return 0.0

    intersection = len(resume_set.intersection(job_set))
    union = len(resume_set.union(job_set))
    skills_score = round((intersection / len(job_set)) * 100, 2) if job_set else 0.0
    experience_years = extract_experience_years(resume.raw_text or "")
    target_experience_years = experience_level_to_years(job.experience_level)
    experience_score = calculate_experience_score(experience_years, target_experience_years)

    resume_text, job_text = _pair_text(resume, job)
    content_sim = 0.0
    if resume_text and job_text:
        try:
            matrix = TfidfVectorizer().fit_transform([resume_text, job_text]).toarray()
            content_sim = float(cosine_similarity(matrix[0:1], matrix[1:2])[0, 0]) * 100
        except ValueError:
            pass

    if skills_score == 100.0 and experience_score >= 100.0 and content_sim >= 99.0:
        return 100.0

    combined_score = (skills_score * 0.70) + (experience_score * 0.15) + (content_sim * 0.15)
    return min(round(combined_score, 2), 99.99)


@lru_cache(maxsize=1)
def load_ranking_bundle() -> RankingBundle | None:
    if not MODEL_PATH.exists():
        return None

    payload = joblib.load(MODEL_PATH)
    return RankingBundle(
        model=payload["model"],
        vectorizer=payload.get("vectorizer"),
        feature_names=payload["feature_names"],
        trained_at=payload["trained_at"],
        metrics=payload.get("metrics", {}),
        row_count=int(payload.get("row_count", 0)),
    )


def get_ranking_model_status() -> dict[str, Any]:
    bundle = load_ranking_bundle()
    return {
        "available": bundle is not None,
        "model_version": MODEL_VERSION if bundle else None,
        "model_path": str(MODEL_PATH),
        "trained_at": bundle.trained_at if bundle else None,
        "row_count": bundle.row_count if bundle else 0,
        "metrics": bundle.metrics if bundle else {},
    }


def predict_ranking_score(resume: Resume, job: Job) -> float:
    bundle = load_ranking_bundle()
    if not bundle:
        return _heuristic_score(resume, job)

    feature_dict = build_feature_dict(resume, job, bundle.vectorizer)
    feature_values = np.array([[feature_dict[name] for name in bundle.feature_names]], dtype=float)
    predicted = float(bundle.model.predict(feature_values)[0])
    return float(np.clip(predicted, 0.0, 100.0))


def _ndcg_at_k(y_true: np.ndarray, y_pred: np.ndarray, k: int = 5) -> float:
    if y_true.size == 0:
        return 0.0

    order = np.argsort(y_pred)[::-1][:k]
    ideal_order = np.argsort(y_true)[::-1][:k]

    def _dcg(values: np.ndarray) -> float:
        total = 0.0
        for idx, value in enumerate(values):
            total += float(value) / log2(idx + 2)
        return total

    dcg = _dcg(y_true[order])
    idcg = _dcg(y_true[ideal_order])
    return dcg / idcg if idcg > 0 else 0.0


def _precision_recall_mrr_at_k(y_true: np.ndarray, y_pred: np.ndarray, k: int = 5) -> tuple[float, float, float]:
    if y_true.size == 0:
        return 0.0, 0.0, 0.0

    order = np.argsort(y_pred)[::-1][:k]
    relevance = y_true[order] >= RELEVANCE_THRESHOLD
    precision = float(np.sum(relevance)) / min(k, len(y_true))
    recall = float(np.sum(relevance)) / max(1, int(np.sum(y_true >= RELEVANCE_THRESHOLD)))

    reciprocal_rank = 0.0
    for idx, is_relevant in enumerate(relevance, start=1):
        if is_relevant:
            reciprocal_rank = 1.0 / idx
            break

    return precision, recall, reciprocal_rank


def _grouped_ranking_metrics(group_ids: list[str], y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    grouped: dict[str, list[int]] = {}
    for index, group_id in enumerate(group_ids):
        grouped.setdefault(group_id, []).append(index)

    ndcg_scores = []
    precision_scores = []
    recall_scores = []
    mrr_scores = []

    for indices in grouped.values():
        group_true = y_true[indices]
        group_pred = y_pred[indices]
        if group_true.size < 2:
            continue

        ndcg_scores.append(_ndcg_at_k(group_true, group_pred, k=min(5, group_true.size)))
        precision, recall, reciprocal_rank = _precision_recall_mrr_at_k(group_true, group_pred, k=min(5, group_true.size))
        precision_scores.append(precision)
        recall_scores.append(recall)
        mrr_scores.append(reciprocal_rank)

    return {
        "ndcg_at_5": round(float(np.mean(ndcg_scores)) if ndcg_scores else 0.0, 4),
        "precision_at_5": round(float(np.mean(precision_scores)) if precision_scores else 0.0, 4),
        "recall_at_5": round(float(np.mean(recall_scores)) if recall_scores else 0.0, 4),
        "mrr_at_5": round(float(np.mean(mrr_scores)) if mrr_scores else 0.0, 4),
    }


def train_ranking_model(random_state: int = 42) -> dict[str, Any]:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    rankings = Ranking.query.filter(Ranking.matching_score.isnot(None)).all()

    if len(rankings) < 5:
        return {
            "trained": False,
            "message": "Not enough ranked resume/job pairs to train the model.",
            "row_count": len(rankings),
        }

    corpus = []
    for ranking in rankings:
        resume_text, job_text = _pair_text(ranking.resume, ranking.job)
        if resume_text:
            corpus.append(resume_text)
        if job_text:
            corpus.append(job_text)

    vectorizer = None
    if len(corpus) >= 2:
        vectorizer = TfidfVectorizer(max_features=2500, ngram_range=(1, 2), stop_words="english")
        vectorizer.fit(corpus)

    feature_rows = [build_feature_dict(ranking.resume, ranking.job, vectorizer) for ranking in rankings]
    feature_names = _feature_order()
    X = _feature_matrix(feature_rows, feature_names)
    y = np.array([float(ranking.matching_score or 0.0) for ranking in rankings], dtype=float)
    groups = [str(ranking.job_id) for ranking in rankings]

    unique_count = len(np.unique(y))
    if unique_count < 2:
        return {
            "trained": False,
            "message": "Training targets need at least two distinct score values.",
            "row_count": len(rankings),
        }

    test_size = 0.2 if len(rankings) >= 10 else 0.33
    X_train, X_test, y_train, y_test, _, groups_test = train_test_split(
        X,
        y,
        groups,
        test_size=test_size,
        random_state=random_state,
    )

    model = RandomForestRegressor(
        n_estimators=300,
        random_state=random_state,
        max_depth=10,
        min_samples_leaf=2,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    regression_metrics = {
        "rmse": round(sqrt(mean_squared_error(y_test, y_pred)), 4),
        "mae": round(mean_absolute_error(y_test, y_pred), 4),
        "r2": round(r2_score(y_test, y_pred), 4),
    }
    ranking_metrics = _grouped_ranking_metrics(groups_test, y_test, y_pred)
    metrics = {**regression_metrics, **ranking_metrics}

    joblib.dump(
        {
            "model": model,
            "vectorizer": vectorizer,
            "feature_names": feature_names,
            "trained_at": datetime.utcnow().isoformat(),
            "metrics": metrics,
            "row_count": len(rankings),
            "model_version": MODEL_VERSION,
        },
        MODEL_PATH,
    )

    load_ranking_bundle.cache_clear()

    return {
        "trained": True,
        "message": "Ranking model trained successfully.",
        "row_count": len(rankings),
        "model_version": MODEL_VERSION,
        "model_path": str(MODEL_PATH),
        "metrics": metrics,
    }
