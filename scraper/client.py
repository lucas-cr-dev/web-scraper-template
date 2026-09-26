"""HTTP client with retries, exponential backoff and rate limiting."""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass
from typing import Callable

import httpx

log = logging.getLogger(__name__)

RETRY_STATUS = {429, 500, 502, 503, 504}


@dataclass
class ClientConfig:
    user_agent: str = "web-scraper-template/1.0"
    delay: float = 1.0  # minimum seconds between requests
    max_retries: int = 3
    backoff_base: float = 1.0
    backoff_max: float = 30.0
    timeout: float = 15.0
    proxy: str | None = None


class RateLimiter:
    """Ensures at least `interval` seconds between consecutive calls."""

    def __init__(
        self,
        interval: float,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.interval = max(0.0, interval)
        self._clock = clock
        self._sleep = sleep
        self._last: float | None = None

    def wait(self) -> float:
        """Block until the next call is allowed. Returns seconds slept."""
        now = self._clock()
        slept = 0.0
        if self._last is not None:
            remaining = self.interval - (now - self._last)
            if remaining > 0:
                self._sleep(remaining)
                slept = remaining
                now = self._clock()
        self._last = now
        return slept


def backoff_delay(attempt: int, base: float, maximum: float, jitter: bool = True) -> float:
    """Exponential backoff: base * 2**attempt, capped, with optional jitter."""
    delay = min(maximum, base * (2**attempt))
    if jitter:
        delay = delay * (0.5 + random.random() / 2)
    return delay


class Fetcher:
    """Thin wrapper over httpx.Client adding polite defaults."""

    def __init__(
        self,
        config: ClientConfig | None = None,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.config = config or ClientConfig()
        self._sleep = sleep
        self.limiter = RateLimiter(self.config.delay, sleep=sleep)
        kwargs: dict = {
            "headers": {"User-Agent": self.config.user_agent},
            "timeout": self.config.timeout,
            "follow_redirects": True,
        }
        if transport is not None:
            kwargs["transport"] = transport
        elif self.config.proxy:
            kwargs["proxy"] = self.config.proxy
        self._client = httpx.Client(**kwargs)

    def get(self, url: str) -> httpx.Response:
        last_exc: Exception | None = None
        for attempt in range(self.config.max_retries + 1):
            self.limiter.wait()
            try:
                resp = self._client.get(url)
                if resp.status_code in RETRY_STATUS:
                    raise httpx.HTTPStatusError(
                        f"retryable status {resp.status_code}", request=resp.request, response=resp
                    )
                resp.raise_for_status()
                return resp
            except (httpx.TransportError, httpx.HTTPStatusError) as exc:
                status = getattr(getattr(exc, "response", None), "status_code", None)
                if status is not None and status not in RETRY_STATUS:
                    raise  # 4xx such as 404: don't retry
                last_exc = exc
                if attempt >= self.config.max_retries:
                    break
                delay = backoff_delay(attempt, self.config.backoff_base, self.config.backoff_max)
                log.warning("GET %s failed (%s), retry %d in %.1fs", url, exc, attempt + 1, delay)
                self._sleep(delay)
        assert last_exc is not None
        raise last_exc

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "Fetcher":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
