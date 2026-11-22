"""REST API tests with the repository replaced by an in-memory fake (no database needed)."""

from collections.abc import Iterator
from datetime import datetime
from typing import Any

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.api.deps import get_repository
from app.core.cities import CityQuery
from app.main import create_app
from app.models import WeatherReading
from app.repositories.weather_readings import NewWeatherReading
from tests.factories import make_stored_reading

OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


class FakeRepository:
    def __init__(self) -> None:
        self.readings: dict[int, WeatherReading] = {}
        self.list_calls: list[dict[str, Any]] = []

    def upsert(self, reading: NewWeatherReading) -> WeatherReading:
        stored = make_stored_reading(
            reading_id=len(self.readings) + 1,
            **{k: getattr(reading, k) for k in reading.__dataclass_fields__},
        )
        self.readings[stored.id] = stored
        return stored

    def get(self, reading_id: int) -> WeatherReading | None:
        return self.readings.get(reading_id)

    def list(self, **filters: Any) -> tuple[list[WeatherReading], int]:
        self.list_calls.append(filters)
        items = list(self.readings.values())
        return items, len(items)

    def latest(self, city: CityQuery) -> WeatherReading | None:
        matches = [r for r in self.readings.values() if r.city_search_name == city.name]
        return max(matches, key=lambda r: r.observed_at, default=None)


@pytest.fixture
def repo() -> FakeRepository:
    return FakeRepository()


@pytest.fixture
def client(repo: FakeRepository) -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_repository] = lambda: repo
    with TestClient(app) as test_client:
        yield test_client


# --- POST /api/v1/weather/fetch -----------------------------------------------------------


@respx.mock
def test_fetch_stores_and_returns_the_reading(
    client: TestClient, openweather_payload: dict[str, Any]
) -> None:
    route = respx.get(OPENWEATHER_URL).respond(200, json=openweather_payload)

    response = client.post(
        "/api/v1/weather/fetch", params={"city": "Florianopolis,BR", "units": "imperial"}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["city_name"] == "Florianópolis"
    assert body["units"] == "imperial"
    assert body["temperature"] == "24.31"
    assert "raw_payload" not in body
    assert "city_search_name" not in body
    assert route.calls.last.request.url.params["q"] == "Florianopolis,BR"


@pytest.mark.parametrize(
    ("upstream", "expected_status"),
    [
        (httpx.Response(404, json={"message": "city not found"}), 404),
        (httpx.Response(401, json={"message": "Invalid API key"}), 502),
        (httpx.Response(429, json={"message": "limit"}), 503),
        (httpx.Response(500), 503),
        (httpx.ReadTimeout("timeout"), 503),
    ],
)
@respx.mock
def test_fetch_maps_openweather_failures(
    client: TestClient,
    repo: FakeRepository,
    upstream: httpx.Response | Exception,
    expected_status: int,
) -> None:
    respx.get(OPENWEATHER_URL).mock(side_effect=[upstream])

    response = client.post("/api/v1/weather/fetch", params={"city": "Atlantis"})

    assert response.status_code == expected_status
    assert "test-api-key" not in response.text
    assert response.json()["detail"]
    assert repo.readings == {}


@pytest.mark.parametrize(
    "params",
    [{}, {"city": ""}, {"city": "Florianopolis", "units": "kelvin"}],
)
def test_fetch_validates_query_parameters(client: TestClient, params: dict[str, str]) -> None:
    assert client.post("/api/v1/weather/fetch", params=params).status_code == 422


# --- GET /api/v1/weather ------------------------------------------------------------------


def test_list_returns_a_page(client: TestClient, repo: FakeRepository) -> None:
    repo.readings = {1: make_stored_reading(1), 2: make_stored_reading(2)}

    response = client.get(
        "/api/v1/weather",
        params={
            "city": "florianópolis,br",
            "from": "2026-11-22T00:00:00Z",
            "to": "2026-11-23T00:00:00Z",
            "limit": 10,
            "offset": 5,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["limit"] == 10
    assert body["offset"] == 5
    assert [item["id"] for item in body["items"]] == [1, 2]
    filters = repo.list_calls[-1]
    assert filters["city"] == CityQuery("florianopolis", "BR")
    assert filters["observed_from"] == datetime.fromisoformat("2026-11-22T00:00:00Z")
    assert filters["limit"] == 10
    assert filters["offset"] == 5


def test_list_without_filters_uses_defaults(client: TestClient, repo: FakeRepository) -> None:
    response = client.get("/api/v1/weather")

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "limit": 20, "offset": 0}
    assert repo.list_calls[-1]["city"] is None


@pytest.mark.parametrize(
    "params",
    [
        {"limit": 0},
        {"limit": 101},
        {"offset": -1},
        {"from": "not-a-date"},
        {"from": "2026-11-23T00:00:00Z", "to": "2026-11-22T00:00:00Z"},
        {"city": ","},
    ],
)
def test_list_validates_query_parameters(client: TestClient, params: dict[str, Any]) -> None:
    assert client.get("/api/v1/weather", params=params).status_code == 422


# --- GET /api/v1/weather/latest and /{id} -------------------------------------------------


def test_latest_returns_the_newest_reading(client: TestClient, repo: FakeRepository) -> None:
    repo.readings = {1: make_stored_reading(1)}

    response = client.get("/api/v1/weather/latest", params={"city": "Florianopolis"})

    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_latest_returns_404_when_nothing_is_stored(client: TestClient) -> None:
    response = client.get("/api/v1/weather/latest", params={"city": "Atlantis"})

    assert response.status_code == 404
    assert "Atlantis" in response.json()["detail"]


def test_get_by_id(client: TestClient, repo: FakeRepository) -> None:
    repo.readings = {7: make_stored_reading(7)}

    assert client.get("/api/v1/weather/7").json()["id"] == 7
    assert client.get("/api/v1/weather/8").status_code == 404
    assert client.get("/api/v1/weather/abc").status_code == 422


# --- Documentation ------------------------------------------------------------------------


def test_swagger_ui_and_openapi_are_served(client: TestClient) -> None:
    assert client.get("/docs").status_code == 200
    spec = client.get("/openapi.json").json()
    assert spec["info"]["title"] == "Weather Ingest API"
    assert "/api/v1/weather/fetch" in spec["paths"]
