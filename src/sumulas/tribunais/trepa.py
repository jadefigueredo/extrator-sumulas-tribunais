"""Tribunal Regional Eleitoral do Pará: one PDF per súmula on a single page.

Súmulas 1 to 4 are published as HTML pages instead of PDFs and are not covered yet.
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from sumulas.models import DocumentLink, Sumula
from sumulas.text import clean_enunciado, flatten, parse_date
from sumulas.tribunais.base import Tribunal, absolute_url, section, split_referencias

_NUMERO = re.compile(r"Súmula\s+n\.?\s*[°º]?\s*(\d+)|sumula-(?:tre-pa-)?no-(\d+)", re.IGNORECASE)


class TREPA(Tribunal):
    slug = "tre-pa"
    nome = "Tribunal Regional Eleitoral do Pará"
    listing_urls = ("https://www.tre-pa.jus.br/jurisprudencia/sumulas-tre-pa-1/sumulas-tre-pa",)

    def find_links(self, html: str, page_url: str) -> list[DocumentLink]:
        soup = BeautifulSoup(html, "html.parser")
        return [
            DocumentLink(url=absolute_url(a["href"], page_url), label=flatten(a.get_text()))
            for a in soup.select("#ancora-1 > p a[href]:not(.internal-link)")
        ]

    def parse(self, text: str, link: DocumentLink) -> Sumula | None:
        numero = _numero(link)
        if numero is None:
            return None  # e.g. the resolution that approved the súmulas

        text = flatten(text)
        enunciado = section(text, r"resolve editar a seguinte súmula:", (r"Referências:",))
        if not enunciado:
            return None

        aprovacao = re.search(r"Belém,\s*(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})", text)
        publicacao_match = re.search(r"Publicada no\s+(.*?\d{4})", text, re.IGNORECASE)
        publicacao = publicacao_match.group(1) if publicacao_match else None

        return Sumula(
            tribunal=self.slug,
            numero=numero,
            enunciado=clean_enunciado(enunciado),
            url_fonte=link.url,
            publicacao=publicacao,
            data_publicacao=parse_date(publicacao) if publicacao else None,
            data_aprovacao=parse_date(aprovacao.group(1)) if aprovacao else None,
            referencias=split_referencias(section(text, r"Referências:", (r"Belém,",))),
        )


def _numero(link: DocumentLink) -> int | None:
    for candidate in (link.label, link.url):
        if match := _NUMERO.search(candidate):
            return int(match.group(1) or match.group(2))
    return None
