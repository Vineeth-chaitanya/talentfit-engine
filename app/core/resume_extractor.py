import re
from app.core.text_cleaner import clean_text, split_sentences
from app.core.section_parser import parse_sections
from app.core.skill_normalizer import get_skill_normalizer
from app.schemas.resume import CandidateProfile, EvidenceSnippet


# Resume dates are hard to infer reliably without a full timeline parser. For the MVP,
# only explicit phrases such as "3 years" or "4+ yrs" are used. This avoids pretending
# that employment date ranges were interpreted with high confidence.
YEAR_RE = re.compile(r"(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)\b", re.I)


def extract_resume(text: str) -> CandidateProfile:
    """Convert raw resume text into a transparent, defensible profile object.

    This extractor is intentionally deterministic for the core MVP. It combines
    lightweight section parsing with taxonomy-based skill detection so the output is
    explainable in an interview and runnable without paid LLM APIs.
    """
    raw = clean_text(text)
    sections = parse_sections(raw)
    normalizer = get_skill_normalizer()
    skills = normalizer.extract_skills(raw)
    evidence = _build_evidence(raw, sections, skills)
    education = split_sentences(sections.get("education", ""))[:6]
    projects = split_sentences(sections.get("projects", ""))[:8]
    certifications = split_sentences(sections.get("certifications", ""))[:6]
    return CandidateProfile(
        raw_text=raw,
        sections=sections,
        summary=sections.get("summary", "")[:1200],
        skills=skills,
        experience_years=_infer_years(raw),
        education=education,
        projects=projects,
        certifications=certifications,
        evidence=evidence,
    )


def _infer_years(text: str) -> float | None:
    vals = [float(m.group(1)) for m in YEAR_RE.finditer(text)]
    return max(vals) if vals else None


def _build_evidence(raw: str, sections: dict[str, str], skills: list[str]) -> list[EvidenceSnippet]:
    normalizer = get_skill_normalizer()
    evidence: list[EvidenceSnippet] = []
    for skill in skills:
        aliases = normalizer.aliases_for(skill)
        for section, content in sections.items():
            snippet = _snippet_for_skill(content, aliases)
            if snippet:
                evidence.append(EvidenceSnippet(skill=skill, section=section, snippet=snippet))
                break
        else:
            snippet = _snippet_for_skill(raw, aliases)
            if snippet:
                evidence.append(EvidenceSnippet(skill=skill, section="unknown", snippet=snippet))
    return evidence


def _snippet_for_skill(text: str, aliases: list[str]) -> str | None:
    """Return the first sentence that actually contains the canonical skill or an alias."""
    sentences = split_sentences(text)
    patterns = [_alias_pattern(alias) for alias in aliases if alias]
    for sent in sentences:
        if any(pattern.search(sent) for pattern in patterns):
            return sent[:320]
    return None


def _alias_pattern(alias: str) -> re.Pattern:
    # Use soft boundaries so variants like "FastAPI", "Fast API", "fast-api" are all
    # usable as evidence without matching substrings inside unrelated words.
    escaped = re.escape(alias).replace(r"\ ", r"[\s\-/]*")
    return re.compile(rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9])", re.I)
