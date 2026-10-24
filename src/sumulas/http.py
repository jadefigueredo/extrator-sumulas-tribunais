"""HTTP client with retries, exponential backoff and a concurrency limit."""

from __future__ import annotations

import asyncio
import logging
import random
from types import TracebackType

import aiohttp

logger = logging.getLogger(__name__)

RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}
USER_AGENT = (
    "extrator-sumulas-tribunais (+https://github.com/jadefigueredo/extrator-sumulas-tribunais)"
)


class FetchError(Exception):
    """Raised when a URL could not be fetched after every retry."""


class HttpClient:
    def __init__(
        self,
        *,
        max_attempts: int = 4,
        backoff_base: float = 0.5,
        max_concurrency: int = 4,
        timeout: float = 30.0,
    ) -> None:
        self.max_attempts = max_attempts
        self.backoff_base = backoff_base
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> HttpClient:
        self._session = aiohttp.ClientSession(
            timeout=self._timeout, headers={"User-Agent": USER_AGENT}
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self._session:
            await self._session.close()

    async def get_text(self, url: str) -> str:
        body = await self.get_bytes(url)
        return body.decode("utf-8", errors="replace")

    async def get_bytes(self, url: str) -> bytes:
        if self._session is None:
            raise RuntimeError("HttpClient must be used as an async context manager")

        last_error: str = ""
        for attempt in range(1, self.max_attempts + 1):
            try:
                async with self._semaphore, self._session.get(url) as response:
                    if response.status == 200:
                        return await response.read()
                    last_error = f"HTTP {response.status}"
                    if response.status not in RETRYABLE_STATUS:
                        break
            except (TimeoutError, aiohttp.ClientError) as exc:
                last_error = f"{type(exc).__name__}: {exc}"

            if attempt < self.max_attempts:
                delay = self._backoff(attempt)
                logger.warning(
                    "Falha ao baixar %s (%s); tentativa %d/%d, nova tentativa em %.1fs",
                    url,
                    last_error,
                    attempt,
                    self.max_attempts,
                    delay,
                )
                await asyncio.sleep(delay)

        raise FetchError(f"{url}: {last_error}")

    def _backoff(self, attempt: int) -> float:
        """Exponential backoff with full jitter."""
        return random.uniform(0, self.backoff_base * 2 ** (attempt - 1))
