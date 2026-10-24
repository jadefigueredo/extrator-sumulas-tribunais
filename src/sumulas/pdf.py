"""PDF to text conversion."""

from __future__ import annotations

import io
from collections.abc import Callable

import pdfplumber

TextExtractor = Callable[[bytes], str]
"""Anything that turns PDF bytes into plain text. The pipeline receives one, so
tests (or a different converter) can replace pdfplumber without touching the parsers."""


def pdf_to_text(data: bytes) -> str:
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    return "\n".join(pages)
