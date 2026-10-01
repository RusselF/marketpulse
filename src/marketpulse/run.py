import logging
import sys

from marketpulse.db import connect, upsert_products
from marketpulse.pipeline import run_source
from marketpulse.sources import books_toscrape, dummyjson
from marketpulse.validation import validate

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
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

    failed = False
    with connect() as conn:
        for name in names:
            try:
                r = run_source(conn, name, SOURCES[name])
                log.info("ringkasan %-16s run=%d fetched=%d rejected=%d loaded=%d",
                         name, r.run_id, r.fetched, r.rejected, r.loaded)
            except Exception:
                failed = True
                log.exception("source %s gagal", name)
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()