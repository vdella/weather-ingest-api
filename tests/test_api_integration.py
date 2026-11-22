"""End-to-end: HTTP -> service -> PostgreSQL, with only OpenWeather mocked."""

from collections.abc import Iterator
from typing import Any

import pytest
import respx
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_session
from app.main import create_app

OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client


@respx.mock
def test_fetch_then_query(client: TestClient, openweather_payload: dict[str, Any]) -> None:
    respx.get(OPENWEATHER_URL).respond(200, json=openweather_payload)

    created = client.post("/api/v1/weather/fetch", params={"city": "Florianopolis,BR"})
    again = client.post("/api/v1/weather/fetch", params={"city": "Florianopolis,BR"})

    assert created.status_code == 201
    assert again.json()["id"] == created.json()["id"]

    page = client.get("/api/v1/weather", params={"city": "florianópolis"}).json()
    assert page["total"] == 1
    assert page["items"][0]["temperature"] == "24.31"

    latest = client.get("/api/v1/weather/latest", params={"city": "Florianopolis,BR"})
    assert latest.json()["id"] == created.json()["id"]

    by_id = client.get(f"/api/v1/weather/{created.json()['id']}")
    assert by_id.json()["city_name"] == "Florianópolis"

    assert client.get("/health").json()["database"] == "ok"
