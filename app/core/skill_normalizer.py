import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Iterable

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "skills_taxonomy.json"


class SkillNormalizer:
    """Taxonomy-backed skill normalization.

    The implementation is deliberately simple: it maps known aliases to canonical
    skills and uses boundary-aware regex matching. This is easier to audit than an
    opaque model, but it only finds skills represented in the taxonomy.
    """

    def __init__(self, taxonomy_path: str | Path = DATA_PATH):
        self.taxonomy_path = Path(taxonomy_path)
        self.taxonomy = json.loads(self.taxonomy_path.read_text(encoding="utf-8"))
        self.alias_to_canonical: dict[str, str] = {}
        self.canonical_to_category: dict[str, str] = {}
        self.canonical_to_aliases: dict[str, list[str]] = {}
        for item in self.taxonomy:
            canonical = item["canonical"]
            self.canonical_to_category[canonical] = item.get("category", "Other")
            aliases = [canonical, *item.get("synonyms", [])]
            self.canonical_to_aliases[canonical] = aliases
            for alias in aliases:
                self.alias_to_canonical[self._key(alias)] = canonical
        self._patterns = sorted(self.alias_to_canonical.items(), key=lambda kv: len(kv[0]), reverse=True)

    def _key(self, value: str) -> str:
        value = value.lower().strip()
        value = value.replace("+", " plus ")
        value = re.sub(r"[^a-z0-9#]+", " ", value)
        return re.sub(r"\s+", " ", value).strip()

    def normalize_skill(self, skill: str) -> str | None:
        return self.alias_to_canonical.get(self._key(skill))

    def normalize_many(self, skills: Iterable[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for skill in skills:
            canonical = self.normalize_skill(skill) or skill.strip()
            if canonical and canonical not in seen:
                seen.add(canonical)
                out.append(canonical)
        return out

    def extract_skills(self, text: str) -> list[str]:
        normalized_text = f" {self._key(text)} "
        found: list[str] = []
        seen: set[str] = set()
        for alias_key, canonical in self._patterns:
            pattern = rf"(?<![a-z0-9#]){re.escape(alias_key)}(?![a-z0-9#])"
            if re.search(pattern, normalized_text) and canonical not in seen:
                seen.add(canonical)
                found.append(canonical)
        return found

    def aliases_for(self, canonical_skill: str) -> list[str]:
        return self.canonical_to_aliases.get(canonical_skill, [canonical_skill])

    def text_mentions_skill(self, text: str, canonical_skill: str) -> bool:
        """Check whether text mentions a canonical skill through any known alias."""
        normalized = f" {self._key(text)} "
        for alias in self.aliases_for(canonical_skill):
            alias_key = self._key(alias)
            pattern = rf"(?<![a-z0-9#]){re.escape(alias_key)}(?![a-z0-9#])"
            if re.search(pattern, normalized):
                return True
        return False

    def category(self, skill: str) -> str:
        return self.canonical_to_category.get(skill, "Other")


@lru_cache
def get_skill_normalizer() -> SkillNormalizer:
    return SkillNormalizer()
