"""Market-coverage analytics.

Quantifies the value proposition of multi-source aggregation:

* **jobs by source** — distribution across providers,
* **hidden-market percentage** — share of jobs from non-mainstream sources
  (company pages, EURES, startups, agencies, university portals) that a
  single mainstream board would miss,
* **student vs non-student** — accessibility of the market to early-career users,
* **most requested skills** — top demanded skills across all postings.
"""
from __future__ import annotations

from collections import Counter

from ..ai.skill_extraction import SkillExtractor
from ..models.schemas import CoverageReport, JobPosting


class CoverageAnalytics:
    """Computes coverage statistics over a set of aggregated jobs."""

    def __init__(self, extractor: SkillExtractor) -> None:
        self.extractor = extractor

    def compute(self, jobs: list[JobPosting], top_skills: int = 15) -> CoverageReport:
        total = len(jobs)
        by_source: Counter = Counter(j.source for j in jobs)
        hidden = sum(1 for j in jobs if j.is_from_hidden_market)
        hidden_pct = round(100.0 * hidden / total, 2) if total else 0.0
        student = sum(1 for j in jobs if j.is_student_friendly)

        skill_counter: Counter = Counter()
        for job in jobs:
            skills = job.skills or self.extractor.extract(job.search_text)
            skill_counter.update(skills)

        return CoverageReport(
            total_jobs=total,
            jobs_by_source=dict(by_source.most_common()),
            hidden_market_pct=hidden_pct,
            student_jobs=student,
            non_student_jobs=total - student,
            most_requested_skills=skill_counter.most_common(top_skills),
        )
