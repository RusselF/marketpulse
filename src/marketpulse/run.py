import logging
import sys

from marketpulse.db import connect, upsert_products
from marketpulse.sources import books_toscrape, dummyjson

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

    with connect() as conn:
        for name in names:
            try:
                items = SOURCES[name]()
            except Exception:
                log.exception("source %s gagal, lanjut ke source berikutnya", name)
                continue
            n = upsert_products(conn, items)
            log.info("source=%s upserted=%d", name, n)


if __name__ == "__main__":
    main()