"""FastAPI dependencies: one DB session per request, shared OpenWeather client."""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.clients.openweather import OpenWeatherClient
from app.core.db import get_session_factory
from app.repositories.weather_readings import WeatherReadingRepository
from app.services.ingestion import WeatherIngestionService


def get_session() -> Iterator[Session]:
    """Unit of work per request: commit if the handler succeeds, roll back otherwise."""
    with get_session_factory().begin() as session:
        yield session


def get_openweather_client(request: Request) -> OpenWeatherClient:
    client: OpenWeatherClient = request.app.state.openweather_client
    return client


SessionDep = Annotated[Session, Depends(get_session)]


def get_repository(session: SessionDep) -> WeatherReadingRepository:
    return WeatherReadingRepository(session)


RepositoryDep = Annotated[WeatherReadingRepository, Depends(get_repository)]


def get_ingestion_service(
    repository: RepositoryDep,
    client: Annotated[OpenWeatherClient, Depends(get_openweather_client)],
) -> WeatherIngestionService:
    return WeatherIngestionService(client, repository)


IngestionServiceDep = Annotated[WeatherIngestionService, Depends(get_ingestion_service)]
