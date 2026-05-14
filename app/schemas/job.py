from pydantic import BaseModel, Field
from typing import List


class JobProfile(BaseModel):
    raw_text: str
    role_title: str = "Unknown Role"
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    years_experience: float | None = None
    seniority_level: str | None = None
    keywords: List[str] = Field(default_factory=list)
