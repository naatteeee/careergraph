"""Job provider abstraction.

Every source (Adzuna, Jooble, EURES, future portals) implements
:class:`JobProvider`. The :class:`~ai_job_advisor.aggregation.aggregator.JobAggregator`
fans out a query across all enabled providers and merges the results, so adding
a new source is a single new subclass with no changes elsewhere.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..models.schemas import JobPosting


class JobProvider(ABC):
    """Interface implemented by every job source."""

    #: Short, stable source identifier (also stored on each JobPosting).
    name: str = "base"

    @abstractmethod
    def fetch(self, query: str, location: str = "", limit: int = 25) -> list[JobPosting]:
        """Return up to ``limit`` postings matching ``query``/``location``.

        Implementations must never raise on network/credential errors; they
        should log and return an empty list so one failing source cannot break
        aggregation.
        """
        raise NotImplementedError

    @property
    def is_available(self) -> bool:
        """Whether the provider is configured well enough to be queried."""
        return True
