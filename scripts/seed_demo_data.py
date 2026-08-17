from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ai_job_advisor.ai.skill_extraction import get_default_extractor  # noqa: E402
from ai_job_advisor.aggregation.sample_provider import SampleProvider  # noqa: E402
from ai_job_advisor.config import get_settings  # noqa: E402
from ai_job_advisor.db.neo4j_client import Neo4jClient  # noqa: E402
from ai_job_advisor.db.postgres import PostgresClient  # noqa: E402
from ai_job_advisor.graph.builder import GraphBuilder  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("seed")


def main() -> None:
    settings = get_settings()
    extractor = get_default_extractor()
    jobs = SampleProvider().fetch(query="", location="", limit=100)
    for job in jobs:
        job.skills = extractor.extract(job.search_text)
    log.info("Loaded %d sample jobs.", len(jobs))

    # Postgres (best-effort)
    try:
        pg = PostgresClient(settings)
        pg.init_schema()
        for job in jobs:
            pg.upsert_job(job)
        pg.close()
        log.info("Persisted jobs to PostgreSQL.")
    except Exception as exc:  # noqa: BLE001
        log.warning("Skipping Postgres seed (%s).", exc)

    # Neo4j (best-effort) — define a few transferable-skill links for the demo
    try:
        client = Neo4jClient(settings)
        client.init_constraints()
        builder = GraphBuilder(client, extractor)
        builder.build_from_jobs(jobs)
        builder.link_related_skills(
            [
                ("pytorch", "tensorflow"),
                ("machine learning", "deep learning"),
                ("postgresql", "sql"),
                ("docker", "kubernetes"),
            ]
        )
        client.close()
        log.info("Built Neo4j graph.")
    except Exception as exc:  # noqa: BLE001
        log.warning("Skipping Neo4j seed (%s).", exc)


if __name__ == "__main__":
    main()
