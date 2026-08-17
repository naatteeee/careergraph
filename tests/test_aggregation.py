from ai_job_advisor.aggregation.aggregator import JobAggregator
from ai_job_advisor.aggregation.providers import AdzunaProvider, EuresProvider, JoobleProvider
from ai_job_advisor.aggregation.sample_provider import SampleProvider
from ai_job_advisor.config import Settings
from ai_job_advisor.models.schemas import JobPosting


def test_sample_provider_returns_jobs():
    jobs = SampleProvider().fetch(query="", location="", limit=50)
    assert len(jobs) >= 5
    assert all(isinstance(j, JobPosting) for j in jobs)


def test_unconfigured_http_providers_unavailable():
    s = Settings(adzuna_app_id="", adzuna_app_key="", jooble_api_key="", eures_enabled=False)
    assert AdzunaProvider(s).is_available is False
    assert JoobleProvider(s).is_available is False
    assert EuresProvider(s).is_available is False


def test_unavailable_providers_return_empty():
    s = Settings()
    assert AdzunaProvider(s).fetch("python") == []
    assert JoobleProvider(s).fetch("python") == []


def test_aggregator_dedup_prefers_mainstream():
    hidden = JobPosting(title="Engineer", company="Acme", description="x", source="company_page", location="Ljubljana")
    main = JobPosting(title="Engineer", company="Acme", description="x", source="adzuna", location="Ljubljana")

    class P1:
        name = "company_page"
        is_available = True
        def fetch(self, q, location="", limit=25):
            return [hidden]

    class P2:
        name = "adzuna"
        is_available = True
        def fetch(self, q, location="", limit=25):
            return [main]

    agg = JobAggregator([P1(), P2()])
    out = agg.aggregate("engineer")
    assert len(out) == 1  # deduplicated
    assert out[0].source == "adzuna"  # mainstream preferred


def test_aggregator_survives_failing_provider(sample_jobs):
    class Boom:
        name = "boom"
        is_available = True
        def fetch(self, q, location="", limit=25):
            raise RuntimeError("network down")

    agg = JobAggregator([Boom(), SampleProvider()])
    out = agg.aggregate("")
    assert len(out) >= 5  # sample data still returned despite failing provider


def test_from_settings_falls_back_to_sample():
    agg = JobAggregator.from_settings(Settings(use_sample_provider=True))
    out = agg.aggregate("python", "Ljubljana")
    assert len(out) >= 1
