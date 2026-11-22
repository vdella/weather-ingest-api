# ADR-0004: OpenWeather Current Weather API through a dedicated httpx client

- **Status:** Accepted
- **Date:** 2026-11-22

## Context

The assessment asks for a `GET` request to a public API, with dynamic URL parameters and API-key authentication. OpenWeather is the suggested provider.
The extracted data will be stored (feature 2) and served (feature 3), so the extraction code must be easy to reuse and to test without network access or a real key.

## Decision

- **Provider and endpoint:** OpenWeather *Current Weather Data*, `GET /data/2.5/weather`. It is on the free tier, needs only an API key, and returns one self-contained observation per call, which maps naturally to one database row.
- **Dynamic parameters:** `q` (city, optionally `City,CC`), `units` (`standard` / `metric` / `imperial`) and `lang`. `units` and `lang` default to `DEFAULT_UNITS` / `DEFAULT_LANG` and can be overridden per call.
- **Authentication:** the key is sent as the `appid` query parameter, which is the only scheme OpenWeather supports. It is read from `OPENWEATHER_API_KEY` into a `SecretStr`.
- **HTTP library:** `httpx` (sync client), with an explicit timeout and an injectable `httpx.Client` for tests.
- **Validation:** the response is parsed into Pydantic models declaring only the fields we use. The full JSON is kept alongside (`CurrentWeather.raw`) so nothing is lost for storage.
- **Error mapping:** the client converts HTTP and transport failures into domain exceptions:

  | Upstream condition | Exception |
  |---|---|
  | 404 | `CityNotFoundError` |
  | 401 | `InvalidApiKeyError` |
  | 429 | `RateLimitedError` |
  | timeout, connection error, 5xx | `UpstreamUnavailableError` |
  | other status, invalid JSON or schema | `UnexpectedResponseError` |

  The REST layer maps these to HTTP status codes later, without knowing about httpx.
- **Key hygiene:** because the key travels in the URL, exception messages never include the URL, exceptions are raised `from None` (no chained httpx exception carrying the URL), and the `httpx` logger is raised to `WARNING` so request URLs are not logged.
- **CLI:** a small `weather-ingest fetch <city>` command exercises the client end to end before the database and API exist.

## Alternatives considered

- **One Call API 3.0**: richer data (forecasts, alerts) but requires a separate subscription, even for the free quota, and needs coordinates instead of a city name.
- **requests**: equally capable for this use case, but httpx offers first-class timeouts, a transport layer that is trivial to mock with `respx`, and an async API if we ever need concurrent ingestion.
- **Async client from the start**: the ingestion is one request per API call; a sync client keeps the code simpler and works well inside FastAPI's thread pool. Switching later only touches this module.
- **Retries with backoff**: useful for 429/5xx, but they hide failures in a demo and complicate tests. Left as future work.

## Consequences

- Callers depend only on `OpenWeatherClient` and its exceptions, not on httpx.
- Tests run offline: `respx` mocks the transport, and a recorded payload in `tests/fixtures/` keeps them realistic.
- If OpenWeather changes or drops a field we declared, validation fails loudly with `UnexpectedResponseError` instead of storing bad data.
