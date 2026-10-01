CREATE TABLE IF NOT EXISTS products (
    source      TEXT        NOT NULL,
    external_id TEXT        NOT NULL,
    title       TEXT        NOT NULL,
    price       NUMERIC(12,2),
    category    TEXT,
    raw         JSONB       NOT NULL,
    fetched_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (source, external_id)
);

CREATE TABLE IF NOT EXISTS price_history (
    id          BIGSERIAL PRIMARY KEY,
    source      TEXT          NOT NULL,
    external_id TEXT          NOT NULL,
    price       NUMERIC(12,2),
    observed_at TIMESTAMPTZ   NOT NULL DEFAULT now(),
    FOREIGN KEY (source, external_id) REFERENCES products (source, external_id)
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id      BIGSERIAL PRIMARY KEY,
    source      TEXT        NOT NULL,
    started_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    status      TEXT        NOT NULL DEFAULT 'running',  -- running | success | failed
    fetched     INTEGER,
    rejected    INTEGER,
    loaded      INTEGER,
    error       TEXT
);

CREATE TABLE IF NOT EXISTS raw_items (
    run_id      BIGINT      NOT NULL REFERENCES pipeline_runs (run_id),
    source      TEXT        NOT NULL,
    external_id TEXT        NOT NULL,
    payload     JSONB       NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_raw_items_run ON raw_items (run_id);

CREATE TABLE IF NOT EXISTS stg_products (
    run_id      BIGINT      NOT NULL REFERENCES pipeline_runs (run_id),
    source      TEXT        NOT NULL,
    external_id TEXT        NOT NULL,
    title       TEXT        NOT NULL,
    price       NUMERIC(12,2),
    category    TEXT,
    raw         JSONB       NOT NULL,
    PRIMARY KEY (run_id, source, external_id)
);

CREATE INDEX IF NOT EXISTS idx_price_history_lookup
    ON price_history (source, external_id, observed_at DESC);