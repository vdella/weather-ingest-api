from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Identity,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import DateTime

from app.models.base import Base

Temperature = Numeric(6, 2)
Coordinate = Numeric(8, 5)


class WeatherReading(Base):
    """One observation of the current weather in a city, as reported by OpenWeather."""

    __tablename__ = "weather_readings"
    __table_args__ = (
        # Idempotency key: the same observation fetched twice (in the same units) is one row.
        UniqueConstraint("city_id", "observed_at", "units"),
        Index("ix_weather_readings_city_search_observed_at", "city_search_name", "observed_at"),
        Index("ix_weather_readings_observed_at", "observed_at"),
        CheckConstraint("units IN ('standard', 'metric', 'imperial')", name="units_valid"),
        CheckConstraint("humidity BETWEEN 0 AND 100", name="humidity_percent"),
        CheckConstraint("cloudiness BETWEEN 0 AND 100", name="cloudiness_percent"),
        CheckConstraint("wind_deg BETWEEN 0 AND 360", name="wind_deg_range"),
        CheckConstraint("latitude BETWEEN -90 AND 90", name="latitude_range"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="longitude_range"),
        {"comment": "Current weather observations collected from OpenWeather"},
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)

    # Location
    city_id: Mapped[int] = mapped_column(Integer, comment="OpenWeather city id")
    city_name: Mapped[str] = mapped_column(Text, comment="City name as returned by OpenWeather")
    city_search_name: Mapped[str] = mapped_column(
        Text, comment="Lower-cased, accent-free city name used for lookups"
    )
    country_code: Mapped[str | None] = mapped_column(String(2), comment="ISO 3166-1 alpha-2")
    latitude: Mapped[Decimal] = mapped_column(Coordinate)
    longitude: Mapped[Decimal] = mapped_column(Coordinate)

    # Time
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), comment="When OpenWeather measured the data (dt)"
    )
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="When this service last collected the observation",
    )

    # Request context
    units: Mapped[str] = mapped_column(Text, comment="Unit system of the measurements")
    lang: Mapped[str] = mapped_column(Text, comment="Language of weather_description")

    # Measurements
    temperature: Mapped[Decimal] = mapped_column(Temperature)
    feels_like: Mapped[Decimal] = mapped_column(Temperature)
    temp_min: Mapped[Decimal] = mapped_column(Temperature)
    temp_max: Mapped[Decimal] = mapped_column(Temperature)
    humidity: Mapped[int] = mapped_column(SmallInteger, comment="%")
    pressure: Mapped[int] = mapped_column(SmallInteger, comment="hPa")
    wind_speed: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    wind_deg: Mapped[int | None] = mapped_column(SmallInteger, comment="Degrees")
    cloudiness: Mapped[int] = mapped_column(SmallInteger, comment="%")
    weather_main: Mapped[str] = mapped_column(Text, comment="e.g. Clouds")
    weather_description: Mapped[str] = mapped_column(Text, comment="e.g. nublado")

    raw_payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB, comment="Original OpenWeather response, for auditing and reprocessing"
    )

    def __repr__(self) -> str:
        return (
            f"WeatherReading(id={self.id!r}, city={self.city_name!r}, "
            f"observed_at={self.observed_at!r}, units={self.units!r})"
        )
