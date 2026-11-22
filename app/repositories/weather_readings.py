"""All SQL for the weather_readings table lives here."""

from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.cities import CityQuery
from app.models import WeatherReading


@dataclass(frozen=True, slots=True)
class NewWeatherReading:
    """Values for one observation, before it gets an id."""

    city_id: int
    city_name: str
    city_search_name: str
    country_code: str | None
    latitude: Decimal
    longitude: Decimal
    observed_at: datetime
    units: str
    lang: str
    temperature: Decimal
    feels_like: Decimal
    temp_min: Decimal
    temp_max: Decimal
    humidity: int
    pressure: int
    wind_speed: Decimal
    wind_deg: int | None
    cloudiness: int
    weather_main: str
    weather_description: str
    raw_payload: dict[str, Any]


# Columns that identify an observation; everything else is refreshed on conflict.
_NATURAL_KEY = ("city_id", "observed_at", "units")


class WeatherReadingRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert(self, reading: NewWeatherReading) -> WeatherReading:
        """Insert the observation, or refresh it if it was already stored (idempotent)."""
        values = asdict(reading)
        insert_stmt = insert(WeatherReading).values(**values)
        updates = {k: insert_stmt.excluded[k] for k in values if k not in _NATURAL_KEY}
        upsert_stmt = insert_stmt.on_conflict_do_update(
            index_elements=list(_NATURAL_KEY),
            set_={**updates, "fetched_at": func.now()},
        ).returning(WeatherReading)
        return self._session.scalars(
            upsert_stmt, execution_options={"populate_existing": True}
        ).one()

    def get(self, reading_id: int) -> WeatherReading | None:
        return self._session.get(WeatherReading, reading_id)

    def list(
        self,
        *,
        city: CityQuery | None = None,
        observed_from: datetime | None = None,
        observed_to: datetime | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[WeatherReading], int]:
        """Readings matching the filters, newest first, plus the total count for pagination."""
        query = self._filtered(select(WeatherReading), city, observed_from, observed_to)
        total = self._session.scalar(
            self._filtered(
                select(func.count()).select_from(WeatherReading), city, observed_from, observed_to
            )
        )
        items = self._session.scalars(
            query.order_by(WeatherReading.observed_at.desc(), WeatherReading.id.desc())
            .limit(limit)
            .offset(offset)
        ).all()
        return list(items), total or 0

    def latest(self, city: CityQuery) -> WeatherReading | None:
        items, _ = self.list(city=city, limit=1)
        return items[0] if items else None

    @staticmethod
    def _filtered[T: Select[Any]](
        stmt: T,
        city: CityQuery | None,
        observed_from: datetime | None,
        observed_to: datetime | None,
    ) -> T:
        if city is not None:
            stmt = stmt.where(WeatherReading.city_search_name == city.name)
            if city.country_code:
                stmt = stmt.where(WeatherReading.country_code == city.country_code)
        if observed_from is not None:
            stmt = stmt.where(WeatherReading.observed_at >= observed_from)
        if observed_to is not None:
            stmt = stmt.where(WeatherReading.observed_at < observed_to)
        return stmt
