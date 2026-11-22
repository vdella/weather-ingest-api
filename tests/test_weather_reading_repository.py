from datetime import timedelta
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.cities import CityQuery
from app.models import WeatherReading
from app.repositories.weather_readings import WeatherReadingRepository
from tests.factories import OBSERVED_AT, make_new_reading


@pytest.fixture
def repo(db_session: Session) -> WeatherReadingRepository:
    return WeatherReadingRepository(db_session)


def test_upsert_inserts_a_new_reading(repo: WeatherReadingRepository) -> None:
    stored = repo.upsert(make_new_reading())

    assert stored.id is not None
    assert stored.city_name == "Florianópolis"
    assert stored.temperature == Decimal("24.31")
    assert stored.raw_payload == {"id": 3463237}
    assert stored.fetched_at is not None
    assert repo.get(stored.id) is stored


def test_upsert_is_idempotent(repo: WeatherReadingRepository, db_session: Session) -> None:
    first = repo.upsert(make_new_reading())
    second = repo.upsert(make_new_reading(temperature=Decimal("25.00"), weather_description="sol"))

    assert second.id == first.id
    assert second.temperature == Decimal("25.00")
    assert second.weather_description == "sol"
    assert db_session.scalar(select(func.count()).select_from(WeatherReading)) == 1


def test_same_observation_in_other_units_is_a_new_row(repo: WeatherReadingRepository) -> None:
    metric = repo.upsert(make_new_reading())
    imperial = repo.upsert(make_new_reading(units="imperial", temperature=Decimal("75.76")))

    assert imperial.id != metric.id


def test_check_constraints_reject_invalid_values(repo: WeatherReadingRepository) -> None:
    with pytest.raises(IntegrityError):
        repo.upsert(make_new_reading(humidity=150))


def test_list_filters_by_city_and_time_newest_first(repo: WeatherReadingRepository) -> None:
    for hours in range(3):
        repo.upsert(make_new_reading(observed_at=OBSERVED_AT + timedelta(hours=hours)))
    repo.upsert(
        make_new_reading(city_id=3448439, city_name="São Paulo", city_search_name="sao paulo")
    )

    items, total = repo.list(
        city=CityQuery.parse("florianópolis,BR"),
        observed_from=OBSERVED_AT + timedelta(hours=1),
        limit=10,
    )

    assert total == 2
    assert [r.observed_at for r in items] == [
        OBSERVED_AT + timedelta(hours=2),
        OBSERVED_AT + timedelta(hours=1),
    ]


def test_list_paginates_and_reports_the_total(repo: WeatherReadingRepository) -> None:
    for hours in range(5):
        repo.upsert(make_new_reading(observed_at=OBSERVED_AT + timedelta(hours=hours)))

    items, total = repo.list(limit=2, offset=2)

    assert total == 5
    assert [r.observed_at for r in items] == [
        OBSERVED_AT + timedelta(hours=2),
        OBSERVED_AT + timedelta(hours=1),
    ]


def test_latest_returns_the_most_recent_reading_for_a_city(
    repo: WeatherReadingRepository,
) -> None:
    repo.upsert(make_new_reading())
    newest = repo.upsert(make_new_reading(observed_at=OBSERVED_AT + timedelta(hours=1)))

    assert repo.latest(CityQuery.parse("Florianopolis")) is newest
    assert repo.latest(CityQuery.parse("Florianopolis,US")) is None
    assert repo.latest(CityQuery.parse("Atlantis")) is None
