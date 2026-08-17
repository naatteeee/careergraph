from ai_job_advisor.analytics.coverage import CoverageAnalytics
from ai_job_advisor.models.schemas import JobPosting


def test_coverage_basic(extractor, sample_jobs):
    cov = CoverageAnalytics(extractor)
    report = cov.compute(sample_jobs)
    assert report.total_jobs == len(sample_jobs)
    assert sum(report.jobs_by_source.values()) == report.total_jobs
    assert 0.0 <= report.hidden_market_pct <= 100.0
    assert report.student_jobs + report.non_student_jobs == report.total_jobs
    assert len(report.most_requested_skills) > 0


def test_hidden_market_pct(extractor):
    jobs = [
        JobPosting(title="A", company="C1", source="adzuna", description="python"),
        JobPosting(title="B", company="C2", source="company_page", description="sql"),
        JobPosting(title="C", company="C3", source="eures", description="java"),
        JobPosting(title="D", company="C4", source="startup", description="aws"),
    ]
    cov = CoverageAnalytics(extractor)
    report = cov.compute(jobs)
    # 3 of 4 are non-mainstream -> 75%
    assert report.hidden_market_pct == 75.0


def test_empty(extractor):
    cov = CoverageAnalytics(extractor)
    report = cov.compute([])
    assert report.total_jobs == 0
    assert report.hidden_market_pct == 0.0


def test_most_requested_skills_ranking(extractor):
    jobs = [
        JobPosting(title="A", company="C1", source="adzuna", description="python sql"),
        JobPosting(title="B", company="C2", source="adzuna", description="python docker"),
        JobPosting(title="C", company="C3", source="adzuna", description="python"),
    ]
    cov = CoverageAnalytics(extractor)
    report = cov.compute(jobs)
    top_skill, top_count = report.most_requested_skills[0]
    assert top_skill == "python"
    assert top_count == 3
