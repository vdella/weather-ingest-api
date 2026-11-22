# ADR-0007: REST API with FastAPI, OpenAPI/Swagger and a Postman collection

- **Status:** Accepted
- **Date:** 2026-11-22

## Context

The stored data must be queryable remotely through a simple RESTful API, documented with Swagger or Postman.
The API also needs a way to trigger ingestion, because the assessment does not prescribe a scheduler.

## Decision

- **Framework: FastAPI** served by **Uvicorn**. Request validation, response serialization and the OpenAPI document come from the same type hints, so the Swagger UI (`/docs`) and ReDoc (`/redoc`) never drift from the code.
- **Postman:** a hand-curated collection in `docs/postman_collection.json` with a `baseUrl` variable, for reviewers who prefer Postman.
- **Resource design**, versioned under `/api/v1`:

  | Method | Path | Purpose |
  |---|---|---|
  | `POST` | `/weather/fetch?city=&units=&lang=` | Fetch from OpenWeather and store; returns `201` with the stored reading |
  | `GET` | `/weather?city=&from=&to=&limit=&offset=` | List, newest first, with a `total` for pagination |
  | `GET` | `/weather/latest?city=` | Newest reading for a city |
  | `GET` | `/weather/{id}` | One reading |
  | `GET` | `/health` | Liveness and database check (unversioned, for infrastructure) |

- **Ingestion via `POST`.** It changes server state and calls a third party, so it is not a `GET`. Thanks to the upsert, repeating it is safe.
- **Response models are separate from the ORM.** `raw_payload` and the internal `city_search_name` are not exposed; decimals are serialized as strings to keep their exact value.
- **Error contract.** Every error body is `{"detail": ...}`. OpenWeather failures map to: city not found → `404`; invalid key or unexpected upstream answer → `502`; rate limited, timeout, 5xx → `503`. Invalid parameters → `422`.
- **Pagination:** `limit` (1–100, default 20) and `offset`, with the total count in the response. Time range is half-open: `from` inclusive, `to` exclusive.
- **Dependencies:** one SQLAlchemy session per request (commit on success, rollback on error) and one pooled OpenWeather client created in the application lifespan. Tests replace them with `app.dependency_overrides`.
- **Synchronous handlers.** SQLAlchemy and the httpx client are sync; FastAPI runs sync endpoints in its thread pool, which is plenty for this workload.

## Alternatives considered

- **Flask + flask-smorest / Django REST Framework**: both mature, but they need extra libraries or more boilerplate to get validated, typed, self-documented endpoints. DRF also brings Django's ORM, which overlaps with SQLAlchemy.
- **`GET /weather/{city}` that fetches on demand**: convenient but a `GET` with side effects, and it mixes reading stored data with calling OpenWeather.
- **Cursor-based pagination**: better for very large tables, but limit/offset is simpler to use from Swagger and is enough here.
- **Authentication on the API**: out of scope for the assessment; listed as future work. The OpenWeather key never leaves the server.
- **Async endpoints with asyncpg**: more throughput under heavy concurrency, but it would complicate the stack for no visible benefit here.

## Consequences

- Swagger UI at `/docs` is the quickest way to try the service; no extra tooling is needed.
- The Postman collection is maintained by hand and must be updated when endpoints change.
