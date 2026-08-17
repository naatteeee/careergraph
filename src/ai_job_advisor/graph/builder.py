"""Graph construction.

Projects the domain (users, jobs, skills, companies, industries) into the
Neo4j property graph using idempotent ``MERGE`` queries that realise the
schema:

Nodes:  User, Skill, Job, Company, Industry
Edges:  (User)-[:HAS_SKILL]->(Skill)
        (Job)-[:REQUIRES_SKILL]->(Skill)
        (Company)-[:OFFERS_JOB]->(Job)
        (User)-[:INTERESTED_IN]->(Industry)
        (Skill)-[:RELATED_TO]-(Skill)
        (Company)-[:IN_INDUSTRY]->(Industry)
"""
from __future__ import annotations

import logging

from ..ai.skill_extraction import SkillExtractor
from ..db.neo4j_client import Neo4jClient
from ..models.schemas import JobPosting, UserProfile

logger = logging.getLogger(__name__)


class GraphBuilder:
    """Builds and maintains the job-market knowledge graph."""

    def __init__(self, client: Neo4jClient, extractor: SkillExtractor) -> None:
        self.client = client
        self.extractor = extractor

    def add_job(self, job: JobPosting) -> None:
        skills = job.skills or self.extractor.extract(job.search_text)
        query = """
        MERGE (c:Company {name: $company})
        MERGE (j:Job {content_hash: $hash})
          SET j.title = $title, j.source = $source, j.location = $location,
              j.is_student_friendly = $student, j.url = $url
        MERGE (c)-[:OFFERS_JOB]->(j)
        WITH j, c
        FOREACH (sk IN $skills |
            MERGE (s:Skill {name: sk})
            MERGE (j)-[:REQUIRES_SKILL]->(s)
        )
        WITH j, c
        FOREACH (_ IN CASE WHEN $industry <> '' THEN [1] ELSE [] END |
            MERGE (i:Industry {name: $industry})
            MERGE (c)-[:IN_INDUSTRY]->(i)
        )
        """
        with self.client.session() as s:
            s.run(  # type: ignore[attr-defined]
                query,
                company=job.company or "Unknown",
                hash=job.content_hash,
                title=job.title,
                source=job.source,
                location=job.location,
                student=job.is_student_friendly,
                url=job.url,
                skills=skills,
                industry=job.industry,
            )

    def add_user(self, user: UserProfile) -> None:
        norm_skills = [self.extractor.normalize(s) or s.lower() for s in user.skills]
        query = """
        MERGE (u:User {user_id: $user_id})
          SET u.profile_type = $ptype, u.location = $location
        WITH u
        FOREACH (sk IN $skills |
            MERGE (s:Skill {name: sk})
            MERGE (u)-[:HAS_SKILL]->(s)
        )
        WITH u
        FOREACH (ind IN $industries |
            MERGE (i:Industry {name: ind})
            MERGE (u)-[:INTERESTED_IN]->(i)
        )
        """
        with self.client.session() as s:
            s.run(  # type: ignore[attr-defined]
                query,
                user_id=user.user_id,
                ptype=user.profile_type.value,
                location=user.location,
                skills=[s for s in norm_skills if s],
                industries=user.preferred_industries,
            )

    def link_related_skills(self, related_pairs: list[tuple[str, str]]) -> None:
        """Add RELATED_TO edges (e.g. from an ESCO skill graph import)."""
        query = """
        UNWIND $pairs AS pair
        MERGE (a:Skill {name: pair[0]})
        MERGE (b:Skill {name: pair[1]})
        MERGE (a)-[:RELATED_TO]-(b)
        """
        with self.client.session() as s:
            s.run(query, pairs=[list(p) for p in related_pairs])  # type: ignore[attr-defined]

    def build_from_jobs(self, jobs: list[JobPosting]) -> None:
        for job in jobs:
            self.add_job(job)
        logger.info("Built graph from %d jobs.", len(jobs))
