import pytest

from sumulas.text import flatten, parse_date


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("DJ. N° 5131/2012, 16/10/2012", "2012-10-16"),
        ("DJe de 9.8.2022", "2022-08-09"),
        ("Belém, 2 de agosto de 2022.", "2022-08-02"),
        ("realizada em 27/7/2016", "2016-07-27"),
        ("em 1º de março de 2020", None),  # ordinal day is not supported on purpose
        ("31/02/2020", None),
        ("sem data", None),
    ],
)
def test_parse_date(text, expected):
    assert parse_date(text) == expected


def test_parse_date_returns_first_date():
    assert parse_date("de 9.8.2022, republicada em 1 de setembro de 2022") == "2022-08-09"


def test_flatten_collapses_line_breaks_and_nbsp():
    assert flatten("Publicada no\nDJe\xa0\n de 9.8.2022.") == "Publicada no DJe de 9.8.2022."
