# ADR-0002: Python 3.12 with uv, ruff, mypy and pytest

- **Status:** Accepted
- **Date:** 2026-11-22

## Context

The assessment prefers Python. We need a toolchain that gives reproducible installs (locally, in CI and in Docker), fast feedback, and enforces a consistent code style without bikeshedding in review.

## Decision

- **Python 3.12** as the minimum supported version (`requires-python = ">=3.12"`). CI also tests on 3.13 to catch forward-compatibility issues early.
- **uv** for environment and dependency management. Dependencies are declared in `pyproject.toml` (PEP 621), dev tools in a PEP 735 `[dependency-groups]` table, and every resolved version is pinned in `uv.lock`, which is committed.
- **hatchling** as the build backend, so the project builds a normal wheel with `uv build`.
- **ruff** for both linting and formatting (replaces flake8, isort, black and pyupgrade with a single, fast tool).
- **mypy in strict mode** on the `app` package.
- **pytest** with `pytest-cov` for tests and coverage.

## Alternatives considered

- **pip + requirements.txt**: universally known, but no lockfile with hashes for the full graph unless we add pip-tools, and it is noticeably slower in CI and Docker builds. The project still installs with plain `pip install .` because metadata is standard PEP 621.
- **Poetry**: mature, but uses its own non-standard sections for dev dependencies and is slower to resolve. uv covers the same features with standard metadata.
- **black + isort + flake8**: three tools and three configurations for what ruff does alone.

## Consequences

- Contributors need `uv` installed (a single static binary). `uv sync` creates `.venv` with the exact locked versions.
- CI and the Docker image install with `uv sync --locked`, which fails if `uv.lock` is out of date with `pyproject.toml`, so drift is caught in review.
- Strict typing has an upfront cost on every module, but catches contract mismatches between layers (client, service, repository, API) before runtime.
