# 🧭 AI Job Advisor

Aggregate job opportunities from multiple sources and recommend them using **AI** and **graph-based reasoning** — built for **students, graduates, and early-career professionals**.

The platform aggregates vacancies across heterogeneous sources (general boards *and* the "hidden" market of company pages, EURES, startups, agencies), represents users, jobs, skills, companies and industries as a knowledge graph, and produces **explainable, skill-aware** recommendations plus **skill-gap analysis** and **market-coverage analytics**.

> Runs **fully offline out of the box** (sample data + deterministic hashing embeddings). Add API keys and databases to scale up — nothing else changes.

---

## ✨ Features

| # | Feature | Module |
|---|---------|--------|
| 1 | **User profile** (Student / Graduating Soon / Non-Student, skills, education, location, industries) | `models/schemas.py`, Streamlit sidebar |
| 2 | **Job aggregation** (Jooble, Adzuna, EURES + extensible `JobProvider` base) | `aggregation/` |
| 3 | **AI skill extraction** (extract, normalise, taxonomy) | `ai/skill_extraction.py` |
| 4 | **Graph construction** (User, Skill, Job, Company, Industry + relationships) | `graph/builder.py`, `db/neo4j_client.py` |
| 5 | **Recommendation engine** (match score, skill similarity, semantic search, missing skills) | `recommendation/engine.py` |
| 6 | **Skill-gap analysis** (missing skills, learning priorities, readiness score) | `recommendation/skill_gap.py` |
| 7 | **Market-coverage analytics** (by source, hidden-market %, student vs non-student, top skills) | `analytics/coverage.py` |
| 8 | **Dashboard** (recommendations, skill gap, coverage, skill-demand trends) | `app/streamlit_app.py` |

---

## 🏗️ Architecture

```
                         ┌──────────────────────────────┐
                         │       Streamlit Dashboard      │
                         └───────────────┬────────────────┘
                                         │
                         ┌───────────────▼────────────────┐
                         │   JobAdvisorService (facade)    │
                         └──┬─────────┬─────────┬──────────┘
            ┌───────────────┘         │         └───────────────┐
   ┌────────▼─────────┐   ┌───────────▼──────────┐   ┌──────────▼─────────┐
   │  JobAggregator    │   │  RecommendationEngine │   │  CoverageAnalytics │
   │  + providers      │   │  + SkillGapAnalyzer   │   │                    │
   └────────┬──────────┘   └───────────┬──────────┘   └────────────────────┘
            │                          │
   ┌────────▼──────────┐   ┌───────────▼──────────┐
   │ Adzuna / Jooble /  │   │ EmbeddingProvider     │
   │ EURES / Sample     │   │ (local / openai /     │
   └────────────────────┘   │  hashing)             │
                            │ + SkillExtractor       │
                            └────────────────────────┘
            │                          │
   ┌────────▼──────────┐   ┌───────────▼──────────┐
   │   PostgreSQL       │   │       Neo4j           │
   │ (raw + normalised) │   │  (knowledge graph)    │
   └────────────────────┘   └────────────────────────┘
```

**Design principles:** clean layering, a single extensibility seam per concern (`JobProvider`, `EmbeddingProvider`), full type hints, lazy imports of heavy deps so the core is always importable, and graceful degradation (no DB / no keys / no models still runs).

### Project structure
```
ai-job-advisor/
├── app/streamlit_app.py            # Dashboard (UI)
├── src/ai_job_advisor/
│   ├── config.py                   # Env-var settings (typed, cached)
│   ├── models/schemas.py           # Domain dataclasses
│   ├── ai/
│   │   ├── embeddings.py           # local ST / OpenAI-compatible / hashing
│   │   └── skill_extraction.py     # taxonomy + extractor + normaliser
│   ├── aggregation/
│   │   ├── base.py                 # JobProvider ABC
│   │   ├── providers.py            # Adzuna / Jooble / EURES
│   │   ├── sample_provider.py      # offline demo data
│   │   └── aggregator.py           # fan-out + dedup
│   ├── recommendation/
│   │   ├── engine.py               # scoring + semantic search
│   │   └── skill_gap.py            # gap + priorities + readiness
│   ├── analytics/coverage.py       # market coverage
│   ├── graph/builder.py            # Neo4j graph construction
│   ├── db/{postgres,neo4j_client}.py
│   └── services/pipeline.py        # JobAdvisorService facade
├── sql/schema.sql                  # PostgreSQL schema
├── neo4j/schema.cypher             # Neo4j constraints + model + queries
├── scripts/seed_demo_data.py       # Load demo data into DBs
├── tests/                          # 35 unit/integration tests (offline)
├── Dockerfile / docker-compose.yml # app + postgres + neo4j
├── requirements*.txt / pyproject.toml / Makefile / .env.example
└── README.md
```

---

## 🚀 Quick start (local, no Docker, no keys)

