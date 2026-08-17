CREATE TABLE IF NOT EXISTS companies (
    company_id   SERIAL PRIMARY KEY,
    name_norm    TEXT UNIQUE NOT NULL,
    website      TEXT,
    industry     TEXT,
    size_band    TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS jobs (
    job_id              SERIAL PRIMARY KEY,
    content_hash        TEXT UNIQUE NOT NULL,
    external_id         TEXT,
    title               TEXT NOT NULL,
    company             TEXT,
    description         TEXT,
    source              TEXT NOT NULL,
    location            TEXT,
    industry            TEXT,
    url                 TEXT,
    is_student_friendly BOOLEAN NOT NULL DEFAULT FALSE,
    posted_at           TIMESTAMPTZ,
    first_seen          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_jobs_source     ON jobs (source);
CREATE INDEX IF NOT EXISTS idx_jobs_location   ON jobs (location);
CREATE INDEX IF NOT EXISTS idx_jobs_posted_at  ON jobs (posted_at);

-- A logical job can be seen on multiple sources; this preserves coverage signal.
CREATE TABLE IF NOT EXISTS job_source_link (
    content_hash TEXT NOT NULL,
    source       TEXT NOT NULL,
    source_url   TEXT,
    first_seen   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (content_hash, source)
);

CREATE TABLE IF NOT EXISTS skills (
    skill_id        SERIAL PRIMARY KEY,
    canonical_name  TEXT UNIQUE NOT NULL,
    skill_type      TEXT,            -- 'skill' | 'knowledge'
    esco_uri        TEXT
);

CREATE TABLE IF NOT EXISTS job_skills (
    job_hash        TEXT NOT NULL,
    skill_id        INTEGER NOT NULL REFERENCES skills(skill_id),
    requirement     TEXT NOT NULL DEFAULT 'essential',  -- 'essential' | 'optional'
    confidence      REAL DEFAULT 1.0,
    PRIMARY KEY (job_hash, skill_id)
);

CREATE TABLE IF NOT EXISTS users (
    user_id          TEXT PRIMARY KEY,
    profile_type     TEXT NOT NULL,  -- 'student' | 'graduating_soon' | 'non_student'
    education        TEXT,
    location         TEXT,
    consent_state    TEXT NOT NULL DEFAULT 'granted',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_skills (
    user_id     TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    skill_id    INTEGER NOT NULL REFERENCES skills(skill_id),
    proficiency TEXT,
    source      TEXT DEFAULT 'declared',  -- 'declared' | 'inferred'
    PRIMARY KEY (user_id, skill_id)
);

CREATE TABLE IF NOT EXISTS user_industries (
    user_id   TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    industry  TEXT NOT NULL,
    PRIMARY KEY (user_id, industry)
);

-- Recommendation log: auditability for transparency / oversight requirements.
CREATE TABLE IF NOT EXISTS recommendation_log (
    rec_id        SERIAL PRIMARY KEY,
    user_id       TEXT NOT NULL,
    job_hash      TEXT NOT NULL,
    model_version TEXT,
    score         REAL,
    rank          INTEGER,
    explanation   JSONB,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_reclog_user ON recommendation_log (user_id);
