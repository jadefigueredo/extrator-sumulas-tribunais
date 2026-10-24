from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixture_text():
    def load(*parts: str) -> str:
        return FIXTURES.joinpath(*parts).read_text(encoding="utf-8")

    return load
