"""Skill-gap analysis.

Given a user's skills and a target (an explicit set of required skills, e.g. a
target job, or the aggregate demand across the market), compute:

* **missing skills** — required skills the user lacks,
* **learning priorities** — missing skills ranked by market demand,
* **readiness score** — fraction of required skills the user already holds.
"""
from __future__ import annotations

from collections import Counter
from typing import Iterable

from ..ai.skill_extraction import SkillExtractor
from ..models.schemas import JobPosting, SkillGapItem, SkillGapReport


class SkillGapAnalyzer:
    """Computes skill gaps and learning priorities."""

    def __init__(self, extractor: SkillExtractor) -> None:
        self.extractor = extractor

    def _normalize(self, skills: Iterable[str]) -> set[str]:
        out: set[str] = set()
        for s in skills:
            out.add(self.extractor.normalize(s) or s.strip().lower())
        return {s for s in out if s}

    def analyze(
        self,
        user_skills: Iterable[str],
        required_skills: Iterable[str],
        market_demand: Counter | None = None,
    ) -> SkillGapReport:
        user = self._normalize(user_skills)
        required = self._normalize(required_skills)
        if not required:
            return SkillGapReport(readiness_score=1.0, matched_skills=sorted(user), missing_skills=[])

        matched = sorted(user & required)
        missing = sorted(required - user)
        readiness = round(len(matched) / len(required), 4)

        demand = market_demand or Counter()
        max_demand = max(demand.values()) if demand else 1
        items: list[SkillGapItem] = []
        for skill in missing:
            d = demand.get(skill, 0)
            # Priority blends market demand (normalised) with a base weight so
            # in-demand-but-missing skills rank first.
            priority = round(0.4 + 0.6 * (d / max_demand if max_demand else 0), 4)
            items.append(SkillGapItem(skill=skill, market_demand=d, priority=priority))
        items.sort(key=lambda i: i.priority, reverse=True)
        return SkillGapReport(readiness_score=readiness, matched_skills=matched, missing_skills=items)

    def analyze_against_market(self, user_skills: Iterable[str], jobs: list[JobPosting]) -> SkillGapReport:
        """Gap of the user against *all skills demanded by the market*."""
        demand = self.extractor.extract_many(j.search_text for j in jobs)
        required = list(demand.keys())
        return self.analyze(user_skills, required, market_demand=demand)
