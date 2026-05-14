import re
from collections import Counter
from app.core.text_cleaner import clean_text, split_sentences
from app.core.skill_normalizer import get_skill_normalizer
from app.schemas.job import JobProfile

TITLE_RE = re.compile(r"(?:job title|title|role)\s*[:\-]\s*(.+)", re.I)
YEAR_RE = re.compile(r"(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)\b", re.I)
REQUIRED_HINTS = ("required", "requirements", "must have", "you have", "minimum", "qualifications")
PREFERRED_HINTS = ("preferred", "nice to have", "bonus", "plus", "desirable")


def extract_job(text: str) -> JobProfile:
    """Extract a transparent job profile from a job description.

    The extractor favors precision over aggressive inference. Skills are detected from
    the taxonomy, then classified as required/preferred based on nearby wording.
    """
    raw = clean_text(text)
    normalizer = get_skill_normalizer()
    all_skills = normalizer.extract_skills(raw)
    required, preferred = _classify_skills(raw, all_skills)
    return JobProfile(
        raw_text=raw,
        role_title=_extract_title(raw),
        required_skills=required,
        preferred_skills=preferred,
        responsibilities=_extract_responsibilities(raw),
        years_experience=_extract_years(raw),
        seniority_level=_infer_seniority(raw),
        keywords=_keywords(raw, all_skills),
    )


def _extract_title(text: str) -> str:
    first_lines = [l.strip() for l in text.splitlines() if l.strip()]
    for line in first_lines[:8]:
        m = TITLE_RE.search(line)
        if m:
            return m.group(1).strip()[:100]
    for line in first_lines[:4]:
        if any(t in line.lower() for t in ["engineer", "scientist", "analyst", "developer", "architect"]):
            return line[:100]
    return "Unknown Role"


def _classify_skills(text: str, skills: list[str]) -> tuple[list[str], list[str]]:
    normalizer = get_skill_normalizer()
    sentences = split_sentences(text)
    required, preferred = [], []
    for skill in skills:
        contexts = []
        for sentence in sentences:
            if normalizer.text_mentions_skill(sentence, skill):
                contexts.append(sentence.lower())
        joined = " ".join(contexts)
        if any(h in joined for h in PREFERRED_HINTS):
            preferred.append(skill)
        elif any(h in joined for h in REQUIRED_HINTS):
            required.append(skill)
        else:
            # When a posting lists tools without labels, treat them as required but do
            # not claim the system inferred contractual requirements. The README notes
            # this as a heuristic.
            required.append(skill)
    return _unique(required), _unique([s for s in preferred if s not in required])


def _extract_responsibilities(text: str) -> list[str]:
    sentences = split_sentences(text)
    action_terms = ("build", "develop", "deploy", "design", "collaborate", "analyze", "maintain", "evaluate", "optimize")
    return [s[:280] for s in sentences if s.lower().startswith(action_terms) or any(f" {t} " in s.lower() for t in action_terms)][:10]


def _extract_years(text: str) -> float | None:
    vals = [float(m.group(1)) for m in YEAR_RE.finditer(text)]
    return min(vals) if vals else None


def _infer_seniority(text: str) -> str | None:
    lower = text.lower()
    if any(x in lower for x in ["principal", "staff"]):
        return "staff/principal"
    if "senior" in lower or "sr." in lower:
        return "senior"
    if "lead" in lower:
        return "lead"
    if "junior" in lower or "entry" in lower:
        return "entry"
    if "intern" in lower:
        return "intern"
    return None


def _keywords(text: str, skills: list[str]) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z+/#.-]{2,}", text.lower())
    stop = {"and", "the", "with", "for", "you", "our", "will", "are", "this", "that", "from", "experience", "skills", "required"}
    counts = Counter(w for w in words if w not in stop and len(w) > 2)
    top = [w for w, _ in counts.most_common(20)]
    return _unique(skills + top)[:30]


def _unique(items: list[str]) -> list[str]:
    seen, out = set(), []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out
