import asyncio
import logging
import time
from collections.abc import Awaitable, Callable

import httpx

from marketpulse.http_client import RETRY_STATUS, backoff_delay

log = logging.getLogger(__name__)


class AsyncRateLimiter:
    """Membagikan 'slot waktu' mulai request, aman untuk banyak coroutine."""

    def __init__(self, min_interval: float):
        self.min_interval = min_interval
        self._lock = asyncio.Lock()
        self._next = 0.0

    async def wait(self) -> None:
        async with self._lock:  # reservasi slot harus atomik
            now = time.monotonic()
            start = max(now, self._next)
            self._next = start + self.min_interval
        if start > now:
            await asyncio.sleep(start - now)  # tidur di luar lock


class AsyncResilientClient:
    def __init__(
        self,
        base_url: str = "",
        *,
        max_concurrency: int = 5,
        max_retries: int = 4,
        backoff_base: float = 0.5,
        backoff_cap: float = 30.0,
        min_interval: float = 0.1,
        timeout: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ):
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(timeout),
            headers={"User-Agent": "marketpulse/0.1 (learning project)"},
            follow_redirects=True,
            transport=transport,
        )
        self._sem = asyncio.Semaphore(max_concurrency)
        self._limiter = AsyncRateLimiter(min_interval)
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.backoff_cap = backoff_cap
        self._sleep = sleep

    async def __aenter__(self) -> "AsyncResilientClient":
        return self

    async def __aexit__(self, *exc) -> None:
        await self._client.aclose()

    async def get(self, url: str, **kwargs) -> httpx.Response:
        for attempt in range(self.max_retries + 1):
            await self._limiter.wait()
            resp: httpx.Response | None = None
            try:
                async with self._sem:  # slot hanya dipegang saat request berlangsung
                    resp = await self._client.get(url, **kwargs)
            except httpx.TransportError as exc:
                if attempt == self.max_retries:
                    raise
                reason = type(exc).__name__
            else:
                if resp.status_code not in RETRY_STATUS or attempt == self.max_retries:
                    return resp
                reason = f"HTTP {resp.status_code}"

            delay = backoff_delay(attempt, resp, self.backoff_base, self.backoff_cap)
            log.warning("retry %d/%d untuk %s (%s), tunggu %.2fs",
                        attempt + 1, self.max_retries, url, reason, delay)
            await self._sleep(delay)

        raise RuntimeError("tidak tercapai")