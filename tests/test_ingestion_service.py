from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.clients.openweather import CurrentWeather
from app.clients.openweather_schemas import CurrentWeatherResponse
from app.core.config import Units
from app.models import WeatherReading
from app.repositories.weather_readings import NewWeatherReading, WeatherReadingRepository
from app.services.ingestion import WeatherIngestionService, to_new_reading


def make_observation(payload: dict[str, Any], units: Units = "metric") -> CurrentWeather:
    return CurrentWeather(
        data=CurrentWeatherResponse.model_validate(payload), units=units, lang="pt_br", raw=payload
    )


def test_maps_observation_to_table_columns(openweather_payload: dict[str, Any]) -> None:
    reading = to_new_reading(make_observation(openweather_payload))

    assert reading.city_id == 3463237
    assert reading.city_name == "Florianópolis"
    assert reading.city_search_name == "florianopolis"
    assert reading.country_code == "BR"
    assert reading.latitude == Decimal("-27.5967")
    assert reading.observed_at == datetime(2026, 11, 22, 12, 0, tzinfo=UTC)
    assert reading.units == "metric"
    assert reading.lang == "pt_br"
    assert reading.temperature == Decimal("24.31")
    assert reading.humidity == 74
    assert reading.pressure == 1014
    assert reading.wind_speed == Decimal("4.63")
    assert reading.wind_deg == 70
    assert reading.cloudiness == 75
    assert reading.weather_main == "Clouds"
    assert reading.weather_description == "nublado"
    assert reading.raw_payload is openweather_payload


class FakeProvider:
    def __init__(self, observation: CurrentWeather) -> None:
        self.observation = observation
        self.calls: list[tuple[str, Units | None, str | None]] = []

    def get_current_weather(
        self, city: str, *, units: Units | None = None, lang: str | None = None
    ) -> CurrentWeather:
        self.calls.append((city, units, lang))
        return self.observation


class FakeStore:
    def __init__(self) -> None:
        self.saved: list[NewWeatherReading] = []

    def upsert(self, reading: NewWeatherReading) -> WeatherReading:
        self.saved.append(reading)
        return WeatherReading(id=1, city_name=reading.city_name)


def test_ingest_fetches_and_stores(openweather_payload: dict[str, Any]) -> None:
    provider = FakeProvider(make_observation(openweather_payload, units="imperial"))
    store = FakeStore()

    result = WeatherIngestionService(provider, store).ingest(
        "Florianopolis,BR", units="imperial", lang="en"
    )

    assert provider.calls == [("Florianopolis,BR", "imperial", "en")]
    assert len(store.saved) == 1
    assert store.saved[0].units == "imperial"
    assert result.id == 1


def test_ingest_persists_a_real_payload(
    db_session: Session, openweather_payload: dict[str, Any]
) -> None:
    provider = FakeProvider(make_observation(openweather_payload))
    service = WeatherIngestionService(provider, WeatherReadingRepository(db_session))

    first = service.ingest("Florianopolis")
    again = service.ingest("Florianopolis")

    assert again.id == first.id
    assert first.raw_payload["name"] == "Florianópolis"
    assert first.temperature == Decimal("24.31")
