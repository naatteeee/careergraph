
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from ..config import Settings, get_settings
from ..models.schemas import JobPosting
from .base import JobProvider

logger = logging.getLogger(__name__)


def _safe_requests():
    try:
        import requests  # lazy import

        return requests
    except Exception:  # pragma: no cover - requests always available in app env
        logger.warning("`requests` not installed; HTTP providers disabled.")
        return None


class AdzunaProvider(JobProvider):
    """Adzuna REST API (https://developer.adzuna.com/)."""

    name = "adzuna"

    def __init__(self, settings: Settings | None = None) -> None:
        s = settings or get_settings()
        self.app_id = s.adzuna_app_id
        self.app_key = s.adzuna_app_key
        self.country = s.adzuna_country

    @property
    def is_available(self) -> bool:
        return bool(self.app_id and self.app_key)

    def fetch(self, query: str, location: str = "", limit: int = 25) -> list[JobPosting]:
        if not self.is_available:
            logger.info("Adzuna credentials missing; skipping.")
            return []
        requests = _safe_requests()
        if requests is None:
            return []
        url = f"https://api.adzuna.com/v1/api/jobs/{self.country}/search/1"
        params: dict[str, Any] = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": limit,
            "what": query,
            "where": location,
            "content-type": "application/json",
        }
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            payload = resp.json()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Adzuna fetch failed: %s", exc)
            return []
        jobs: list[JobPosting] = []
        for item in payload.get("results", []):
            jobs.append(
                JobPosting(
                    title=item.get("title", ""),
                    company=(item.get("company") or {}).get("display_name", ""),
                    description=item.get("description", ""),
                    source=self.name,
                    location=(item.get("location") or {}).get("display_name", ""),
                    industry=(item.get("category") or {}).get("label", ""),
                    url=item.get("redirect_url", ""),
                    external_id=str(item.get("id", "")),
                )
            )
        return jobs


class JoobleProvider(JobProvider):
    """Jooble API (POST https://jooble.org/api/{key})."""

    name = "jooble"

    def __init__(self, settings: Settings | None = None) -> None:
        s = settings or get_settings()
        self.api_key = s.jooble_api_key

    @property
    def is_available(self) -> bool:
        return bool(self.api_key)

    def fetch(self, query: str, location: str = "", limit: int = 25) -> list[JobPosting]:
        if not self.is_available:
            logger.info("Jooble API key missing; skipping.")
            return []
        requests = _safe_requests()
        if requests is None:
            return []
        url = f"https://jooble.org/api/{self.api_key}"
        body = {"keywords": query, "location": location}
        try:
            resp = requests.post(url, json=body, timeout=30)
            resp.raise_for_status()
            payload = resp.json()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Jooble fetch failed: %s", exc)
            return []
        jobs: list[JobPosting] = []
        for item in payload.get("jobs", [])[:limit]:
            jobs.append(
                JobPosting(
                    title=item.get("title", ""),
                    company=item.get("company", ""),
                    description=item.get("snippet", ""),
                    source=self.name,
                    location=item.get("location", ""),
                    url=item.get("link", ""),
                    external_id=str(item.get("id", "")),
                )
            )
        return jobs


class EuresProvider(JobProvider):
    """EURES integration.

    EURES does not expose a simple public REST search API; production
    integration typically goes via the EURES portal data exports / national
    PES feeds or a licensed normalised feed. This provider is a clearly-marked
    extension point: enable it and wire your chosen access method in ``fetch``.
    """

    name = "eures"

    def __init__(self, settings: Settings | None = None) -> None:
        s = settings or get_settings()
        self.enabled = s.eures_enabled

    @property
    def is_available(self) -> bool:
        return self.enabled

    def fetch(self, query: str, location: str = "", limit: int = 25) -> list[JobPosting]:
        if not self.enabled:
            logger.info("EURES integration disabled; skipping.")
            return []
        # TODO: integrate EURES portal export / national PES feed / licensed feed.
        logger.warning("EURES provider enabled but no feed wired; returning empty.")
        return []
