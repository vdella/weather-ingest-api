# weather-ingest-api

> A data pipeline that pulls current weather data from the OpenWeather API, stores it in PostgreSQL, and serves it through a documented REST API. The whole stack runs in Docker Compose.

[![Tests](https://github.com/vdella/weather-ingest-api/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/vdella/weather-ingest-api/actions/workflows/tests.yml)
[![Release](https://github.com/vdella/weather-ingest-api/actions/workflows/release.yml/badge.svg)](https://github.com/vdella/weather-ingest-api/actions/workflows/release.yml)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.11x-009688)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791)
![Docker](https://img.shields.io/badge/docker-compose-2496ED)

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Getting an OpenWeather API Key](#getting-an-openweather-api-key)
- [Configuration](#configuration)
- [Running with Docker (recommended)](#running-with-docker-recommended)
- [Running Locally (without Docker)](#running-locally-without-docker)
- [Using the API](#using-the-api)
- [Database Schema](#database-schema)
- [Testing](#testing)
- [Design Decisions](#design-decisions)
- [Development Workflow](#development-workflow)
- [What I Would Do With More Time](#what-i-would-do-with-more-time)

---

## Overview

The project covers four steps:

1. **Extract**: send an authenticated `GET` request to the OpenWeather *Current Weather* endpoint. The query parameters (city, units, language) are dynamic, and the API key is read from the environment.
2. **Store**: save the normalized result in a relational table in PostgreSQL. Ingestion is **idempotent**, so fetching the same observation twice never creates duplicate rows.
3. **Serve**: expose the stored data through a RESTful API with filtering and pagination. The API is documented with OpenAPI (Swagger UI).
4. **Ship**: build and run the API and the database with one Docker Compose command.

## Architecture

```mermaid
flowchart LR
    OW[(OpenWeather API)] -->|GET /data/2.5/weather| C[OpenWeather client]
    subgraph API container
        C --> S[Ingestion service]
        S --> R[Repository]
        Q[REST routes] --> R
    end
    R <-->|SQL| DB[(PostgreSQL)]
    U[User / Swagger / Postman] -->|HTTP| Q
```

The code is split into layers so that each part has one job:

| Layer | Responsibility |
|---|---|
| `clients/` | Talks to OpenWeather (HTTP, auth, timeouts, error mapping) |
| `services/` | Business logic: fetch, normalize, persist |
| `repositories/` | All SQL and database access |
| `api/` | HTTP routes, request validation, response schemas |

## Tech Stack

- **Python 3.12**
- **FastAPI**: REST API with automatic OpenAPI docs
- **SQLAlchemy 2.x** with **Alembic**: ORM and versioned schema migrations
- **PostgreSQL 16**
- **httpx**: HTTP client for OpenWeather
- **Pydantic / pydantic-settings**: validation and typed configuration
- **pytest**: tests (the external API is mocked)
- **uv**, **ruff**, **mypy**: dependency locking, lint/format, static typing
- **Docker & Docker Compose**
- **GitHub Actions** with **release-please**: CI and automated releases

## Project Structure

```
weather-ingest-api/
├── app/
│   ├── api/              # Routes and response schemas
│   ├── clients/          # OpenWeather HTTP client
│   ├── services/         # Ingestion logic
│   ├── repositories/     # Database access
│   ├── models/           # ORM models
│   ├── core/             # Settings, logging, DB session
│   └── main.py           # FastAPI entrypoint
├── migrations/           # Alembic migrations
├── tests/
├── docs/
│   ├── adr/              # Architecture Decision Records
│   └── postman_collection.json
├── .github/workflows/    # CI (tests) and release automation
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── pyproject.toml
├── uv.lock
└── README.md
```

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose v2
- An OpenWeather API key (free tier is enough)
- *(Optional, for running locally)* Python 3.12+, [uv](https://docs.astral.sh/uv/) and a local PostgreSQL instance

## Getting an OpenWeather API Key

1. Create a free account at [openweathermap.org](https://openweathermap.org/api).
2. Go to **My API keys** and copy the default key, or generate a new one.
3. **Note:** a new key can take some time to activate. Until then, requests may return `401 Unauthorized`.

## Configuration

All configuration comes from environment variables. Start by copying the template:

```bash
cp .env.example .env
```

Then fill in your values:

| Variable | Description | Example |
|---|---|---|
| `OPENWEATHER_API_KEY` | Your OpenWeather API key **(required)** | `abc123...` |
| `OPENWEATHER_BASE_URL` | OpenWeather base URL | `https://api.openweathermap.org/data/2.5` |
| `OPENWEATHER_TIMEOUT_SECONDS` | HTTP timeout for external calls | `10` |
| `DEFAULT_UNITS` | `standard`, `metric` or `imperial` | `metric` |
| `DEFAULT_LANG` | Language for weather descriptions | `pt_br` |
| `POSTGRES_USER` | Database user | `weather` |
| `POSTGRES_PASSWORD` | Database password | `change-me` |
| `POSTGRES_DB` | Database name | `weather` |
| `DATABASE_URL` | SQLAlchemy connection string | `postgresql+psycopg://weather:change-me@db:5432/weather` |

> `.env` is listed in `.gitignore` and must never be committed. Only `.env.example` is versioned.

## Running with Docker (recommended)

```bash
git clone https://github.com/<your-user>/weather-ingest-api.git
cd weather-ingest-api
cp .env.example .env        # then set OPENWEATHER_API_KEY
docker compose up --build
```

What happens:
- PostgreSQL starts, and its healthcheck reports when it is ready.
- The API container waits for the database to be **healthy**, applies the migrations, and starts on port `8000`.
- Data is persisted in a named Docker volume, so it survives restarts.

Once it is up:
- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- Health check: <http://localhost:8000/health>

To stop the stack:

```bash
docker compose down        # keep the data
docker compose down -v     # also delete the database volume
```

## Running Locally (without Docker)

```bash
uv sync                     # creates .venv with the exact versions from uv.lock
cp .env.example .env        # point DATABASE_URL to your local Postgres
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

## Using the API

All endpoints are versioned under `/api/v1`.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/weather/fetch` | Fetch current weather for a city from OpenWeather and store it |
| `GET` | `/api/v1/weather` | List stored readings (filters and pagination) |
| `GET` | `/api/v1/weather/{id}` | Get a single reading by id |
| `GET` | `/api/v1/weather/latest` | Get the most recent reading for a city |
| `GET` | `/health` | Liveness check (API and database) |

### Query parameters

| Endpoint | Parameter | Description |
|---|---|---|
| `POST /weather/fetch` | `city` *(required)* | City name, e.g. `Florianopolis` or `Florianopolis,BR` |
| | `units` | Overrides `DEFAULT_UNITS` |
| | `lang` | Overrides `DEFAULT_LANG` |
| `GET /weather` | `city` | Filter by city name (case-insensitive) |
| | `from` / `to` | ISO-8601 time range on the observation time |
| | `limit` / `offset` | Pagination (default `limit=20`, max `100`) |
| `GET /weather/latest` | `city` *(required)* | City name |

### Examples

Ingest the current weather for Florianópolis:

```bash
curl -X POST "http://localhost:8000/api/v1/weather/fetch?city=Florianopolis,BR"
```

List the stored readings for a city within a time range:

```bash
curl "http://localhost:8000/api/v1/weather?city=Florianopolis&from=2026-11-22T00:00:00Z&to=2026-11-23T00:00:00Z&limit=10"
```

Get the latest reading:

```bash
curl "http://localhost:8000/api/v1/weather/latest?city=Florianopolis"
```

### Error responses

| Status | When |
|---|---|
| `404 Not Found` | The city does not exist on OpenWeather, or no stored reading matches |
| `422 Unprocessable Entity` | Invalid query parameters |
| `502 Bad Gateway` | OpenWeather returned an unexpected error or invalid key |
| `503 Service Unavailable` | OpenWeather rate limit hit or request timed out |

### Postman

A ready-to-import collection is available at [`docs/postman_collection.json`](docs/postman_collection.json).

## Database Schema

Table: **`weather_readings`**

| Column | Type | Notes |
|---|---|---|
| `id` | `BIGSERIAL` | Primary key |
| `city_id` | `INTEGER` | OpenWeather city id |
| `city_name` | `TEXT` | |
| `country_code` | `CHAR(2)` | ISO 3166-1 alpha-2 |
| `latitude` / `longitude` | `NUMERIC(8,5)` | |
| `observed_at` | `TIMESTAMPTZ` | When OpenWeather measured the data (`dt`) |
| `fetched_at` | `TIMESTAMPTZ` | When this service collected it (default `now()`) |
| `units` | `TEXT` | Unit system used for the values below |
| `temperature` / `feels_like` / `temp_min` / `temp_max` | `NUMERIC(5,2)` | |
| `humidity` | `SMALLINT` | % |
| `pressure` | `SMALLINT` | hPa |
| `wind_speed` | `NUMERIC(5,2)` | |
| `wind_deg` | `SMALLINT` | Degrees |
| `cloudiness` | `SMALLINT` | % |
| `weather_main` / `weather_description` | `TEXT` | e.g. `Clouds` / `nublado` |
| `raw_payload` | `JSONB` | Original response, kept for auditing and reprocessing |

**Constraints and indexes**
- `UNIQUE (city_id, observed_at)`: makes ingestion idempotent (an upsert on conflict).
- Index on `(lower(city_name), observed_at DESC)`: supports the "filter by city, newest first" queries.

## Testing

```bash
uv run pytest               # tests
uv run ruff check .         # lint
uv run ruff format .        # format
uv run mypy                 # type-check
```

The OpenWeather client is mocked in the tests, so **no API key is needed** to run them.
Tests that need a real database run only when `TEST_DATABASE_URL` points to a PostgreSQL instance (CI provides one); otherwise they are skipped.

## Design Decisions

- **Ingestion through an HTTP endpoint.** A `POST` endpoint keeps the demo self-contained and easy to try in Swagger. A scheduled job (cron, or a worker with a queue) would be the natural next step for continuous collection.
- **Separate observation time and collection time.** OpenWeather updates its data every few minutes. Keeping both timestamps makes deduplication and freshness checks explicit.
- **Idempotent writes.** The unique constraint plus an upsert means that retries and repeated calls are safe.
- **Raw payload in `JSONB`.** Typed columns make querying easy, and the raw JSON keeps all the information in case the schema needs to change later.
- **Layered structure.** HTTP, business logic, and persistence are decoupled, so each layer can be tested on its own.
- **Configuration from the environment only.** No secrets live in code or in the Git history.

Every significant choice is recorded, with the alternatives that were rejected, as an [Architecture Decision Record](docs/adr/README.md).

## Development Workflow

The project is developed through small pull requests against `main`:

| Branch | Scope |
|---|---|
| `chore/bootstrap` | Project skeleton, CI and release workflows, README, ADR process |
| `feat/01-extraction` | OpenWeather client: authenticated `GET` with dynamic query parameters |
| `feat/02-storage` | PostgreSQL table, migrations and idempotent persistence |
| `feat/03-rest-api` | REST API with Swagger UI and a Postman collection |
| `feat/04-docker` | Dockerfile and Docker Compose for the API and the database |

- **Commits** follow [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `test:`, `docs:`, `ci:`, ...).
- **CI**: every PR to `main` runs lint, type-check and tests ([`tests.yml`](.github/workflows/tests.yml)).
- **Releases**: [release-please](https://github.com/googleapis/release-please) keeps a release PR open on `main`; merging it tags a new version and publishes a GitHub Release with the changelog ([`release.yml`](.github/workflows/release.yml)).

See [ADR-0003](docs/adr/0003-ci-and-release-strategy.md) for the details.

## What I Would Do With More Time

- Scheduled ingestion for a configurable list of cities
- Retries with exponential backoff for transient OpenWeather failures
- Structured logging and basic metrics (request latency, ingestion success rate)
- Authentication on the read API (API key or OAuth2)