"""Offline sample provider.

Returns a deterministic set of realistic postings so the whole application —
ingestion, extraction, graph build, recommendation, analytics, dashboard —
runs end-to-end with no API keys and no network. Crucially it includes
postings from *non-mainstream* sources (company pages, EURES, startups) so the
hidden-market analytics are meaningful in the demo.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from ..models.schemas import JobPosting
from .base import JobProvider

_NOW = datetime(2026, 6, 1)

_SAMPLE: list[JobPosting] = [
    JobPosting(
        title="Junior Data Scientist",
        company="DataNest",
        description="Work with Python, pandas and machine learning to build models. SQL and statistics required. Great for students and recent graduates.",
        source="company_page",
        location="Ljubljana",
        industry="Technology",
        url="https://datanest.example/careers/junior-ds",
        is_student_friendly=True,
        posted_at=_NOW - timedelta(days=2),
        external_id="cp-001",
    ),
    JobPosting(
        title="Machine Learning Intern",
        company="Kovac AI",
        description="Internship in NLP and deep learning using PyTorch and TensorFlow. Python and Git essential. Student-friendly, flexible hours.",
        source="startup",
        location="Maribor",
        industry="Technology",
        url="https://kovac.example/jobs/ml-intern",
        is_student_friendly=True,
        posted_at=_NOW - timedelta(days=5),
        external_id="su-002",
    ),
    JobPosting(
        title="Backend Engineer (Python)",
        company="FinFlow",
        description="Build REST APIs with FastAPI and PostgreSQL. Docker and AWS experience valued. Strong communication and teamwork.",
        source="adzuna",
        location="Ljubljana",
        industry="Finance",
        url="https://adzuna.example/jobs/backend-python",
        is_student_friendly=False,
        posted_at=_NOW - timedelta(days=1),
        external_id="az-003",
    ),
    JobPosting(
        title="Data Analyst",
        company="MarketSense",
        description="Data analysis with SQL, Excel and Power BI. Build dashboards in Tableau. Statistics and communication skills required.",
        source="jooble",
        location="Remote",
        industry="Marketing",
        url="https://jooble.example/jobs/data-analyst",
        is_student_friendly=False,
        posted_at=_NOW - timedelta(days=3),
        external_id="jb-004",
    ),
    JobPosting(
        title="Frontend Developer (React)",
        company="Webaria",
        description="Develop UIs with React, TypeScript and JavaScript. Git and REST API integration. Agile teamwork.",
        source="eures",
        location="Graz",
        industry="Technology",
        url="https://eures.example/jobs/frontend-react",
        is_student_friendly=False,
        posted_at=_NOW - timedelta(days=7),
        external_id="eu-005",
    ),
    JobPosting(
        title="Junior Marketing Specialist",
        company="BrightReach",
        description="Digital marketing and sales support. Excel, communication and English required. Ideal for graduating students.",
        source="company_page",
        location="Ljubljana",
        industry="Marketing",
        url="https://brightreach.example/careers/marketing",
        is_student_friendly=True,
        posted_at=_NOW - timedelta(days=4),
        external_id="cp-006",
    ),
    JobPosting(
        title="MLOps Engineer",
        company="FinFlow",
        description="Deploy ML models with Docker and Kubernetes on AWS. Python, Git and data engineering pipelines. NLP a plus.",
        source="agency",
        location="Ljubljana",
        industry="Finance",
        url="https://agency.example/jobs/mlops",
        is_student_friendly=False,
        posted_at=_NOW - timedelta(days=6),
        external_id="ag-007",
    ),
    JobPosting(
        title="Research Assistant — NLP",
        company="Institute Lab",
        description="NLP and machine learning research with Python, PyTorch and statistics. Slovenian and English. Suitable for students.",
        source="university_portal",
        location="Ljubljana",
        industry="Research",
        url="https://institute.example/jobs/ra-nlp",
        is_student_friendly=True,
        posted_at=_NOW - timedelta(days=8),
        external_id="up-008",
    ),
]


class SampleProvider(JobProvider):
    """Yields built-in sample data, optionally filtered by query/location."""

    name = "sample"

    def fetch(self, query: str, location: str = "", limit: int = 25) -> list[JobPosting]:
        results = list(_SAMPLE)
        if location:
            loc = location.strip().lower()
            filtered = [j for j in results if loc in j.location.lower() or j.location.lower() == "remote"]
            results = filtered or results
        if query:
            q = query.strip().lower()
            results = [j for j in results if q in j.search_text.lower()] or results
        return results[:limit]
