"""Typed application settings, loaded from environment variables (and `.env`)."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

Units = Literal["standard", "metric", "imperial"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openweather_api_key: SecretStr
    openweather_base_url: HttpUrl = HttpUrl("https://api.openweathermap.org/data/2.5")
    openweather_timeout_seconds: float = Field(default=10.0, gt=0)

    default_units: Units = "metric"
    default_lang: str = "pt_br"


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings (cached, so `.env` is read once)."""
    return Settings()
