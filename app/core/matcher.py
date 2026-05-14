from __future__ import annotations
from functools import lru_cache
from typing import Iterable
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.config import get_settings
from app.schemas.resume import CandidateProfile, EvidenceSnippet
from app.schemas.job import JobProfile
from app.schemas.match import MatchResult, PartialMatch
from app.core.skill_normalizer import get_skill_normalizer

# Interview note: these are not learned weights. They are product heuristics chosen
# to make the score explainable. In a production system, this should be calibrated
# with recruiter feedback, interview outcomes, or labeled candidate-job pairs.
WEIGHTS = {
    "required_skill_coverage": 0.35,
    "preferred_skill_coverage": 0.15,
    "semantic_similarity": 0.20,
    "keyword_similarity": 0.15,
    "experience_alignment": 0.10,
    "project_relevance": 0.05,
}


@lru_cache
def _embedding_model():
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(get_settings().embedding_model)
    except Exception:
        # The system remains runnable in restricted environments. The README is explicit
        # that TF-IDF is used as a fallback when the local embedding model is unavailable.
        return None


def match_candidate_to_job(candidate: CandidateProfile, job: JobProfile) -> MatchResult:
    """Compute an interpretable candidate-job fit score.

    This is a hybrid ranker, not a hiring decision model. It combines exact normalized
    skill coverage with text similarity and simple experience alignment, then returns
    every intermediate component for auditability.
    """
    candidate_skills = set(candidate.skills)
    required = set(job.required_skills)
    preferred = set(job.preferred_skills)

    matched_required = sorted(candidate_skills & required)
    matched_preferred = sorted(candidate_skills & preferred)
    missing_required = sorted(required - candidate_skills)
    missing_preferred = sorted(preferred - candidate_skills)

    required_score = _coverage(matched_required, required)
    preferred_score = _coverage(matched_preferred, preferred)
    semantic_score = _semantic_similarity(candidate.raw_text, job.raw_text)
    keyword_score = _tfidf_similarity(candidate.raw_text, job.raw_text)
    experience_score = _experience_alignment(candidate.experience_years, job.years_experience)
    project_score = _project_relevance(candidate, job)

    breakdown = {
        "required_skill_coverage": round(required_score * 100, 2),
        "preferred_skill_coverage": round(preferred_score * 100, 2),
        "semantic_similarity": round(semantic_score * 100, 2),
        "keyword_similarity": round(keyword_score * 100, 2),
        "experience_alignment": round(experience_score * 100, 2),
        "project_relevance": round(project_score * 100, 2),
    }
    final = sum(breakdown[k] * WEIGHTS[k] for k in WEIGHTS)

    partial_matches = _partial_matches(missing_required, candidate.skills)
    risks = _risk_flags(job, candidate, missing_required, semantic_score)
    evidence = _rank_evidence(candidate.evidence, list(required | preferred))[:8]

    return MatchResult(
        final_score=round(float(np.clip(final, 0, 100)), 2),
        score_breakdown=breakdown,
        matched_skills=sorted(set(matched_required + matched_preferred)),
        missing_required_skills=missing_required,
        missing_preferred_skills=missing_preferred,
        partial_matches=partial_matches,
        strongest_evidence_snippets=evidence,
        risk_flags=risks,
    )


def _coverage(matched: Iterable[str], target: Iterable[str]) -> float:
    target = list(target)
    if not target:
        return 1.0
    return len(set(matched)) / len(set(target))


def _tfidf_similarity(a: str, b: str) -> float:
    try:
        vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)
        matrix = vec.fit_transform([a, b])
        return float(cosine_similarity(matrix[0], matrix[1])[0, 0])
    except ValueError:
        return 0.0


def _semantic_similarity(a: str, b: str) -> float:
    model = _embedding_model()
    if model is None:
        return _tfidf_similarity(a, b)
    emb = model.encode([a[:6000], b[:6000]], normalize_embeddings=True)
    return float(np.clip(np.dot(emb[0], emb[1]), 0, 1))


def _experience_alignment(candidate_years: float | None, required_years: float | None) -> float:
    if required_years is None:
        return 1.0
    if candidate_years is None:
        # Penalize uncertainty, but do not make it zero because many resumes omit an
        # explicit total even when date ranges imply experience.
        return 0.45
    return float(np.clip(candidate_years / required_years, 0, 1))


def _project_relevance(candidate: CandidateProfile, job: JobProfile) -> float:
    project_text = " ".join(candidate.projects) or candidate.sections.get("projects", "")
    if not project_text:
        return 0.35
    return _tfidf_similarity(project_text, job.raw_text)


def _partial_matches(missing_required: list[str], candidate_skills: list[str]) -> list[PartialMatch]:
    normalizer = get_skill_normalizer()
    partials: list[PartialMatch] = []
    for req in missing_required:
        req_cat = normalizer.category(req)
        if req_cat == "Other":
            continue
        same_cat = [s for s in candidate_skills if normalizer.category(s) == req_cat and s != req]
        if same_cat:
            partials.append(PartialMatch(required_skill=req, candidate_skill=same_cat[0], reason=f"Both are in the {req_cat} category, but this is only a weak proxy."))
    return partials[:8]


def _risk_flags(job: JobProfile, candidate: CandidateProfile, missing_required: list[str], semantic_score: float) -> list[str]:
    flags = []
    if missing_required:
        flags.append(f"Missing {len(missing_required)} required skill(s): {', '.join(missing_required[:5])}")
    if job.years_experience and candidate.experience_years is None:
        flags.append("Job mentions years of experience, but resume does not clearly state total years.")
    elif job.years_experience and candidate.experience_years and candidate.experience_years < job.years_experience:
        flags.append(f"Experience may be below requirement: {candidate.experience_years:g} vs {job.years_experience:g} years.")
    if semantic_score < 0.25:
        flags.append("Resume and job description have low semantic similarity.")
    return flags


def _rank_evidence(evidence: list[EvidenceSnippet], priority_skills: list[str]) -> list[EvidenceSnippet]:
    priority = {s: i for i, s in enumerate(priority_skills)}
    return sorted(evidence, key=lambda e: priority.get(e.skill, 10_000))
