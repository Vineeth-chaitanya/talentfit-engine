from pydantic import BaseModel, Field
from typing import Dict, List
from app.schemas.resume import EvidenceSnippet
from app.schemas.job import JobProfile
from app.schemas.resume import CandidateProfile


class PartialMatch(BaseModel):
    required_skill: str
    candidate_skill: str
    reason: str


class ResumeSuggestion(BaseModel):
    suggestion: str
    reason: str
    evidence: str
    related_requirement: str


class MatchResult(BaseModel):
    final_score: float
    score_breakdown: Dict[str, float]
    matched_skills: List[str] = Field(default_factory=list)
    missing_required_skills: List[str] = Field(default_factory=list)
    missing_preferred_skills: List[str] = Field(default_factory=list)
    partial_matches: List[PartialMatch] = Field(default_factory=list)
    strongest_evidence_snippets: List[EvidenceSnippet] = Field(default_factory=list)
    risk_flags: List[str] = Field(default_factory=list)


class AnalyzeRequest(BaseModel):
    resume_text: str | None = None
    job_description: str


class AnalyzeResponse(BaseModel):
    candidate: CandidateProfile
    job: JobProfile
    match: MatchResult
    fit_report: str
    suggestions: List[ResumeSuggestion] = Field(default_factory=list)
