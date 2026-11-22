# ADR-0005: PostgreSQL with SQLAlchemy 2.0, psycopg 3 and Alembic

- **Status:** Accepted
- **Date:** 2026-11-22

## Context

The extracted observations must be stored in a relational database (MySQL or PostgreSQL), and the evaluation looks at how well the tables are structured.
The schema must be created the same way on a laptop, in CI and in Docker, and it must be able to evolve.

## Decision

- **PostgreSQL 16.** It has `JSONB` to keep the raw payload alongside typed columns, `TIMESTAMPTZ`, `INSERT ... ON CONFLICT` for idempotent writes, identity columns and check constraints.
- **SQLAlchemy 2.0** with typed declarative models (`Mapped[...]`), used through a **repository** class that holds all SQL. Services never build queries.
- **psycopg 3** (`postgresql+psycopg://`) as the driver; the binary wheel avoids needing `libpq` headers.
- **Alembic** for versioned migrations. `migrations/env.py` reads the URL from `DATABASE_URL` and uses the models' metadata.
  - Migrations are reviewed like code; a naming convention on `MetaData` gives constraints stable, predictable names.
  - CI runs `alembic upgrade head`, `alembic check` (fails if the models and the migrations differ) and `alembic downgrade base`.
- **Unit of work at the edge.** Repositories never commit. The caller (a CLI command, later an HTTP request) opens a session, commits on success and rolls back on error.
- **Configuration split.** `DatabaseSettings` holds only database options, so running migrations does not require the OpenWeather key.
- **Testing.** Repository tests run against a real PostgreSQL (`TEST_DATABASE_URL`), with the schema built by the real migrations and each test wrapped in a rolled-back transaction. Locally they are skipped when no database is configured; CI always runs them.

## Alternatives considered

- **MySQL**: also allowed by the assessment, but its JSON type is less capable than `JSONB`, it has no `TIMESTAMPTZ`, and its upsert syntax does not support `RETURNING`.
- **Raw SQL with psycopg only**: fewer layers, but we would hand-write mapping and migrations. SQLAlchemy Core still gives full control where needed (the upsert uses the PostgreSQL `insert()` construct).
- **`Base.metadata.create_all()` on startup**: simple, but it cannot alter an existing table, so the first schema change would need a manual step anyway.
- **SQLite for tests**: fast, but does not support `JSONB`, `ON CONFLICT ... RETURNING` with the same semantics, or the check constraints exactly as Postgres does, so it would test a different database.
- **Testcontainers**: starts Postgres from the test suite, but requires Docker on every machine that runs the tests. A CI service container plus an opt-in URL is simpler.

## Consequences

- Developers need a PostgreSQL instance to run the full suite locally (the Docker Compose setup in feature 4 provides one).
- Schema changes require a new Alembic revision; CI fails if the models change without one.
