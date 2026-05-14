from pydantic import BaseModel, Field
from typing import Dict, List


class EvidenceSnippet(BaseModel):
    skill: str
    section: str = "unknown"
    snippet: str


class CandidateProfile(BaseModel):
    raw_text: str
    sections: Dict[str, str] = Field(default_factory=dict)
    summary: str = ""
    skills: List[str] = Field(default_factory=list)
    experience_years: float | None = None
    education: List[str] = Field(default_factory=list)
    projects: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    evidence: List[EvidenceSnippet] = Field(default_factory=list)
