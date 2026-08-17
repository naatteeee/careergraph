from collections import Counter

from ai_job_advisor.recommendation.skill_gap import SkillGapAnalyzer


def test_readiness_full(extractor):
    an = SkillGapAnalyzer(extractor)
    report = an.analyze(["Python", "SQL"], ["python", "sql"])
    assert report.readiness_score == 1.0
    assert report.missing_skills == []


def test_readiness_partial(extractor):
    an = SkillGapAnalyzer(extractor)
    report = an.analyze(["Python"], ["python", "sql", "docker", "aws"])
    assert report.readiness_score == 0.25
    assert {i.skill for i in report.missing_skills} == {"sql", "docker", "aws"}


def test_learning_priority_orders_by_demand(extractor):
    an = SkillGapAnalyzer(extractor)
    demand = Counter({"docker": 10, "aws": 2, "sql": 1})
    report = an.analyze(["Python"], ["python", "docker", "aws", "sql"], market_demand=demand)
    # docker is most in demand -> first priority
    assert report.learning_priorities[0] == "docker"


def test_no_required_skills_is_ready(extractor):
    an = SkillGapAnalyzer(extractor)
    report = an.analyze(["Python"], [])
    assert report.readiness_score == 1.0


def test_against_market(extractor, sample_jobs):
    an = SkillGapAnalyzer(extractor)
    report = an.analyze_against_market(["Python", "SQL"], sample_jobs)
    assert 0.0 <= report.readiness_score <= 1.0
    assert len(report.missing_skills) > 0
    # priorities should be sorted descending
    priorities = [i.priority for i in report.missing_skills]
    assert priorities == sorted(priorities, reverse=True)
