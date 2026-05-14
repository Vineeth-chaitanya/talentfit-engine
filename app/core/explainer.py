from app.schemas.match import MatchResult
from app.schemas.resume import CandidateProfile
from app.schemas.job import JobProfile


def generate_fit_report(candidate: CandidateProfile, job: JobProfile, result: MatchResult) -> str:
    lines = [f"Overall Fit: {result.final_score:.0f}/100", ""]
    role = job.role_title if job.role_title != "Unknown Role" else "the target role"
    lines.append(f"Target Role: {role}")
    lines.append("")

    lines.append("Strong Matches:")
    if result.matched_skills:
        for skill in result.matched_skills[:10]:
            locations = [e.section for e in candidate.evidence if e.skill == skill]
            place = f" found in {', '.join(sorted(set(locations)))}" if locations else " found in resume"
            lines.append(f"- {skill}:{place}")
    else:
        lines.append("- No direct skill matches were found in the current taxonomy.")

    lines.append("")
    lines.append("Missing Required Skills:")
    if result.missing_required_skills:
        for skill in result.missing_required_skills:
            lines.append(f"- {skill}")
    else:
        lines.append("- None detected.")

    if result.partial_matches:
        lines.append("")
        lines.append("Partial Matches:")
        for p in result.partial_matches[:8]:
            lines.append(f"- {p.candidate_skill} partially supports {p.required_skill}: {p.reason}")

    if result.strongest_evidence_snippets:
        lines.append("")
        lines.append("Evidence Snippets:")
        for e in result.strongest_evidence_snippets[:5]:
            lines.append(f"- {e.skill} ({e.section}): {e.snippet}")

    lines.append("")
    recommendation = _recommendation(result)
    lines.append(f"Recommendation: {recommendation}")
    return "\n".join(lines)


def _recommendation(result: MatchResult) -> str:
    if result.final_score >= 80:
        return "This candidate appears to be a strong fit. Focus improvements on making deployment, metrics, and business impact more explicit."
    if result.final_score >= 60:
        return "This candidate has a credible fit, but should strengthen missing required skills and move the most relevant project evidence higher."
    return "This candidate may need substantial resume targeting or additional project evidence before applying to this role."
