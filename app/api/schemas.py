"""Response models: the public contract of the REST API (decoupled from the ORM)."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class WeatherReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(examples=[1])
    city_id: int = Field(description="OpenWeather city id", examples=[3463237])
    city_name: str = Field(examples=["Florianópolis"])
    country_code: str | None = Field(examples=["BR"])
    latitude: Decimal = Field(examples=["-27.59670"])
    longitude: Decimal = Field(examples=["-48.54920"])
    observed_at: datetime = Field(description="When OpenWeather measured the data")
    fetched_at: datetime = Field(description="When this service last collected it")
    units: str = Field(examples=["metric"])
    lang: str = Field(examples=["pt_br"])
    temperature: Decimal = Field(examples=["24.31"])
    feels_like: Decimal
    temp_min: Decimal
    temp_max: Decimal
    humidity: int = Field(description="%", examples=[74])
    pressure: int = Field(description="hPa", examples=[1014])
    wind_speed: Decimal = Field(examples=["4.63"])
    wind_deg: int | None = Field(description="Degrees", examples=[70])
    cloudiness: int = Field(description="%", examples=[75])
    weather_main: str = Field(examples=["Clouds"])
    weather_description: str = Field(examples=["nublado"])


class WeatherReadingPage(BaseModel):
    items: list[WeatherReadingOut]
    total: int = Field(description="Number of readings matching the filters")
    limit: int
    offset: int


class ErrorResponse(BaseModel):
    detail: str = Field(examples=["City not found on OpenWeather: 'Atlantis'"])


class HealthResponse(BaseModel):
    status: str = Field(examples=["ok"])
    database: str = Field(examples=["ok"])
    version: str
