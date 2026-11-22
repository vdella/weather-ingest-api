"""Fetch -> normalize -> persist."""

from decimal import Decimal
from typing import Protocol

from app.clients.openweather import CurrentWeather
from app.core.cities import search_key
from app.core.config import Units
from app.models import WeatherReading
from app.repositories.weather_readings import NewWeatherReading


class WeatherProvider(Protocol):
    def get_current_weather(
        self, city: str, *, units: Units | None = None, lang: str | None = None
    ) -> CurrentWeather: ...


class ReadingStore(Protocol):
    def upsert(self, reading: NewWeatherReading) -> WeatherReading: ...


def _dec(value: float) -> Decimal:
    # Go through str() so 24.31 becomes Decimal("24.31"), not its binary approximation.
    return Decimal(str(value))


def to_new_reading(observation: CurrentWeather) -> NewWeatherReading:
    """Map an OpenWeather observation onto the columns of weather_readings."""
    data = observation.data
    return NewWeatherReading(
        city_id=data.id,
        city_name=data.name,
        city_search_name=search_key(data.name),
        country_code=data.sys.country,
        latitude=_dec(data.coord.lat),
        longitude=_dec(data.coord.lon),
        observed_at=data.dt,
        units=observation.units,
        lang=observation.lang,
        temperature=_dec(data.main.temp),
        feels_like=_dec(data.main.feels_like),
        temp_min=_dec(data.main.temp_min),
        temp_max=_dec(data.main.temp_max),
        humidity=data.main.humidity,
        pressure=data.main.pressure,
        wind_speed=_dec(data.wind.speed),
        wind_deg=data.wind.deg,
        cloudiness=data.clouds.all,
        weather_main=data.condition.main,
        weather_description=data.condition.description,
        raw_payload=observation.raw,
    )


class WeatherIngestionService:
    """Fetches the current weather for a city and stores it.

    Transactions are owned by the caller (one unit of work per CLI command or HTTP request).
    """

    def __init__(self, provider: WeatherProvider, store: ReadingStore) -> None:
        self._provider = provider
        self._store = store

    def ingest(
        self, city: str, *, units: Units | None = None, lang: str | None = None
    ) -> WeatherReading:
        observation = self._provider.get_current_weather(city, units=units, lang=lang)
        return self._store.upsert(to_new_reading(observation))
