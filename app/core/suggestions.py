"""Grounded resume suggestions.

Suggestions are intentionally conservative: every suggestion includes an evidence
field copied from the candidate resume. Missing-skill suggestions are phrased as
truthfulness checks rather than instructions to fabricate experience.
"""

from app.schemas.match import MatchResult, ResumeSuggestion
from app.schemas.resume import CandidateProfile
from app.schemas.job import JobProfile


def generate_suggestions(candidate: CandidateProfile, job: JobProfile, result: MatchResult) -> list[ResumeSuggestion]:
    suggestions: list[ResumeSuggestion] = []
    evidence_by_skill = {e.skill: e.snippet for e in candidate.evidence}

    for skill in result.matched_skills[:5]:
        evidence = evidence_by_skill.get(skill)
        if evidence:
            suggestions.append(ResumeSuggestion(
                suggestion=f"Make the {skill} evidence more measurable and easier to scan.",
                reason="The job appears to value this skill, and the resume already has grounded evidence for it.",
                evidence=evidence,
                related_requirement=skill,
            ))

    for missing in result.missing_required_skills[:5]:
        anchor = _best_existing_anchor(candidate)
        if anchor:
            suggestions.append(ResumeSuggestion(
                suggestion=f"Add truthful evidence for {missing} only if you have used it; otherwise, add a small project or learning section before claiming it.",
                reason="This is listed as a required skill but was not found in the resume text.",
                evidence=anchor,
                related_requirement=missing,
            ))

    if job.required_skills and candidate.projects:
        suggestions.append(ResumeSuggestion(
            suggestion="Move the most job-relevant ML/search/backend project closer to the top of the resume.",
            reason="Recruiters scan quickly, and this role depends on technical evidence being visible early.",
            evidence=candidate.projects[0][:300],
            related_requirement=", ".join(job.required_skills[:4]),
        ))

    return suggestions[:8]


def _best_existing_anchor(candidate: CandidateProfile) -> str:
    if candidate.evidence:
        return candidate.evidence[0].snippet
    if candidate.summary:
        return candidate.summary[:300]
    return candidate.raw_text[:300]
