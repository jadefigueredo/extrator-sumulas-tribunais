"""HTTP client with retries, exponential backoff and a concurrency limit."""

from __future__ import annotations

import asyncio
import logging
import random
from types import TracebackType

import httpx

logger = logging.getLogger(__name__)

RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}

# Alguns tribunais servem o site atrás de um WAF (ex.: Akamai no TRE-PA) que
# responde 403 a clientes sem cara de navegador. Mandamos o conjunto de headers
# que uma navegação real envia para que a coleta não seja bloqueada.
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",  # noqa: E501
    "Accept-Language": "pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}


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
        self._timeout = httpx.Timeout(timeout)
        self._session: httpx.AsyncClient | None = None

    async def __aenter__(self) -> HttpClient:
        self._session = httpx.AsyncClient(
            http2=True, timeout=self._timeout, headers=DEFAULT_HEADERS, follow_redirects=True
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self._session:
            await self._session.aclose()

    async def get_text(self, url: str) -> str:
        body = await self.get_bytes(url)
        return body.decode("utf-8", errors="replace")

    async def get_bytes(self, url: str) -> bytes:
        if self._session is None:
            raise RuntimeError("HttpClient must be used as an async context manager")

        last_error: str = ""
        for attempt in range(1, self.max_attempts + 1):
            try:
                async with self._semaphore:
                    response = await self._session.get(url)
                if response.status_code == 200:
                    return response.content
                last_error = f"HTTP {response.status_code}"
                if response.status_code not in RETRYABLE_STATUS:
                    break
            except httpx.HTTPError as exc:
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
