import logging
import random
import time
from collections.abc import Callable
import httpx

log = logging.getLogger(__name__)

RETRY_STATUS = {429, 500, 502, 503, 504}


class RateLimiter:
    """jeda minimum antar request (single-thread)."""

    def __init__(self, min_interval: float):
        self.min_interval = min_interval
        self._last = 0.0

    def wait(self) -> None:
        elapsed = time.monotonic() - self._last
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last = time.monotonic()

class ResilientClient:
    def __init__(
        self,
        base_url: str = "",
        *,
        max_retries: int = 4,
        backoff_base: float = 0.5,
        backoff_cap: float = 30.0,
        min_interval: float = 0.2,
        timeout: float = 10.0,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self._client = httpx.Client(
            base_url=base_url,
            timeout=httpx.Timeout(timeout),
            headers={"User-Agent": "marketpulse/0.1 (learning project)"},
            follow_redirects=True,
            transport=transport,
        )
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.backoff_cap = backoff_cap
        self._limiter = RateLimiter(min_interval)
        self._sleep = sleep

    def __enter__(self) -> "ResilientClient":
        return self

    def __exit__(self, *exc) -> None:
        self._client.close()

    def _delay(self, attempt: int, resp: httpx.Response | None) -> float:
        # Server meminta jeda eksplisit? Patuhi.
        if resp is not None and resp.status_code == 429:
            retry_after = resp.headers.get("Retry-After", "")
            if retry_after.isdigit():
                return min(float(retry_after), self.backoff_cap)
        # Exponential backoff dengan "full jitter"
        ceiling = min(self.backoff_cap, self.backoff_base * 2**attempt)
        return random.uniform(0, ceiling)

    def get(self, url: str, **kwargs) -> httpx.Response:
        for attempt in range(self.max_retries + 1):
            self._limiter.wait()
            resp: httpx.Response | None = None
            try:
                resp = self._client.get(url, **kwargs)
            except httpx.TransportError as exc:  # timeout, koneksi putus, DNS, dll.
                if attempt == self.max_retries:
                    raise
                reason = type(exc).__name__
            else:
                if resp.status_code not in RETRY_STATUS or attempt == self.max_retries:
                    return resp  # sukses, error permanen (404), atau jatah retry habis
                reason = f"HTTP {resp.status_code}"

            delay = self._delay(attempt, resp)
            log.warning(
                "retry %d/%d untuk %s (%s), tunggu %.2fs",
                attempt + 1, self.max_retries, url, reason, delay,
            )
            self._sleep(delay)

        raise RuntimeError("tidak tercapai")


def make_client(base_url: str = "") -> ResilientClient:
    return ResilientClient(base_url)