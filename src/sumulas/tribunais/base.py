from __future__ import annotations

import re
from abc import ABC, abstractmethod
from urllib.parse import urljoin, urlsplit, urlunsplit

from sumulas.models import DocumentLink, Sumula


class Tribunal(ABC):
    """A court: where its súmulas are listed and how to read each document."""

    slug: str
    nome: str
    listing_urls: tuple[str, ...]

    @abstractmethod
    def find_links(self, html: str, page_url: str) -> list[DocumentLink]:
        """Return the PDF links found on a listing page."""

    @abstractmethod
    def parse(self, text: str, link: DocumentLink) -> Sumula | None:
        """Extract a súmula from a document's text, or ``None`` if it is not one."""


def absolute_url(href: str, page_url: str) -> str:
    """Resolve ``href`` against the page and collapse duplicated slashes in the path."""
    parts = urlsplit(urljoin(page_url, href))
    return urlunsplit(parts._replace(path=re.sub(r"/{2,}", "/", parts.path)))


def section(text: str, start: str, stops: tuple[str, ...] = ()) -> str | None:
    """Return the text after the ``start`` regex and before the first ``stops`` regex."""
    match = re.search(start, text, re.IGNORECASE)
    if not match:
        return None
    rest = text[match.end() :]
    end = len(rest)
    for stop in stops:
        stop_match = re.search(stop, rest, re.IGNORECASE)
        if stop_match:
            end = min(end, stop_match.start())
    return rest[:end].strip() or None


def split_referencias(text: str | None) -> list[str]:
    if not text:
        return []
    items = (item.strip().rstrip(".").strip() for item in text.split(";"))
    return [item for item in items if item]
