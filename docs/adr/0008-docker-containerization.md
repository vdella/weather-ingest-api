# ADR-0008: Multi-stage Docker image and a Docker Compose stack

- **Status:** Accepted, amended by [ADR-0010](0010-database-port-not-published.md) (database port)
- **Date:** 2026-11-22

## Context

The assessment lists Docker as optional; this project treats it as required. Anyone must be able to run the API and the database on any machine with one command, and the evaluation looks at whether the environment is reproducible and works.

## Decision

**Image (`Dockerfile`)**

- **Multi-stage build.** The builder stage uses `uv` to install the locked, production-only dependencies (`uv sync --locked --no-dev`) into `/opt/venv`. The runtime stage copies only that virtualenv, `alembic.ini`, `migrations/` and the entrypoint. No compilers, no `uv`, no tests, no source tree.
- **Base image:** `python:3.12-slim-bookworm` in both stages, so the venv's interpreter path is identical. `psycopg[binary]` ships its own `libpq`, so no system packages are installed.
- **Layer caching:** dependencies are installed before the application code is copied, and the uv cache is a BuildKit cache mount. Changing code does not reinstall dependencies.
- **Pinned versions:** the uv image is pinned to a version and every Python package comes from `uv.lock`.
- **Non-root user** (uid 10001) and a Docker `HEALTHCHECK` that calls `/health` with the Python standard library (no `curl` in the image).
- **Entrypoint with modes:** `api` (default) runs `alembic upgrade head` and then `exec`s Uvicorn (PID 1, so it receives stop signals); `migrate` only migrates; any other command runs as-is, e.g. `docker compose run --rm api weather-ingest ingest "Florianopolis,BR"`.
- `.dockerignore` keeps `.env`, `.git` and the local virtualenv out of the build context.

**Stack (`docker-compose.yml`)**

- `db`: `postgres:16-alpine`, a named volume for the data, and a `pg_isready` healthcheck. The port is published on `127.0.0.1` only, for `psql` or running the integration tests from the host.
- `api`: built from the Dockerfile, `depends_on: db: condition: service_healthy`, configured from `.env`. `DATABASE_URL` is built from the `POSTGRES_*` variables so the credentials are defined once.

**Verification and delivery**

- The tests workflow builds the image and runs `docker compose up --wait`, then checks `/health`, that the migrations ran, that OpenWeather errors are mapped, and that the container is not running as root.
- The release workflow publishes `ghcr.io/<owner>/weather-ingest-api` with `X.Y.Z`, `X.Y` and `latest` tags for every release.

## Alternatives considered

- **Single-stage image:** simpler, but ships the build toolchain and the uv cache, making the image larger.
- **Alpine Python base:** smaller, but musl often forces building wheels from source, and slim with prebuilt wheels is both smaller in practice and faster to build.
- **Distroless runtime:** smaller attack surface, but no shell for the entrypoint script and harder to debug. Worth revisiting for production.
- **Running migrations in a separate one-shot Compose service:** the cleanest choice with several API replicas (avoids concurrent migrations). With a single API container, migrating in the entrypoint is simpler; the `migrate` mode is already there for a future init job.
- **Gunicorn with Uvicorn workers:** useful for several processes per container, but in a container orchestrator scaling usually happens with replicas, and a single Uvicorn process keeps signals and logs simple.

## Consequences

- `docker compose up --build` is the only command needed after creating `.env`.
- If `POSTGRES_PASSWORD` contains URL-reserved characters (`@`, `:`, `/`, `%`), it must be URL-encoded in the derived `DATABASE_URL`.
- Docker problems are caught in CI, not only on a reviewer's machine.
