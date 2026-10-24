"""Listing page → PDF links → text → súmulas."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Protocol

from sumulas.http import FetchError
from sumulas.models import DocumentLink, Sumula
from sumulas.pdf import TextExtractor
from sumulas.tribunais.base import Tribunal

logger = logging.getLogger(__name__)


class Fetcher(Protocol):
    async def get_text(self, url: str) -> str: ...
    async def get_bytes(self, url: str) -> bytes: ...


@dataclass
class Result:
    tribunal: str
    sumulas: list[Sumula] = field(default_factory=list)
    falhas: list[str] = field(default_factory=list)
    ignorados: list[str] = field(default_factory=list)


async def collect(tribunal: Tribunal, fetcher: Fetcher, extract_text: TextExtractor) -> Result:
    result = Result(tribunal=tribunal.slug)

    links: list[DocumentLink] = []
    for page_url in tribunal.listing_urls:
        try:
            html = await fetcher.get_text(page_url)
        except FetchError as exc:
            result.falhas.append(str(exc))
            continue
        links.extend(tribunal.find_links(html, page_url))

    links = list(dict.fromkeys(links))  # same PDF can be listed on more than one page
    logger.info("%s: %d documentos encontrados", tribunal.slug, len(links))

    async def process(link: DocumentLink) -> None:
        try:
            data = await fetcher.get_bytes(link.url)
            text = await asyncio.to_thread(extract_text, data)
        except FetchError as exc:
            result.falhas.append(str(exc))
            return
        except Exception as exc:  # a broken PDF must not stop the other documents
            logger.exception("Erro ao converter %s", link.url)
            result.falhas.append(f"{link.url}: {type(exc).__name__}: {exc}")
            return

        sumula = tribunal.parse(text, link)
        if sumula is None:
            result.ignorados.append(link.url)
        else:
            result.sumulas.append(sumula)

    await asyncio.gather(*(process(link) for link in links))

    unique: dict[int, Sumula] = {}
    for sumula in sorted(result.sumulas, key=lambda s: s.numero):
        unique.setdefault(sumula.numero, sumula)
    result.sumulas = list(unique.values())
    return result
