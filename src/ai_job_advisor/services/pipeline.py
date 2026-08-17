"""High-level orchestration service.

Wires the components into a single facade the UI (or a CLI/cron job) can call:
aggregate -> extract skills -> (optionally) persist -> (optionally) build graph,
then recommend / analyse. Persistence and graph build are best-effort: failures
are logged and the in-memory results are still returned.
"""
from __future__ import annotations

import logging

from ..ai.embeddings import EmbeddingProvider, get_embedding_provider
from ..ai.skill_extraction import SkillExtractor, get_default_extractor
from ..aggregation.aggregator import JobAggregator
from ..analytics.coverage import CoverageAnalytics
from ..config import Settings, get_settings
from ..models.schemas import (
    CoverageReport,
    JobPosting,
    Recommendation,
    SkillGapReport,
    UserProfile,
)
from ..recommendation.engine import RecommendationEngine
from ..recommendation.skill_gap import SkillGapAnalyzer

logger = logging.getLogger(__name__)


class JobAdvisorService:
    """Facade over aggregation, AI, recommendation and analytics."""

    def __init__(
        self,
        settings: Settings | None = None,
        embedder: EmbeddingProvider | None = None,
        extractor: SkillExtractor | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.extractor = extractor or get_default_extractor()
        self.embedder = embedder or get_embedding_provider(self.settings)
        self.aggregator = JobAggregator.from_settings(self.settings)
        self.engine = RecommendationEngine(self.embedder, self.extractor)
        self.gap = SkillGapAnalyzer(self.extractor)
        self.coverage = CoverageAnalytics(self.extractor)

    def ingest(self, query: str, location: str = "") -> list[JobPosting]:
        jobs = self.aggregator.aggregate(
            query, location, limit_per_source=self.settings.default_results_per_source
        )
        for job in jobs:
            if not job.skills:
                job.skills = self.extractor.extract(job.search_text)
        logger.info("Ingested %d unique jobs for query=%r location=%r", len(jobs), query, location)
        return jobs

    def recommend(self, user: UserProfile, jobs: list[JobPosting], top_k: int = 10) -> list[Recommendation]:
        return self.engine.recommend(user, jobs, top_k=top_k)

    def skill_gap(self, user: UserProfile, jobs: list[JobPosting]) -> SkillGapReport:
        return self.gap.analyze_against_market(user.skills, jobs)

    def skill_gap_for_job(self, user: UserProfile, job: JobPosting, jobs: list[JobPosting]) -> SkillGapReport:
        demand = self.extractor.extract_many(j.search_text for j in jobs)
        required = job.skills or self.extractor.extract(job.search_text)
        return self.gap.analyze(user.skills, required, market_demand=demand)

    def market_coverage(self, jobs: list[JobPosting]) -> CoverageReport:
        return self.coverage.compute(jobs)
