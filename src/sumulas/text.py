"""Helpers to normalize text extracted from PDFs and parse Brazilian dates."""

from __future__ import annotations

import re
from datetime import date

MESES = {
    "janeiro": 1,
    "fevereiro": 2,
    "março": 3,
    "marco": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}

_NUMERIC_DATE = re.compile(r"\b(\d{1,2})[/.](\d{1,2})[/.](\d{4})\b")
_WRITTEN_DATE = re.compile(r"\b(\d{1,2})\s+de\s+([a-zç]+)\s+de\s+(\d{4})\b", re.IGNORECASE)


def flatten(text: str) -> str:
    """Collapse every run of whitespace (including line breaks and NBSP) into one space.

    PDF text comes with line breaks in arbitrary places, so the parsers work on a
    single line and rely on textual markers instead of layout.
    """
    return " ".join(text.replace("\xa0", " ").split())


def clean_enunciado(text: str) -> str:
    """Strip whitespace and the quotes some courts put around the whole statement."""
    text = text.strip()
    if text[:1] in '"“':
        text = re.sub(r"^[\"“]\s*", "", text)
        text = re.sub(r"\s*[\"”]\s*([.;]?)$", r"\1", text)
    return text


def parse_date(text: str) -> str | None:
    """Return the first date found in ``text`` as ISO 8601, or ``None``.

    Accepts ``16/10/2012``, ``9.8.2022`` and ``2 de agosto de 2022``.
    """
    candidates: list[tuple[int, date]] = []

    for match in _NUMERIC_DATE.finditer(text):
        day, month, year = (int(g) for g in match.groups())
        parsed = _safe_date(year, month, day)
        if parsed:
            candidates.append((match.start(), parsed))

    for match in _WRITTEN_DATE.finditer(text):
        day, month_name, year = match.groups()
        month = MESES.get(month_name.lower())
        parsed = _safe_date(int(year), month, int(day)) if month else None
        if parsed:
            candidates.append((match.start(), parsed))

    if not candidates:
        return None
    return min(candidates)[1].isoformat()


def _safe_date(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None
