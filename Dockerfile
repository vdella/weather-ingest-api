# syntax=docker/dockerfile:1.7

ARG PYTHON_VERSION=3.12

# --- uv binary -------------------------------------------------------------------------------
FROM ghcr.io/astral-sh/uv:0.11.29 AS uv

# --- Build: resolve the locked dependencies into a self-contained virtualenv ----------------
FROM python:${PYTHON_VERSION}-slim-bookworm AS builder

COPY --from=uv /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /src

# Dependencies first: this layer is reused until pyproject.toml or uv.lock change.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --locked --no-dev --no-install-project

# Then the application itself, installed as a regular (non-editable) package.
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY app ./app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

# --- Runtime: no compilers, no uv, no source tree, non-root ----------------------------------
FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime

LABEL org.opencontainers.image.title="weather-ingest-api" \
      org.opencontainers.image.description="OpenWeather -> PostgreSQL -> REST API" \
      org.opencontainers.image.source="https://github.com/vdella/weather-ingest-api" \
      org.opencontainers.image.licenses="MIT"

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --home-dir /app --no-create-home app

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY alembic.ini ./
COPY migrations ./migrations
COPY --chmod=0755 docker/entrypoint.sh /usr/local/bin/docker-entrypoint

USER app
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=20s --retries=5 \
  CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen(f\"http://127.0.0.1:{os.environ.get('PORT', '8000')}/health\", timeout=2)"]

ENTRYPOINT ["docker-entrypoint"]
CMD ["api"]
