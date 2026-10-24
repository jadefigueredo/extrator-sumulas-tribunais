import pytest

from sumulas.models import DocumentLink
from sumulas.tribunais.trepa import TREPA

trepa = TREPA()
BASE = "https://www.tre-pa.jus.br/jurisprudencia/sumulas-tre-pa-1/arquivos/"


def parse(fixture_text, numero):
    link = DocumentLink(url=f"{BASE}sumula-no-{numero}-texto", label=f"Súmula nº {numero}")
    return trepa.parse(fixture_text("tre-pa", f"sumula{numero:02d}.txt"), link)


@pytest.mark.parametrize("numero", range(5, 11))
def test_every_sample_is_parsed(fixture_text, numero):
    sumula = parse(fixture_text, numero)

    assert sumula.numero == numero
    assert len(sumula.enunciado) > 40
    assert "resolve editar" not in sumula.enunciado
    assert "Referências" not in sumula.enunciado
    assert sumula.data_aprovacao == "2022-08-02"
    assert sumula.publicacao == "DJe de 9.8.2022"
    assert sumula.data_publicacao == "2022-08-09"
    assert sumula.referencias


def test_references_are_split(fixture_text):
    sumula = parse(fixture_text, 5)

    assert sumula.enunciado.startswith("Caso haja aplicação de multa sancionatória")
    assert sumula.referencias == [
        "Lei n° 9.504/1997, art. 37, § 1°",
        "Acórdão n° 31.914, de 21.1.2021, no Recurso Eleitoral n° 0600589-31.2020",
        "Acórdão n° 31.866, de 27.4.2021, no Recurso Eleitoral n° 0600947-93.2020",
        "Acórdão n° 31.935, de 27.5.2021, no Recurso Eleitoral n° 0600587-61.2020",
    ]


def test_number_comes_from_url_when_label_is_missing(fixture_text):
    link = DocumentLink(url=f"{BASE}sumula-no-7-nao-sao-aptos", label="")
    sumula = trepa.parse(fixture_text("tre-pa", "sumula07.txt"), link)

    assert sumula.numero == 7


def test_resolution_document_is_ignored(fixture_text):
    link = DocumentLink(
        url=f"{BASE}res-5-737-propostas-de-sumulas", label="Resolução TRE-Pa nº 5.737/2022"
    )

    assert trepa.parse(fixture_text("tre-pa", "resolucao-5737.txt"), link) is None


def test_find_links_skips_html_pages_and_other_tabs(fixture_text):
    html = fixture_text("tre-pa", "listagem.html")
    links = trepa.find_links(html, trepa.listing_urls[0])

    assert [link.label for link in links] == [
        "Resolução TRE-Pa nº 5.737/2022",
        "Súmula nº 5",
        "Súmula nº 6",
    ]
    assert links[2].url == f"{BASE}sumula-no-6-para-fins-de-comprovacao-da-filiacao-partidaria"
