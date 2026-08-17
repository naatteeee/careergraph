"""Core domain models for AI Job Advisor.

These are intentionally plain ``dataclasses`` with type hints so the domain
layer carries no heavy third-party dependency and is trivial to unit-test.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class ProfileType(str, Enum):
    """Lifecycle stage of the user, used to tailor recommendations."""

    STUDENT = "student"
    GRADUATING_SOON = "graduating_soon"
    NON_STUDENT = "non_student"


# Sources we treat as "mainstream / highly visible" job boards. Anything
# coming from a different source counts towards the *hidden* job market.
MAINSTREAM_SOURCES: frozenset[str] = frozenset({"adzuna", "jooble", "linkedin", "mojedelo"})


@dataclass(slots=True)
class JobPosting:
    """A single normalised job posting from any source."""

    title: str
    company: str
    description: str
    source: str
    location: str = ""
    industry: str = ""
    url: str = ""
    skills: list[str] = field(default_factory=list)
    is_student_friendly: bool = False
    posted_at: Optional[datetime] = None
    external_id: str = ""

    @property
    def content_hash(self) -> str:
        """Stable hash used to deduplicate the same role across sources."""
        key = f"{self.title.strip().lower()}|{self.company.strip().lower()}|{self.location.strip().lower()}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]

    @property
    def search_text(self) -> str:
        """Concatenated text used for embedding / semantic search."""
        return " . ".join(
            part for part in [self.title, self.company, self.industry, self.description, " ".join(self.skills)] if part
        )

    @property
    def is_from_hidden_market(self) -> bool:
        return self.source.lower() not in MAINSTREAM_SOURCES


@dataclass(slots=True)
class UserProfile:
    """Profile supplied by a student / graduate / early-career professional."""

    user_id: str
    profile_type: ProfileType = ProfileType.STUDENT
    skills: list[str] = field(default_factory=list)
    education: str = ""
    location: str = ""
    preferred_industries: list[str] = field(default_factory=list)

    @property
    def profile_text(self) -> str:
        return " . ".join(
            part
            for part in [
                self.education,
                self.location,
                " ".join(self.preferred_industries),
                " ".join(self.skills),
            ]
            if part
        )


@dataclass(slots=True)
class Recommendation:
    """A scored job recommendation returned to the user."""

    job: JobPosting
    match_score: float
    semantic_score: float
    skill_similarity: float
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SkillGapItem:
    skill: str
    market_demand: int
    priority: float


@dataclass(slots=True)
class SkillGapReport:
    """Result of comparing a user against a target role / the market."""

    readiness_score: float
    matched_skills: list[str]
    missing_skills: list[SkillGapItem]

    @property
    def learning_priorities(self) -> list[str]:
        return [item.skill for item in sorted(self.missing_skills, key=lambda i: i.priority, reverse=True)]


@dataclass(slots=True)
class CoverageReport:
    """Market-coverage analytics across all aggregated jobs."""

    total_jobs: int
    jobs_by_source: dict[str, int]
    hidden_market_pct: float
    student_jobs: int
    non_student_jobs: int
    most_requested_skills: list[tuple[str, int]]
