"""Job aggregator.

Fans a query out across all configured providers, merges results, and
deduplicates the *same logical role* seen on multiple sources via
``JobPosting.content_hash``. When a duplicate is found, mainstream sources are
preferred as the canonical record but the alternate source is remembered so
coverage analytics can still see it.
"""
from __future__ import annotations

import logging

from ..config import Settings, get_settings
from ..models.schemas import JobPosting
from .base import JobProvider
from .providers import AdzunaProvider, EuresProvider, JoobleProvider
from .sample_provider import SampleProvider

logger = logging.getLogger(__name__)


class JobAggregator:
    """Aggregates and deduplicates postings from multiple providers."""

    def __init__(self, providers: list[JobProvider]) -> None:
        self.providers = providers

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> "JobAggregator":
        s = settings or get_settings()
        providers: list[JobProvider] = []
        if s.use_sample_provider:
            providers.append(SampleProvider())
        for provider in (AdzunaProvider(s), JoobleProvider(s), EuresProvider(s)):
            if provider.is_available:
                providers.append(provider)
        if not providers:
            logger.warning("No providers available; falling back to SampleProvider.")
            providers.append(SampleProvider())
        return cls(providers)

    def aggregate(self, query: str, location: str = "", limit_per_source: int = 25) -> list[JobPosting]:
        collected: dict[str, JobPosting] = {}
        for provider in self.providers:
            try:
                postings = provider.fetch(query, location, limit_per_source)
            except Exception as exc:  # noqa: BLE001 - defensive: never let one source break all
                logger.warning("Provider %s failed: %s", provider.name, exc)
                continue
            for posting in postings:
                key = posting.content_hash
                existing = collected.get(key)
                if existing is None:
                    collected[key] = posting
                elif existing.is_from_hidden_market and not posting.is_from_hidden_market:
                    # Prefer the mainstream source as canonical record.
                    collected[key] = posting
        return list(collected.values())
