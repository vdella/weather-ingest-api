from collections.abc import Iterator
from typing import Any

import httpx
import pytest
import respx

from app.clients.openweather import (
    CityNotFoundError,
    InvalidApiKeyError,
    OpenWeatherClient,
    OpenWeatherError,
    RateLimitedError,
    UnexpectedResponseError,
    UpstreamUnavailableError,
)
from app.core.config import get_settings

BASE_URL = "https://api.openweathermap.org/data/2.5"
API_KEY = "super-secret-key"


@pytest.fixture
def client() -> Iterator[OpenWeatherClient]:
    with OpenWeatherClient(
        api_key=API_KEY, base_url=BASE_URL, default_units="metric", default_lang="pt_br"
    ) as c:
        yield c


@pytest.fixture
def mock_api() -> Iterator[respx.MockRouter]:
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as router:
        yield router


def test_sends_authenticated_request_with_dynamic_params(
    client: OpenWeatherClient, mock_api: respx.MockRouter, openweather_payload: dict[str, Any]
) -> None:
    route = mock_api.get("/weather").respond(200, json=openweather_payload)

    result = client.get_current_weather("Florianopolis,BR", units="imperial", lang="en")

    request = route.calls.last.request
    assert request.url.params["q"] == "Florianopolis,BR"
    assert request.url.params["units"] == "imperial"
    assert request.url.params["lang"] == "en"
    assert request.url.params["appid"] == API_KEY
    assert result.data.name == "Florianópolis"
    assert result.units == "imperial"
    assert result.lang == "en"
    assert result.raw == openweather_payload


def test_falls_back_to_default_units_and_lang(
    client: OpenWeatherClient, mock_api: respx.MockRouter, openweather_payload: dict[str, Any]
) -> None:
    route = mock_api.get("/weather").respond(200, json=openweather_payload)

    result = client.get_current_weather("  Florianopolis  ")

    params = route.calls.last.request.url.params
    assert params["q"] == "Florianopolis"
    assert params["units"] == "metric"
    assert params["lang"] == "pt_br"
    assert result.units == "metric"


def test_rejects_blank_city(client: OpenWeatherClient) -> None:
    with pytest.raises(ValueError, match="city"):
        client.get_current_weather("   ")


def test_requires_api_key() -> None:
    with pytest.raises(ValueError, match="API key"):
        OpenWeatherClient(api_key="", base_url=BASE_URL)


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (404, CityNotFoundError),
        (401, InvalidApiKeyError),
        (429, RateLimitedError),
        (500, UpstreamUnavailableError),
        (503, UpstreamUnavailableError),
        (400, UnexpectedResponseError),
    ],
)
def test_maps_http_errors_to_domain_errors(
    client: OpenWeatherClient,
    mock_api: respx.MockRouter,
    status: int,
    expected: type[OpenWeatherError],
) -> None:
    mock_api.get("/weather").respond(status, json={"cod": status, "message": "error"})

    with pytest.raises(expected) as exc_info:
        client.get_current_weather("Florianopolis")

    assert API_KEY not in str(exc_info.value)
    assert exc_info.value.__cause__ is None


def test_maps_timeout_to_unavailable(client: OpenWeatherClient, mock_api: respx.MockRouter) -> None:
    mock_api.get("/weather").mock(side_effect=httpx.ReadTimeout("timed out"))

    with pytest.raises(UpstreamUnavailableError, match="timed out"):
        client.get_current_weather("Florianopolis")


def test_maps_connection_error_without_leaking_the_key(
    client: OpenWeatherClient, mock_api: respx.MockRouter
) -> None:
    mock_api.get("/weather").mock(side_effect=httpx.ConnectError(f"failed for appid={API_KEY}"))

    with pytest.raises(UpstreamUnavailableError) as exc_info:
        client.get_current_weather("Florianopolis")

    assert API_KEY not in str(exc_info.value)
    assert exc_info.value.__cause__ is None
    assert exc_info.value.__suppress_context__ is True


def test_rejects_non_json_body(client: OpenWeatherClient, mock_api: respx.MockRouter) -> None:
    mock_api.get("/weather").respond(200, text="<html>oops</html>")

    with pytest.raises(UnexpectedResponseError):
        client.get_current_weather("Florianopolis")


def test_rejects_payload_missing_fields(
    client: OpenWeatherClient, mock_api: respx.MockRouter, openweather_payload: dict[str, Any]
) -> None:
    del openweather_payload["main"]
    mock_api.get("/weather").respond(200, json=openweather_payload)

    with pytest.raises(UnexpectedResponseError, match="main"):
        client.get_current_weather("Florianopolis")


def test_builds_from_settings(
    mock_api: respx.MockRouter, openweather_payload: dict[str, Any]
) -> None:
    route = mock_api.get("/weather").respond(200, json=openweather_payload)

    with OpenWeatherClient.from_settings(get_settings()) as client:
        client.get_current_weather("Florianopolis")

    params = route.calls.last.request.url.params
    assert params["appid"] == "test-api-key"
    assert params["units"] == "metric"
    assert params["lang"] == "pt_br"
