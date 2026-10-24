"""Tribunal de Justiça do Pará: one PDF per súmula, listed in four pages."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from sumulas.models import DocumentLink, Sumula
from sumulas.text import clean_enunciado, flatten, parse_date
from sumulas.tribunais.base import Tribunal, absolute_url, section, split_referencias

_BASE = "https://www.tjpa.jus.br/PortalExterno/institucional/Acordaos-e-Jurisprudencia/"

_HEADER = re.compile(
    r"Súmula\s+n\.?\s*[°º]?\s*(?P<numero>\d+)(?:\s*\((?P<parenteses>[^)]*)\))?",
    re.IGNORECASE,
)
_RESOLUCAO = re.compile(r"Res\.?\s*(\d+/\d{4})", re.IGNORECASE)
_DIARIO = re.compile(r"Diário da Justiça.*?\d{2}/\d{2}/\d{4}(?:\s*-\s*p\.\s*\d+)?", re.IGNORECASE)

_STOPS = (
    r"A relação originária",
    r"Data de Aprovação",
    r"Referência Legislativa",
    r"Diário da Justiça",
)


class TJPA(Tribunal):
    slug = "tjpa"
    nome = "Tribunal de Justiça do Estado do Pará"
    listing_urls = (
        _BASE + "166246-Sumulas-n.-01-a-10.xhtml",
        _BASE + "166247-Sumulas-n.-11-a-23.xhtml",
        _BASE + "242244-Sumulas-de-n.-21-em-diante.xhtml",
        _BASE + "339250-Sumulas-n.-31-a-40.xhtml",
    )

    def find_links(self, html: str, page_url: str) -> list[DocumentLink]:
        soup = BeautifulSoup(html, "html.parser")
        return [
            DocumentLink(url=absolute_url(a["href"], page_url), label=flatten(a.get_text()))
            for a in soup.select("li.tj-icon-pdf a[href]")
        ]

    def parse(self, text: str, link: DocumentLink) -> Sumula | None:
        text = flatten(text)
        header = _HEADER.search(text)
        if not header:
            return None

        body = text[header.end() :]
        enunciado = section(body, r"^", _STOPS)
        if not enunciado:
            return None

        resolucao = publicacao = None
        parenteses = header.group("parenteses")
        if parenteses:
            if res := _RESOLUCAO.search(parenteses):
                resolucao = f"Res. {res.group(1)}"
            publicacao = parenteses.split(" - ", 1)[1].strip() if " - " in parenteses else None
        if publicacao is None and (diario := _DIARIO.search(body)):
            publicacao = diario.group(0)

        aprovacao = section(body, r"Data de Aprovação[^0-9]*", (r"Referência Legislativa",))

        return Sumula(
            tribunal=self.slug,
            numero=int(header.group("numero")),
            enunciado=clean_enunciado(enunciado),
            url_fonte=link.url,
            resolucao=resolucao,
            publicacao=publicacao,
            data_publicacao=parse_date(publicacao) if publicacao else None,
            data_aprovacao=parse_date(aprovacao) if aprovacao else None,
            referencias=split_referencias(section(body, r"Referência Legislativa")),
        )
