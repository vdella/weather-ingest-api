"""FastAPI application entry point: ``uvicorn app.main:app``."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.api.errors import register_error_handlers
from app.api.routes import weather
from app.clients.openweather import OpenWeatherClient
from app.core.config import get_settings

API_PREFIX = "/api/v1"

DESCRIPTION = """
Pulls the **current weather** for a city from [OpenWeather](https://openweathermap.org/current),
stores it in PostgreSQL and lets you query the stored readings.

1. `POST /api/v1/weather/fetch?city=Florianopolis,BR` to collect an observation.
2. `GET /api/v1/weather` to list, filter and paginate what was stored.
"""


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logging.basicConfig(level=logging.INFO)
    # One pooled HTTP client for the app's lifetime; fails fast if the API key is missing.
    with OpenWeatherClient.from_settings(get_settings()) as client:
        app.state.openweather_client = client
        yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Weather Ingest API",
        version=__version__,
        description=DESCRIPTION,
        lifespan=lifespan,
    )
    register_error_handlers(app)
    app.include_router(weather.router, prefix=API_PREFIX)
    return app


app = create_app()
