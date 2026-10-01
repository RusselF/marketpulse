import logging
import sys

from marketpulse.db import connect, upsert_products
from marketpulse.sources import books_toscrape, dummyjson
from marketpulse.validation import validate

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("marketpulse")

SOURCES = {
    "dummyjson": dummyjson.fetch_products,
    "books_toscrape": books_toscrape.fetch_products,
}


def main() -> None:
    names = sys.argv[1:] or list(SOURCES)
    unknown = set(names) - set(SOURCES)
    if unknown:
        raise SystemExit(f"source tidak dikenal: {', '.join(sorted(unknown))}")

    results: dict[str, str] = {}
    with connect() as conn:
        for name in names:
            try:
                items = SOURCES[name]()
                valid, rejected = validate(items)
                for r in rejected:
                    log.warning("reject %s/%s: %s", r.product.source, r.product.external_id, r.reason)
                n = upsert_products(conn, valid)
                results[name] = f"ok ({n} rows, {len(rejected)} rejected)"
            except Exception:
                log.exception("source %s gagal", name)
                results[name] = "FAILED"

    for name, status in results.items():
        log.info("ringkasan %-16s %s", name, status)
    if any(s == "FAILED" for s in results.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()