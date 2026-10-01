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

CREATE INDEX IF NOT EXISTS idx_price_history_lookup
    ON price_history (source, external_id, observed_at DESC);