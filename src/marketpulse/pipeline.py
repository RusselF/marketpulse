import json
import logging
from collections.abc import Callable
from dataclasses import dataclass

import psycopg

from marketpulse.models import Product
from marketpulse.transform import transform
from marketpulse.validation import validate

log = logging.getLogger(__name__)

MERGE_PRODUCTS_SQL = """
INSERT INTO products (source, external_id, title, price, category, raw, fetched_at)
SELECT source, external_id, title, price, category, raw, now()
FROM stg_products
WHERE run_id = %(run_id)s
ON CONFLICT (source, external_id) DO UPDATE SET
    title      = EXCLUDED.title,
    price      = EXCLUDED.price,
    category   = EXCLUDED.category,
    raw        = EXCLUDED.raw,
    fetched_at = now();
"""

MERGE_HISTORY_SQL = """
INSERT INTO price_history (source, external_id, price)
SELECT s.source, s.external_id, s.price
FROM stg_products s
LEFT JOIN LATERAL (
    SELECT h.price
    FROM price_history h
    WHERE h.source = s.source AND h.external_id = s.external_id
    ORDER BY h.observed_at DESC, h.id DESC
    LIMIT 1
) last ON TRUE
WHERE s.run_id = %(run_id)s
  AND s.price IS DISTINCT FROM last.price;
"""


@dataclass(frozen=True)
class RunResult:
    run_id: int
    fetched: int
    rejected: int
    loaded: int


def _start_run(conn: psycopg.Connection, source: str) -> int:
    row = conn.execute(
        "INSERT INTO pipeline_runs (source) VALUES (%s) RETURNING run_id", (source,)
    ).fetchone()
    return row[0]


def _finish_run(conn, run_id, status, fetched=None, rejected=None, loaded=None, error=None) -> None:
    conn.execute(
        """UPDATE pipeline_runs
           SET status = %s, finished_at = now(), fetched = %s, rejected = %s, loaded = %s, error = %s
           WHERE run_id = %s""",
        (status, fetched, rejected, loaded, error, run_id),
    )


def _land_raw(conn: psycopg.Connection, run_id: int, items: list[Product]) -> None:
    with conn.transaction(), conn.cursor() as cur:
        with cur.copy(
            "COPY raw_items (run_id, source, external_id, payload) FROM STDIN"
        ) as copy:
            for p in items:
                copy.write_row((run_id, p.source, p.external_id, json.dumps(p.raw, default=str)))


def _load(conn: psycopg.Connection, run_id: int, items: list[Product]) -> int:
    with conn.transaction():  # staging, merge, riwayat harga, dan pembersihan: atomik
        with conn.cursor() as cur:
            with cur.copy(
                "COPY stg_products (run_id, source, external_id, title, price, category, raw) FROM STDIN"
            ) as copy:
                for p in items:
                    copy.write_row((
                        run_id, p.source, p.external_id, p.title, p.price, p.category,
                        json.dumps(p.raw, default=str),
                    ))
            cur.execute(MERGE_PRODUCTS_SQL, {"run_id": run_id})  # produk dulu (foreign key)
            cur.execute(MERGE_HISTORY_SQL, {"run_id": run_id})
            cur.execute("DELETE FROM stg_products WHERE run_id = %s", (run_id,))
    return len(items)


def run_source(
    conn: psycopg.Connection, name: str, extract: Callable[[], list[Product]]
) -> RunResult:
    run_id = _start_run(conn, name)
    try:
        extracted = extract()
        _land_raw(conn, run_id, extracted)  # tx 1: raw tersimpan apa pun yang terjadi setelahnya
        valid, rejected = validate([transform(p) for p in extracted])
        for r in rejected:
            log.warning("reject %s/%s: %s", r.product.source, r.product.external_id, r.reason)
        loaded = _load(conn, run_id, valid)  # tx 2
        _finish_run(conn, run_id, "success", len(extracted), len(rejected), loaded)
        return RunResult(run_id, len(extracted), len(rejected), loaded)
    except Exception as exc:
        _finish_run(conn, run_id, "failed", error=repr(exc)[:500])
        raise