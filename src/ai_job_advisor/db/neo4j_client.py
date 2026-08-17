"""Neo4j graph persistence and graph-based reasoning.

The ``neo4j`` driver is imported lazily; if Neo4j is disabled or unreachable
the application degrades gracefully (the in-memory recommender still works).
"""
from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Iterator

from ..config import Settings, get_settings

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Wrapper exposing graph construction and graph-recommendation queries."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._driver = None

    def _get_driver(self):
        if self._driver is None:
            from neo4j import GraphDatabase  # lazy import

            self._driver = GraphDatabase.driver(
                self.settings.neo4j_uri,
                auth=(self.settings.neo4j_user, self.settings.neo4j_password),
            )
        return self._driver

    @contextmanager
    def session(self) -> Iterator[object]:
        driver = self._get_driver()
        session = driver.session()
        try:
            yield session
        finally:
            session.close()

    def init_constraints(self) -> None:
        statements = [
            "CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE",
            "CREATE CONSTRAINT job_hash IF NOT EXISTS FOR (j:Job) REQUIRE j.content_hash IS UNIQUE",
            "CREATE CONSTRAINT skill_name IF NOT EXISTS FOR (s:Skill) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT company_name IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE",
            "CREATE CONSTRAINT industry_name IF NOT EXISTS FOR (i:Industry) REQUIRE i.name IS UNIQUE",
        ]
        with self.session() as s:
            for stmt in statements:
                s.run(stmt)  # type: ignore[attr-defined]
        logger.info("Neo4j constraints ensured.")

    def recommend_by_shared_skills(self, user_id: str, top_k: int = 10) -> list[dict]:
        """Graph reasoning: rank jobs by count of skills shared with the user,
        including skills reachable one hop via RELATED_TO (transferable skills).
        """
        query = """
        MATCH (u:User {user_id: $user_id})-[:HAS_SKILL]->(us:Skill)
        OPTIONAL MATCH (us)-[:RELATED_TO]-(rel:Skill)
        WITH u, collect(DISTINCT us) + collect(DISTINCT rel) AS userSkills
        MATCH (j:Job)-[:REQUIRES_SKILL]->(req:Skill)
        WHERE req IN userSkills
        WITH j, count(DISTINCT req) AS overlap
        MATCH (j)-[:REQUIRES_SKILL]->(allReq:Skill)
        WITH j, overlap, count(DISTINCT allReq) AS required
        RETURN j.content_hash AS content_hash, j.title AS title,
               overlap, required,
               toFloat(overlap) / required AS coverage
        ORDER BY coverage DESC, overlap DESC
        LIMIT $top_k
        """
        with self.session() as s:
            result = s.run(query, user_id=user_id, top_k=top_k)  # type: ignore[attr-defined]
            return [dict(record) for record in result]

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None
