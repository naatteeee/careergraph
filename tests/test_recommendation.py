from ai_job_advisor.models.schemas import JobPosting, ProfileType, UserProfile
from ai_job_advisor.recommendation.engine import RecommendationEngine


def _engine(embedder, extractor):
    return RecommendationEngine(embedder, extractor)


def test_recommend_returns_sorted(embedder, extractor, user, sample_jobs):
    engine = _engine(embedder, extractor)
    recs = engine.recommend(user, sample_jobs, top_k=5)
    assert len(recs) == 5
    scores = [r.match_score for r in recs]
    assert scores == sorted(scores, reverse=True)
    assert all(0.0 <= r.match_score <= 1.0 for r in recs)


def test_matched_and_missing_skills(embedder, extractor):
    engine = _engine(embedder, extractor)
    user = UserProfile(user_id="u1", skills=["Python"], profile_type=ProfileType.NON_STUDENT)
    job = JobPosting(
        title="Dev", company="C", source="adzuna",
        description="Python and Docker and Kubernetes required",
    )
    recs = engine.recommend(user, [job], top_k=1)
    rec = recs[0]
    assert "python" in rec.matched_skills
    assert "docker" in rec.missing_skills
    assert "kubernetes" in rec.missing_skills


def test_skill_overlap_drives_score(embedder, extractor):
    engine = _engine(embedder, extractor)
    user = UserProfile(user_id="u1", skills=["Python", "machine learning", "pytorch"])
    strong = JobPosting(title="ML", company="A", source="x",
                        description="Python machine learning pytorch")
    weak = JobPosting(title="Sales", company="B", source="x",
                      description="sales marketing communication")
    recs = engine.recommend(user, [strong, weak], top_k=2)
    assert recs[0].job.title == "ML"
    assert recs[0].skill_similarity > recs[1].skill_similarity


def test_student_boost(embedder, extractor):
    engine = _engine(embedder, extractor)
    student = UserProfile(user_id="s", skills=["Python"], profile_type=ProfileType.STUDENT)
    base = dict(title="Role", company="C", source="x", description="Python")
    friendly = JobPosting(is_student_friendly=True, **base)
    not_friendly = JobPosting(is_student_friendly=False, **base)
    # same hash would dedup, so give distinct titles
    friendly.title = "Friendly Role"
    not_friendly.title = "Other Role"
    recs = engine.recommend(student, [not_friendly, friendly], top_k=2)
    friendly_rec = next(r for r in recs if r.job.title == "Friendly Role")
    other_rec = next(r for r in recs if r.job.title == "Other Role")
    assert friendly_rec.match_score >= other_rec.match_score


def test_semantic_search(embedder, extractor, sample_jobs):
    engine = _engine(embedder, extractor)
    results = engine.semantic_search("machine learning python", sample_jobs, top_k=3)
    assert len(results) == 3
    assert all(0.0 <= score <= 1.0 for _, score in results)


def test_empty_jobs(embedder, extractor, user):
    engine = _engine(embedder, extractor)
    assert engine.recommend(user, [], top_k=5) == []
