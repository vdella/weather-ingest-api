"""Builders for test data."""

from dataclasses import asdict, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from app.models import WeatherReading
from app.repositories.weather_readings import NewWeatherReading

OBSERVED_AT = datetime(2026, 11, 22, 12, 0, tzinfo=UTC)


def make_new_reading(**overrides: Any) -> NewWeatherReading:
    reading = NewWeatherReading(
        city_id=3463237,
        city_name="Florianópolis",
        city_search_name="florianopolis",
        country_code="BR",
        latitude=Decimal("-27.5967"),
        longitude=Decimal("-48.5492"),
        observed_at=OBSERVED_AT,
        units="metric",
        lang="pt_br",
        temperature=Decimal("24.31"),
        feels_like=Decimal("24.72"),
        temp_min=Decimal("23.92"),
        temp_max=Decimal("25.01"),
        humidity=74,
        pressure=1014,
        wind_speed=Decimal("4.63"),
        wind_deg=70,
        cloudiness=75,
        weather_main="Clouds",
        weather_description="nublado",
        raw_payload={"id": 3463237},
    )
    return replace(reading, **overrides)


def make_stored_reading(reading_id: int = 1, **overrides: Any) -> WeatherReading:
    """An in-memory WeatherReading as if it had been loaded from the database."""
    return WeatherReading(
        id=reading_id,
        fetched_at=datetime(2026, 11, 22, 12, 5, tzinfo=UTC),
        **asdict(make_new_reading(**overrides)),
    )
