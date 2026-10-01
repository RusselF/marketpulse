import psycopg
from psycopg.types.json import Jsonb

from marketpulse.models import Product

UPSERT_SQL = """
INSERT INTO products (source, external_id, title, price, category, raw, fetched_at)
VALUES (%s, %s, %s, %s, %s, %s, now())
ON CONFLICT (source, external_id) DO UPDATE SET
    title      = EXCLUDED.title,
    price      = EXCLUDED.price,
    category   = EXCLUDED.category,
    raw        = EXCLUDED.raw,
    fetched_at = now();
"""
HISTORY_SQL = """
INSERT INTO price_history (source, external_id, price)
SELECT %(source)s::text, %(external_id)s::text, %(price)s::numeric
WHERE %(price)s::numeric IS DISTINCT FROM (
    SELECT h.price FROM price_history h
    WHERE h.source = %(source)s::text AND h.external_id = %(external_id)s::text
    ORDER BY h.observed_at DESC, h.id DESC
    LIMIT 1
);
"""

def connect() -> psycopg.Connection:
    return psycopg.connect(
        "postgresql://marketpulse:marketpulse@localhost:5433/marketpulse",
        autocommit=True,
    )


def upsert_products(conn: psycopg.Connection, items: list[Product]) -> int:
    rows = [(p.source, p.external_id, p.title, p.price, p.category, Jsonb(p.raw)) for p in items]
    history = [{"source": p.source, "external_id": p.external_id, "price": p.price} for p in items]
    with conn.transaction():  # keduanya berhasil atau keduanya dibatalkan
        with conn.cursor() as cur:
            cur.executemany(UPSERT_SQL, rows)      # produk harus ada dulu (foreign key)
            cur.executemany(HISTORY_SQL, history)  # catat hanya kalau harga beda dari catatan terakhir
    return len(rows)