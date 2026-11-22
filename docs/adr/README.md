# Architecture Decision Records

This folder records the significant engineering decisions taken in this project, one decision per file.
Each record explains the context, the decision, the alternatives that were considered and the consequences.

- Records are numbered sequentially and never renumbered.
- A record is never edited to change its meaning. To revise a decision, add a new record and mark the old one as `Superseded by ADR-NNNN`.
- New records start from [`template.md`](template.md) and land in the same pull request as the code that implements them.

| ADR | Title | Status |
|---|---|---|
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions | Accepted |
| [0002](0002-python-and-uv-toolchain.md) | Python 3.12 with uv, ruff, mypy and pytest | Accepted |
| [0003](0003-ci-and-release-strategy.md) | GitHub Actions for CI and release-please for releases | Accepted |
| [0004](0004-openweather-client.md) | OpenWeather Current Weather API through a dedicated httpx client | Accepted |
| [0005](0005-postgresql-sqlalchemy-alembic.md) | PostgreSQL with SQLAlchemy 2.0, psycopg 3 and Alembic | Accepted |
| [0006](0006-weather-readings-schema.md) | One `weather_readings` table with a natural key and idempotent upserts | Accepted |
| [0007](0007-rest-api-fastapi.md) | REST API with FastAPI, OpenAPI/Swagger and a Postman collection | Accepted |
| [0008](0008-docker-containerization.md) | Multi-stage Docker image and a Docker Compose stack | Accepted |
