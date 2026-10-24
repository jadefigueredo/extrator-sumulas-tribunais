from sumulas.http import FetchError
from sumulas.pipeline import collect
from sumulas.tribunais.trepa import TREPA

BASE = "https://www.tre-pa.jus.br/jurisprudencia/sumulas-tre-pa-1/arquivos/"


class FakeFetcher:
    def __init__(self, pages: dict[str, str], files: dict[str, bytes]):
        self.pages = pages
        self.files = files

    async def get_text(self, url: str) -> str:
        return self.pages[url]

    async def get_bytes(self, url: str) -> bytes:
        if url not in self.files:
            raise FetchError(f"{url}: HTTP 404")
        return self.files[url]


async def test_collect_parses_ignores_and_reports_failures(fixture_text):
    trepa = TREPA()
    fetcher = FakeFetcher(
        pages={trepa.listing_urls[0]: fixture_text("tre-pa", "listagem.html")},
        files={
            BASE + "res-5-737-propostas-de-sumulas": b"resolucao-5737.txt",
            BASE + "sumula-no-5-caso-haja-aplicacao-de-multa-sancionatoria": b"sumula05.txt",
            # súmula 6 is missing on purpose: the fetch fails
        },
    )

    # the fake "PDF" is the fixture name, so the extractor just reads the fixture
    result = await collect(trepa, fetcher, lambda data: fixture_text("tre-pa", data.decode()))

    assert [s.numero for s in result.sumulas] == [5]
    assert result.ignorados == [BASE + "res-5-737-propostas-de-sumulas"]
    assert len(result.falhas) == 1 and "sumula-no-6" in result.falhas[0]


async def test_listing_failure_is_reported():
    trepa = TREPA()

    class Down(FakeFetcher):
        async def get_text(self, url: str) -> str:
            raise FetchError(f"{url}: HTTP 503")

    result = await collect(trepa, Down({}, {}), lambda data: "")

    assert result.sumulas == []
    assert result.falhas == [f"{trepa.listing_urls[0]}: HTTP 503"]
