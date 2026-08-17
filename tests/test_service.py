from ai_job_advisor.ai.embeddings import HashingEmbeddingProvider
from ai_job_advisor.config import Settings
from ai_job_advisor.services.pipeline import JobAdvisorService


def test_service_end_to_end(user):
    service = JobAdvisorService(
        settings=Settings(use_sample_provider=True, embedding_backend="hashing", embedding_dim=128),
        embedder=HashingEmbeddingProvider(dim=128),
    )
    jobs = service.ingest("data", "Ljubljana")
    assert len(jobs) >= 1
    assert all(j.skills for j in jobs)  # skills extracted during ingest

    recs = service.recommend(user, jobs, top_k=3)
    assert len(recs) <= 3 and len(recs) >= 1

    gap = service.skill_gap(user, jobs)
    assert 0.0 <= gap.readiness_score <= 1.0

    coverage = service.market_coverage(jobs)
    assert coverage.total_jobs == len(jobs)
