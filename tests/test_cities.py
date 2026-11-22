import pytest

from app.core.cities import CityQuery, search_key


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Florianópolis", "florianopolis"),
        ("  SÃO   Paulo ", "sao paulo"),
        ("München", "munchen"),
        ("new york", "new york"),
    ],
)
def test_search_key_ignores_case_accents_and_spacing(raw: str, expected: str) -> None:
    assert search_key(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Florianopolis", CityQuery("florianopolis", None)),
        ("Florianópolis,br", CityQuery("florianopolis", "BR")),
        ("Springfield, IL, US", CityQuery("springfield", "US")),
        ("Springfield,Illinois", CityQuery("springfield", None)),
    ],
)
def test_city_query_parses_openweather_format(raw: str, expected: CityQuery) -> None:
    assert CityQuery.parse(raw) == expected


def test_city_query_rejects_blank_input() -> None:
    with pytest.raises(ValueError):
        CityQuery.parse(" , ")
