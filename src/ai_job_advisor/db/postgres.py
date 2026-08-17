
from __future__ import annotations

import logging
from pathlib import Path

from ..config import Settings, get_settings
from ..models.schemas import JobPosting

logger = logging.getLogger(__name__)

_SCHEMA_PATH = Path(__file__).resolve().parents[3] / "sql" / "schema.sql"


class PostgresClient:
    """Minimal persistence for jobs and skills."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._conn = None

    def connect(self):
        if self._conn is not None:
            return self._conn
        import psycopg  # lazy import

        self._conn = psycopg.connect(self.settings.pg_dsn)
        return self._conn

    def init_schema(self, schema_path: Path | None = None) -> None:
        path = schema_path or _SCHEMA_PATH
        sql = path.read_text(encoding="utf-8")
        conn = self.connect()
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        logger.info("Postgres schema initialised from %s", path)

    def upsert_job(self, job: JobPosting) -> None:
        conn = self.connect()
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO jobs (content_hash, title, company, description, source,
                                  location, industry, url, is_student_friendly, external_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (content_hash) DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    last_seen = NOW();
                """,
                (
                    job.content_hash,
                    job.title,
                    job.company,
                    job.description,
                    job.source,
                    job.location,
                    job.industry,
                    job.url,
                    job.is_student_friendly,
                    job.external_id,
                ),
            )
        conn.commit()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
