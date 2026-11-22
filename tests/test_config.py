import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings


def test_defaults_are_applied() -> None:
    settings = get_settings()

    assert settings.openweather_api_key.get_secret_value() == "test-api-key"
    assert str(settings.openweather_base_url) == "https://api.openweathermap.org/data/2.5"
    assert settings.default_units == "metric"
    assert settings.default_lang == "pt_br"


def test_api_key_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENWEATHER_API_KEY")

    with pytest.raises(ValidationError, match="openweather_api_key"):
        Settings()


def test_api_key_is_not_leaked_by_repr() -> None:
    assert "test-api-key" not in repr(get_settings())


def test_rejects_unknown_units(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEFAULT_UNITS", "kelvin")

    with pytest.raises(ValidationError):
        Settings()


def test_database_url_can_be_overridden(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@db:5432/x")

    assert Settings().database_url == "postgresql+psycopg://u:p@db:5432/x"
