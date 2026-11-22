# ADR-0010: Do not publish the database port by default

- **Status:** Accepted (amends [ADR-0008](0008-docker-containerization.md))
- **Date:** 2026-11-22

## Context

ADR-0008 published PostgreSQL on `127.0.0.1:5432` so that `psql` and the integration tests could reach it from the host.

Following the README on a clean clone, `docker compose up` failed on a machine that already ran PostgreSQL: the `db` container could not bind port 5432 (`address already in use`), and the API never started because it waits for the database to be healthy. Many developers, and so many evaluators, run a local PostgreSQL. The README's first command must work on any machine.

## Decision

- `docker-compose.yml` no longer publishes the database port. The API reaches PostgreSQL over the Compose network (`db:5432`), and `docker compose exec db psql ...` works without a published port.
- Host access is opt-in through `docker-compose.db-port.yml`, still bound to `127.0.0.1`, on the port set by `POSTGRES_PORT`:

  ```bash
  docker compose -f docker-compose.yml -f docker-compose.db-port.yml up -d
  ```

- The API port stays published (that is how the service is used) and can be changed with `API_PORT`.

## Alternatives considered

- **Keep publishing, but on an unusual default port (e.g. 5433)**: fewer clashes, but still a failure mode on the first command, and the host port is not needed to use the service.
- **`docker-compose.override.yml`**: Compose loads it automatically, so committing it would bring back the default publication; leaving it untracked means every developer has to write it.
- **Compose profiles**: profiles select services, not ports of an existing service.

## Consequences

- The default stack starts regardless of what is listening on 5432.
- Running the integration tests against the Compose database needs the extra `-f docker-compose.db-port.yml`; the README shows the command.
