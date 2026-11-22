"""HTTP client for the OpenWeather *Current Weather* API.

The client owns everything that is specific to talking to OpenWeather: building the
authenticated request, timeouts, and translating HTTP failures into domain exceptions.
Error messages never include the request URL, because the API key travels in the query string.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from types import TracebackType
from typing import Any, Self

import httpx
from pydantic import ValidationError

from app.clients.openweather_schemas import CurrentWeatherResponse
from app.core.config import Settings, Units

logger = logging.getLogger(__name__)

# httpx logs every request URL at INFO level, which would include `appid=<key>`.
logging.getLogger("httpx").setLevel(logging.WARNING)


class OpenWeatherError(Exception):
    """Base class for every failure while talking to OpenWeather."""


class CityNotFoundError(OpenWeatherError):
    """OpenWeather does not know the requested city (HTTP 404)."""


class InvalidApiKeyError(OpenWeatherError):
    """The API key is missing, wrong or not activated yet (HTTP 401)."""


class RateLimitedError(OpenWeatherError):
    """The account exceeded its request quota (HTTP 429)."""


class UpstreamUnavailableError(OpenWeatherError):
    """OpenWeather timed out, could not be reached or returned a 5xx."""


class UnexpectedResponseError(OpenWeatherError):
    """OpenWeather answered with a status or a body this client does not understand."""


@dataclass(frozen=True, slots=True)
class CurrentWeather:
    """A validated observation plus the context needed to interpret and store it."""

    data: CurrentWeatherResponse
    units: Units
    lang: str
    raw: dict[str, Any]


class OpenWeatherClient:
    CURRENT_WEATHER_PATH = "/weather"

    def __init__(
        self,
        api_key: str,
        base_url: str,
        *,
        timeout_seconds: float = 10.0,
        default_units: Units = "metric",
        default_lang: str = "en",
        http_client: httpx.Client | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("An OpenWeather API key is required")
        self._api_key = api_key
        self._default_units: Units = default_units
        self._default_lang = default_lang
        self._owns_http_client = http_client is None
        self._http = http_client or httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=timeout_seconds,
            headers={"Accept": "application/json"},
        )

    @classmethod
    def from_settings(cls, settings: Settings) -> Self:
        return cls(
            api_key=settings.openweather_api_key.get_secret_value(),
            base_url=str(settings.openweather_base_url),
            timeout_seconds=settings.openweather_timeout_seconds,
            default_units=settings.default_units,
            default_lang=settings.default_lang,
        )

    def get_current_weather(
        self, city: str, *, units: Units | None = None, lang: str | None = None
    ) -> CurrentWeather:
        """Fetch the current weather for `city`, e.g. ``"Florianopolis,BR"``."""
        city = city.strip()
        if not city:
            raise ValueError("city must not be empty")
        units = units or self._default_units
        lang = lang or self._default_lang

        params = {"q": city, "units": units, "lang": lang, "appid": self._api_key}
        logger.info("Fetching current weather", extra={"city": city, "units": units})

        try:
            response = self._http.get(self.CURRENT_WEATHER_PATH, params=params)
        except httpx.TimeoutException:
            raise UpstreamUnavailableError("OpenWeather request timed out") from None
        except httpx.TransportError as exc:
            raise UpstreamUnavailableError(
                f"Could not reach OpenWeather ({type(exc).__name__})"
            ) from None

        self._raise_for_status(response, city)

        try:
            raw = response.json()
            data = CurrentWeatherResponse.model_validate(raw)
        except (ValueError, ValidationError) as exc:
            raise UnexpectedResponseError(
                f"OpenWeather returned an invalid payload: {exc}"
            ) from None

        return CurrentWeather(data=data, units=units, lang=lang, raw=raw)

    @staticmethod
    def _raise_for_status(response: httpx.Response, city: str) -> None:
        status = response.status_code
        if response.is_success:
            return
        if status == httpx.codes.NOT_FOUND:
            raise CityNotFoundError(f"City not found on OpenWeather: {city!r}")
        if status == httpx.codes.UNAUTHORIZED:
            raise InvalidApiKeyError("OpenWeather rejected the API key")
        if status == httpx.codes.TOO_MANY_REQUESTS:
            raise RateLimitedError("OpenWeather rate limit exceeded")
        if response.is_server_error:
            raise UpstreamUnavailableError(f"OpenWeather is unavailable (HTTP {status})")
        raise UnexpectedResponseError(f"OpenWeather returned HTTP {status}")

    def close(self) -> None:
        if self._owns_http_client:
            self._http.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()
