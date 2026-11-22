from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import IngestionServiceDep, RepositoryDep
from app.api.schemas import ErrorResponse, WeatherReadingOut, WeatherReadingPage
from app.core.cities import CityQuery
from app.core.config import Units
from app.models import WeatherReading

router = APIRouter(prefix="/weather", tags=["weather"])

CityParam = Annotated[
    str,
    Query(
        min_length=1,
        max_length=100,
        description='City name, optionally with a country code, e.g. "Florianopolis,BR"',
        examples=["Florianopolis,BR"],
    ),
]
NOT_FOUND: dict[int | str, dict[str, Any]] = {status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}}


def _parse_city(raw: str) -> CityQuery:
    try:
        return CityQuery.parse(raw)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc


@router.post(
    "/fetch",
    status_code=status.HTTP_201_CREATED,
    response_model=WeatherReadingOut,
    summary="Fetch the current weather from OpenWeather and store it",
    description=(
        "Calls OpenWeather with the given parameters and stores the observation. "
        "Calling it again for the same observation updates the stored row instead of "
        "creating a duplicate."
    ),
    responses={
        **NOT_FOUND,
        status.HTTP_502_BAD_GATEWAY: {"model": ErrorResponse},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
    },
)
def fetch_weather(
    service: IngestionServiceDep,
    city: CityParam,
    units: Annotated[Units | None, Query(description="Defaults to DEFAULT_UNITS")] = None,
    lang: Annotated[
        str | None, Query(max_length=10, description="Defaults to DEFAULT_LANG")
    ] = None,
) -> WeatherReading:
    return service.ingest(city, units=units, lang=lang)


@router.get(
    "",
    response_model=WeatherReadingPage,
    summary="List stored readings",
    description="Newest observations first. All filters are optional and combined with AND.",
)
def list_weather(
    repository: RepositoryDep,
    city: Annotated[
        str | None,
        Query(
            max_length=100,
            description="Case- and accent-insensitive city name, optionally with ',CC'",
        ),
    ] = None,
    observed_from: Annotated[
        datetime | None,
        Query(alias="from", description="Inclusive lower bound on observed_at (ISO-8601)"),
    ] = None,
    observed_to: Annotated[
        datetime | None,
        Query(alias="to", description="Exclusive upper bound on observed_at (ISO-8601)"),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> WeatherReadingPage:
    if observed_from and observed_to and observed_from >= observed_to:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "'from' must be before 'to'")

    items, total = repository.list(
        city=_parse_city(city) if city else None,
        observed_from=observed_from,
        observed_to=observed_to,
        limit=limit,
        offset=offset,
    )
    return WeatherReadingPage(
        items=[WeatherReadingOut.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/latest",
    response_model=WeatherReadingOut,
    summary="Most recent stored reading for a city",
    responses=NOT_FOUND,
)
def latest_weather(repository: RepositoryDep, city: CityParam) -> WeatherReading:
    reading = repository.latest(_parse_city(city))
    if reading is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No stored reading for {city!r}")
    return reading


@router.get(
    "/{reading_id}",
    response_model=WeatherReadingOut,
    summary="Get one stored reading by id",
    responses=NOT_FOUND,
)
def get_weather(repository: RepositoryDep, reading_id: int) -> WeatherReading:
    reading = repository.get(reading_id)
    if reading is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Reading {reading_id} not found")
    return reading
