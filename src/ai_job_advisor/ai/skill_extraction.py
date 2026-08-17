"""AI skill extraction, normalisation and taxonomy.

The extractor is deterministic and offline by default: it matches a curated,
ESCO-inspired skill taxonomy (canonical name -> aliases) against job text using
word-boundary matching, then normalises everything to canonical names. This is
fast, explainable and unit-testable. A neural / LLM extractor can be layered on
top later behind the same interface.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable

# Canonical skill -> set of surface aliases (lowercased). ESCO-inspired but
# trimmed to a practical tech / business / soft-skill seed taxonomy. In
# production this is replaced by an ESCO skill-pillar import.
DEFAULT_TAXONOMY: dict[str, list[str]] = {
    "python": ["python", "py"],
    "java": ["java"],
    "javascript": ["javascript", "js", "ecmascript"],
    "typescript": ["typescript", "ts"],
    "sql": ["sql", "structured query language"],
    "postgresql": ["postgresql", "postgres", "psql"],
    "neo4j": ["neo4j", "cypher"],
    "docker": ["docker", "containerization", "containerisation"],
    "kubernetes": ["kubernetes", "k8s"],
    "aws": ["aws", "amazon web services"],
    "azure": ["azure"],
    "gcp": ["gcp", "google cloud"],
    "machine learning": ["machine learning", "ml"],
    "deep learning": ["deep learning"],
    "pytorch": ["pytorch", "torch"],
    "tensorflow": ["tensorflow", "tf"],
    "nlp": ["nlp", "natural language processing"],
    "data analysis": ["data analysis", "data analytics", "analytics"],
    "data engineering": ["data engineering", "etl", "data pipelines"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "react": ["react", "reactjs", "react.js"],
    "streamlit": ["streamlit"],
    "fastapi": ["fastapi"],
    "rest api": ["rest", "rest api", "restful"],
    "git": ["git", "version control"],
    "linux": ["linux", "unix"],
    "communication": ["communication", "communication skills"],
    "teamwork": ["teamwork", "team player", "collaboration"],
    "project management": ["project management", "scrum", "agile", "kanban"],
    "english": ["english"],
    "slovenian": ["slovenian", "slovene", "slovenščina"],
    "marketing": ["marketing", "digital marketing"],
    "sales": ["sales", "business development"],
    "excel": ["excel", "spreadsheets"],
    "power bi": ["power bi", "powerbi"],
    "tableau": ["tableau"],
    "statistics": ["statistics", "statistical analysis"],
}


def _compile_alias_index(taxonomy: dict[str, list[str]]) -> list[tuple[str, re.Pattern[str]]]:
    """Build (canonical, regex) pairs, longest alias first to avoid partials."""
    index: list[tuple[str, re.Pattern[str]]] = []
    pairs: list[tuple[str, str]] = []
    for canonical, aliases in taxonomy.items():
        for alias in aliases:
            pairs.append((canonical, alias))
    # Longer aliases first so "data analysis" wins over "data".
    pairs.sort(key=lambda p: len(p[1]), reverse=True)
    for canonical, alias in pairs:
        pattern = re.compile(rf"(?<![\w]){re.escape(alias)}(?![\w])", re.IGNORECASE)
        index.append((canonical, pattern))
    return index


@dataclass(slots=True)
class SkillExtractor:
    """Extracts and normalises skills from free text."""

    taxonomy: dict[str, list[str]] = field(default_factory=lambda: dict(DEFAULT_TAXONOMY))
    _index: list[tuple[str, re.Pattern[str]]] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        self._index = _compile_alias_index(self.taxonomy)

    def normalize(self, raw_skill: str) -> str | None:
        """Map a raw skill string to its canonical name, if known."""
        text = raw_skill.strip().lower()
        if not text:
            return None
        if text in self.taxonomy:
            return text
        for canonical, aliases in self.taxonomy.items():
            if text == canonical or text in aliases:
                return canonical
        return None

    def extract(self, text: str) -> list[str]:
        """Return the sorted set of canonical skills found in ``text``."""
        if not text:
            return []
        found: set[str] = set()
        for canonical, pattern in self._index:
            if pattern.search(text):
                found.add(canonical)
        return sorted(found)

    def extract_many(self, texts: Iterable[str]) -> Counter:
        """Count canonical skills across many texts (market-demand signal)."""
        counter: Counter = Counter()
        for text in texts:
            counter.update(self.extract(text))
        return counter


def get_default_extractor() -> SkillExtractor:
    return SkillExtractor()
