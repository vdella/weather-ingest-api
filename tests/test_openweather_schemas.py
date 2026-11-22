from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import ValidationError

from app.clients.openweather_schemas import CurrentWeatherResponse


def test_parses_a_real_payload(openweather_payload: dict[str, Any]) -> None:
    parsed = CurrentWeatherResponse.model_validate(openweather_payload)

    assert parsed.id == 3463237
    assert parsed.name == "Florianópolis"
    assert parsed.sys.country == "BR"
    assert parsed.main.temp == pytest.approx(24.31)
    assert parsed.condition.main == "Clouds"
    assert parsed.dt == datetime(2026, 11, 22, 12, 0, tzinfo=UTC)


def test_optional_fields_may_be_missing(openweather_payload: dict[str, Any]) -> None:
    del openweather_payload["wind"]["deg"]
    del openweather_payload["sys"]["country"]

    parsed = CurrentWeatherResponse.model_validate(openweather_payload)

    assert parsed.wind.deg is None
    assert parsed.sys.country is None


def test_requires_at_least_one_weather_condition(openweather_payload: dict[str, Any]) -> None:
    openweather_payload["weather"] = []

    with pytest.raises(ValidationError):
        CurrentWeatherResponse.model_validate(openweather_payload)
