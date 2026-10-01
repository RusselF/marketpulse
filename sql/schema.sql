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