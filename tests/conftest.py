"""Shared pytest fixtures."""
from __future__ import annotations

import pytest

from ai_job_advisor.ai.embeddings import HashingEmbeddingProvider
from ai_job_advisor.ai.skill_extraction import get_default_extractor
from ai_job_advisor.aggregation.sample_provider import SampleProvider
from ai_job_advisor.models.schemas import ProfileType, UserProfile


@pytest.fixture
def extractor():
    return get_default_extractor()


@pytest.fixture
def embedder():
    return HashingEmbeddingProvider(dim=128)


@pytest.fixture
def sample_jobs():
    return SampleProvider().fetch(query="", location="", limit=50)


@pytest.fixture
def user():
    return UserProfile(
        user_id="u-test",
        profile_type=ProfileType.STUDENT,
        skills=["Python", "SQL", "machine learning"],
        education="BSc Computer Science",
        location="Ljubljana",
        preferred_industries=["Technology"],
    )
