import asyncio
import time

from marketpulse.async_http_client import AsyncResilientClient
from marketpulse.http_client import ResilientClient
from marketpulse.sources.books_toscrape import parse_listing

BASE = "https://books.toscrape.com/"


def get_urls() -> list[str]:
    with ResilientClient() as c:
        r = c.get(BASE)
        items, _ = parse_listing(r.content, str(r.url))
    return [i.raw["url"] for i in items]  # 20 URL halaman detail


def run_sync(urls: list[str]) -> list:
    with ResilientClient(min_interval=0.1) as c:
        return [c.get(u).status_code for u in urls]


async def run_async(urls: list[str], concurrency: int) -> list:
    async with AsyncResilientClient(max_concurrency=concurrency, min_interval=0.1) as c:
        results = await asyncio.gather(*(c.get(u) for u in urls), return_exceptions=True)
    return [r.status_code if not isinstance(r, Exception) else repr(r) for r in results]


if __name__ == "__main__":
    urls = get_urls()

    t0 = time.perf_counter()
    run_sync(urls)
    print(f"sync                -> {len(urls)} halaman, {time.perf_counter() - t0:5.1f}s")

    for n in (1, 5, 10):
        t0 = time.perf_counter()
        statuses = asyncio.run(run_async(urls, n))
        ok = sum(1 for s in statuses if s == 200)
        print(f"async concurrency={n:<2} -> {ok}/{len(urls)} ok, {time.perf_counter() - t0:5.1f}s")