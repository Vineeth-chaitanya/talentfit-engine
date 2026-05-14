import re
from collections import OrderedDict

SECTION_ALIASES = {
    "summary": ["summary", "professional summary", "profile", "objective"],
    "skills": ["skills", "technical skills", "core skills", "technologies", "tools"],
    "experience": ["experience", "work experience", "professional experience", "employment"],
    "education": ["education", "academic background"],
    "projects": ["projects", "selected projects", "portfolio projects"],
    "certifications": ["certifications", "certificates", "licenses"],
}

HEADER_TO_SECTION = {alias: key for key, aliases in SECTION_ALIASES.items() for alias in aliases}
HEADER_RE = re.compile(r"^\s*([A-Z][A-Za-z /&-]{2,45})\s*:?\s*$")


def parse_sections(text: str) -> dict[str, str]:
    lines = text.splitlines()
    sections: OrderedDict[str, list[str]] = OrderedDict()
    current = "summary"
    sections[current] = []

    for line in lines:
        normalized = line.strip().lower()
        normalized = re.sub(r"\s+", " ", normalized)
        if normalized in HEADER_TO_SECTION or _looks_like_header(line, normalized):
            current = HEADER_TO_SECTION.get(normalized, normalized.replace(" ", "_"))
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)

    return {k: "\n".join(v).strip() for k, v in sections.items() if "\n".join(v).strip()}


def _looks_like_header(original: str, normalized: str) -> bool:
    match = HEADER_RE.match(original)
    if not match:
        return False
    return normalized in HEADER_TO_SECTION or normalized in {"awards", "publications", "leadership"}
