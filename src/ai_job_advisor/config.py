"""Application configuration loaded from environment variables.

Kept dependency-free (no pydantic-settings) so the config layer is importable
in any environment, including minimal CI. Values are read once at import time
via :func:`get_settings`.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


def _get(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def _get_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True, frozen=True)
class Settings:
    """Typed application settings."""

    # --- Embeddings -------------------------------------------------------
    # backend: "local" (sentence-transformers), "openai" (OpenAI-compatible),
    # or "hashing" (deterministic, offline, no model download).
    embedding_backend: str = "hashing"
    embedding_dim: int = 384
    st_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"

    # OpenAI-compatible endpoint (works with OpenAI, Azure, Ollama, LM Studio…)
    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"

    # --- PostgreSQL -------------------------------------------------------
    pg_host: str = "localhost"
    pg_port: int = 5432
    pg_db: str = "job_advisor"
    pg_user: str = "advisor"
    pg_password: str = "advisor"

    # --- Neo4j ------------------------------------------------------------
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "neo4jpassword"
    neo4j_enabled: bool = False

    # --- Job provider credentials ----------------------------------------
    adzuna_app_id: str = ""
    adzuna_app_key: str = ""
    adzuna_country: str = "gb"
    jooble_api_key: str = ""
    eures_enabled: bool = False

    # --- Behaviour --------------------------------------------------------
    use_sample_provider: bool = True
    default_results_per_source: int = 25

    @property
    def pg_dsn(self) -> str:
        return (
            f"postgresql://{self.pg_user}:{self.pg_password}"
            f"@{self.pg_host}:{self.pg_port}/{self.pg_db}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        embedding_backend=_get("EMBEDDING_BACKEND", "hashing"),
        embedding_dim=int(_get("EMBEDDING_DIM", "384")),
        st_model_name=_get("ST_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"),
        openai_base_url=_get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        openai_api_key=_get("OPENAI_API_KEY", ""),
        openai_embedding_model=_get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        pg_host=_get("PG_HOST", "localhost"),
        pg_port=int(_get("PG_PORT", "5432")),
        pg_db=_get("PG_DB", "job_advisor"),
        pg_user=_get("PG_USER", "advisor"),
        pg_password=_get("PG_PASSWORD", "advisor"),
        neo4j_uri=_get("NEO4J_URI", "bolt://localhost:7687"),
        neo4j_user=_get("NEO4J_USER", "neo4j"),
        neo4j_password=_get("NEO4J_PASSWORD", "neo4jpassword"),
        neo4j_enabled=_get_bool("NEO4J_ENABLED", False),
        adzuna_app_id=_get("ADZUNA_APP_ID", ""),
        adzuna_app_key=_get("ADZUNA_APP_KEY", ""),
        adzuna_country=_get("ADZUNA_COUNTRY", "gb"),
        jooble_api_key=_get("JOOBLE_API_KEY", ""),
        eures_enabled=_get_bool("EURES_ENABLED", False),
        use_sample_provider=_get_bool("USE_SAMPLE_PROVIDER", True),
        default_results_per_source=int(_get("DEFAULT_RESULTS_PER_SOURCE", "25")),
    )
