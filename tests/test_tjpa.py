import pytest

from sumulas.models import DocumentLink
from sumulas.tribunais.tjpa import TJPA

tjpa = TJPA()
LINK = DocumentLink(url="https://www.tjpa.jus.br/CMSPortal/VisualizarArquivo?idArquivo=1", label="")


def parse(fixture_text, name):
    return tjpa.parse(fixture_text("tjpa", f"{name}.txt"), LINK)


@pytest.mark.parametrize("numero", range(1, 11))
def test_every_sample_has_number_and_statement(fixture_text, numero):
    sumula = parse(fixture_text, f"sumula{numero:02d}")

    assert sumula is not None
    assert sumula.numero == numero
    assert len(sumula.enunciado) > 40
    assert not sumula.enunciado.startswith(("Súmula", "("))


def test_header_with_resolution_and_publication(fixture_text):
    sumula = parse(fixture_text, "sumula07")

    assert sumula.resolucao == "Res. 020/2012"
    assert sumula.publicacao == "DJ. N° 5131/2012, 16/10/2012"
    assert sumula.data_publicacao == "2012-10-16"
    assert sumula.enunciado.startswith("Não padece do vício de inconstitucionalidade")


def test_quotes_are_removed_from_statement(fixture_text):
    sumula = parse(fixture_text, "sumula09")

    assert sumula.enunciado.startswith("Concede-se Habeas Corpus")
    assert sumula.enunciado.endswith("hipossuficiência do paciente.")


def test_publication_in_footer(fixture_text):
    sumula = parse(fixture_text, "sumula05")

    assert sumula.publicacao == "Diário da Justiça n. 4204 de 09/10/2008 - p. 3"
    assert sumula.data_publicacao == "2008-10-09"
    assert "Diário da Justiça" not in sumula.enunciado
    assert "Tribunal de Justiça" not in sumula.enunciado


def test_amended_sumula_keeps_only_current_statement(fixture_text):
    sumula = parse(fixture_text, "sumula06")

    assert sumula.enunciado.startswith("A alegação de hipossuficiência econômica")
    assert sumula.enunciado.endswith("capacidade econômica do requerente.")
    assert sumula.data_aprovacao == "2016-07-27"
    assert sumula.referencias == ["Código de Processo Civil de 2015, art. 98"]


def test_text_without_sumula_is_ignored():
    assert tjpa.parse("Página em manutenção", LINK) is None


def test_find_links_resolves_and_normalizes_urls(fixture_text):
    html = fixture_text("tjpa", "listagem.html")
    links = tjpa.find_links(html, tjpa.listing_urls[0])

    assert [link.url for link in links] == [
        "https://www.tjpa.jus.br/CMSPortal/VisualizarArquivo?idArquivo=259935",
        "https://www.tjpa.jus.br/CMSPortal/VisualizarArquivo?idArquivo=259933",
        "https://www.tjpa.jus.br/CMSPortal/VisualizarArquivo?idArquivo=259931",
    ]
    assert links[0].label.startswith("Súmula nº 10")
