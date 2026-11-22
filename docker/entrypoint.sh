#!/bin/sh
# Container entrypoint.
#   api (default)   apply database migrations, then serve the REST API
#   migrate         only apply database migrations
#   <anything else> run it as-is, e.g. `weather-ingest ingest "Florianopolis,BR"`
set -eu

case "${1:-api}" in
  api)
    alembic upgrade head
    exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers
    ;;
  migrate)
    exec alembic upgrade head
    ;;
  *)
    exec "$@"
    ;;
esac