```bash
# 1. install minimal deps to run tests, or full deps to run the app
pip install -r requirements.txt          # full (includes streamlit, sentence-transformers, drivers)

# 2. run the dashboard — works fully offline with sample data + hashing embeddings
make run                                  # == PYTHONPATH=src streamlit run app/streamlit_app.py
# open http://localhost:8501
```

Run the tests (no model downloads, no network, no DB):
```bash
pip install -r requirements-dev.txt
make test                                 # 35 passed
```

---

## 🐳 Run the full stack with Docker

```bash
cp .env.example .env        # adjust as needed
docker compose up --build
```

This starts:
- **app** → Streamlit at <http://localhost:8501>
- **postgres** → 5432 (schema auto-loaded from `sql/schema.sql`)
- **neo4j** → browser <http://localhost:7474>, bolt 7687 (`neo4j/neo4jpassword`)

Seed demo data into the databases:
```bash
docker compose exec app python scripts/seed_demo_data.py
```

---

## ⚙️ Configuration (environment variables)

All configuration is via env vars (see `.env.example`). Highlights:

| Variable | Default | Meaning |
|----------|---------|---------|
| `EMBEDDING_BACKEND` | `hashing` | `hashing` (offline) · `local` (sentence-transformers) · `openai` (OpenAI-compatible API) |
| `ST_MODEL_NAME` | `all-MiniLM-L6-v2` | local embedding model |
| `OPENAI_BASE_URL` / `OPENAI_API_KEY` / `OPENAI_EMBEDDING_MODEL` | — | works with OpenAI, Azure, **Ollama**, LM Studio, vLLM, … |
| `USE_SAMPLE_PROVIDER` | `true` | include built-in offline jobs |
| `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` / `ADZUNA_COUNTRY` | — | enable Adzuna |
| `JOOBLE_API_KEY` | — | enable Jooble |
| `EURES_ENABLED` | `false` | enable EURES integration point |
| `NEO4J_ENABLED` + `NEO4J_*` | `false` | enable graph persistence |
| `PG_*` | — | PostgreSQL connection |

### Switching to real embeddings
```bash
# Local, private, no API cost:
export EMBEDDING_BACKEND=local ST_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
# Or an OpenAI-compatible endpoint (incl. a local Ollama server):
export EMBEDDING_BACKEND=openai OPENAI_BASE_URL=http://localhost:11434/v1 OPENAI_API_KEY=ollama
```

---

## 🧠 How it works

- **Skill extraction** matches an ESCO-inspired taxonomy (canonical → aliases) against job text with word-boundary, longest-alias-first matching, then normalises to canonical names. Deterministic and explainable.
- **Embeddings** place profiles and jobs in a shared vector space for **semantic search**; the default `hashing` backend is offline & deterministic, swappable for neural encoders without code changes.
- **Recommendation** blends *semantic similarity* and *skill overlap* into a match score, with a small student-friendliness boost, and surfaces matched/missing skills per job.
- **Skill gap** compares the user against a target role (or the whole market), ranking missing skills by *demand × gap* and computing a readiness score.
- **Coverage** quantifies the **hidden market**: the share of jobs from non-mainstream sources a single board would miss.
- **Graph** (Neo4j) enables relational reasoning — e.g. ranking jobs by skills shared with the user, *including transferable skills* one hop away via `RELATED_TO`.

---

## 🔌 Extending: add a new job source

```python
from ai_job_advisor.aggregation.base import JobProvider
from ai_job_advisor.models.schemas import JobPosting

class MyPortalProvider(JobProvider):
    name = "myportal"
    @property
    def is_available(self) -> bool: ...
    def fetch(self, query: str, location: str = "", limit: int = 25) -> list[JobPosting]:
        ...  # return list[JobPosting]; never raise — log and return [] on error
```
Register it in `JobAggregator.from_settings` (or pass providers directly). No other code changes.

---

## ✅ Testing
35 tests cover skill extraction, embeddings, aggregation/dedup, recommendation ranking, skill-gap logic, coverage analytics, and the end-to-end service — all offline.
```bash
make test
```

---

## 📓 Notes & limitations
- Provider endpoint contracts (Adzuna, Jooble) are implemented to commonly documented shapes; **verify against current provider docs** before production. EURES has no simple public search API — `EuresProvider` is a clearly-marked integration point.
- This is a **candidate-facing decision-support tool** (it recommends; it does not auto-reject candidates for employers). In the EU, AI used in recruitment is **high-risk** under the AI Act — keep humans in the loop, log recommendations (`recommendation_log`), avoid inferring sensitive traits, and follow GDPR (consent, data minimisation) for any real user data.
- The skill taxonomy is a seed; in production, import the full **ESCO** skill/occupation graph to populate `Skill` nodes (`esco_uri`) and `RELATED_TO` edges.

## 📄 License
MIT (add your preferred license file).
