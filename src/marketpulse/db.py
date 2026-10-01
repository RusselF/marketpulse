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


def connect() -> psycopg.Connection:
    return psycopg.connect("postgresql://marketpulse:marketpulse@localhost:5433/marketpulse")


def upsert_products(conn: psycopg.Connection, items: list[Product]) -> int:
    rows = [(p.source, p.external_id, p.title, p.price, p.category, Jsonb(p.raw)) for p in items]
    with conn.cursor() as cur:
        cur.executemany(UPSERT_SQL, rows)
    conn.commit()
    return len(rows)