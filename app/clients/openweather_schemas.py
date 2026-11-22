"""Pydantic models for the OpenWeather *Current Weather* response (`/data/2.5/weather`).

Only the fields this service uses are declared; anything else is ignored here and kept in
the raw payload instead. See https://openweathermap.org/current#fields_json
"""

from pydantic import AwareDatetime, BaseModel, Field


class Coordinates(BaseModel):
    lat: float
    lon: float


class WeatherCondition(BaseModel):
    id: int
    main: str
    description: str


class MainMetrics(BaseModel):
    temp: float
    feels_like: float
    temp_min: float
    temp_max: float
    pressure: int
    humidity: int


class Wind(BaseModel):
    speed: float
    deg: int | None = None


class Clouds(BaseModel):
    all: int


class SystemInfo(BaseModel):
    country: str | None = None


class CurrentWeatherResponse(BaseModel):
    id: int = Field(description="OpenWeather city id")
    name: str = Field(description="City name")
    coord: Coordinates
    weather: list[WeatherCondition] = Field(min_length=1)
    main: MainMetrics
    wind: Wind
    clouds: Clouds
    sys: SystemInfo
    dt: AwareDatetime = Field(description="Time of the observation (UTC)")

    @property
    def condition(self) -> WeatherCondition:
        """The primary weather condition (OpenWeather lists the most relevant first)."""
        return self.weather[0]
