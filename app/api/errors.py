"""Translate domain exceptions into HTTP responses."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.clients.openweather import (
    CityNotFoundError,
    InvalidApiKeyError,
    OpenWeatherError,
    RateLimitedError,
    UnexpectedResponseError,
    UpstreamUnavailableError,
)

STATUS_BY_ERROR: dict[type[OpenWeatherError], int] = {
    CityNotFoundError: status.HTTP_404_NOT_FOUND,
    InvalidApiKeyError: status.HTTP_502_BAD_GATEWAY,
    UnexpectedResponseError: status.HTTP_502_BAD_GATEWAY,
    RateLimitedError: status.HTTP_503_SERVICE_UNAVAILABLE,
    UpstreamUnavailableError: status.HTTP_503_SERVICE_UNAVAILABLE,
}


async def openweather_error_handler(request: Request, exc: Exception) -> JSONResponse:
    status_code = next(
        (code for kind, code in STATUS_BY_ERROR.items() if isinstance(exc, kind)),
        status.HTTP_502_BAD_GATEWAY,
    )
    return JSONResponse(status_code=status_code, content={"detail": str(exc)})


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(OpenWeatherError, openweather_error_handler)
