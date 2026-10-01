# MarketPulse

External price data acquisition platform. Pulls product and price data from
multiple sources (REST API, static HTML, dynamic sites), normalizes it into one
model, and stores it idempotently in PostgreSQL.

Built phase by phase as a learning project for data platform engineering.

## Architecture

```text
 REST API ──► httpx ────────┐
 HTML site ─► httpx + BS4 ──┼─► Product (normalized) ─► PostgreSQL (UPSERT)
 JS site ───► Playwright ───┘
```

## Quick start

```bash
docker compose up -d                 # PostgreSQL on localhost:5433
python -m venv .venv && source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m marketpulse.run            # all sources
python -m marketpulse.run dummyjson  # a single source
pytest
```

## Design decisions

- **Composite primary key `(source, external_id)`**: IDs from different sources never collide.
- **UPSERT (`ON CONFLICT DO UPDATE`)**: re-running a job never duplicates rows (idempotent).
- **`raw` JSONB column**: keeps the original payload so data can be reprocessed without re-fetching.
- **Pure parsing functions** (`parse_listing`): tested offline against saved HTML fixtures.
- **Per-source failure isolation**: one failing source does not stop the others.
- **`Decimal` for prices**, never `float`.

## Progress

- [x] Phase 1: API acquisition (httpx, pagination, UPSERT)
- [x] Phase 2: HTML scraper (BeautifulSoup), normalized `Product` model, parser tests
- [ ] Phase 3: Dynamic sites (Playwright)
- [ ] Phase 4: Reliability (retry, backoff, rate limiting)
- [ ] Phase 5: Async and concurrency
- [ ] Phase 6: Data integrity (price history, validation)
- [ ] Phase 7-9: Pipeline stages, scheduler, full Docker setup

## Known limitations

- Price history is overwritten on each run (fixed in Phase 6).
- Books `category` is not captured from listing pages.