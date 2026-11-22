import json
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from alembic import command
from alembic.config import Config as AlembicConfig
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from app.core.config import get_database_settings, get_settings


@pytest.fixture(autouse=True)
def _isolated_settings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    """Keep tests independent from a developer's local `.env` and shell environment."""
    monkeypatch.chdir(tmp_path)  # no `.env` in an empty temp dir
    monkeypatch.setenv("OPENWEATHER_API_KEY", "test-api-key")
    get_settings.cache_clear()
    get_database_settings.cache_clear()
    yield
    get_settings.cache_clear()
    get_database_settings.cache_clear()


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def openweather_payload() -> dict[str, Any]:
    """A realistic OpenWeather *Current Weather* response for Florianópolis."""
    data: dict[str, Any] = json.loads(
        (FIXTURES_DIR / "openweather_current_florianopolis.json").read_text(encoding="utf-8")
    )
    return data


# --- Database (integration) ----------------------------------------------------------------
#
# Tests that use `db_session` run against a real PostgreSQL pointed to by TEST_DATABASE_URL
# (CI provides one). The schema is created with the real Alembic migrations, each test runs
# inside a transaction that is rolled back, and the schema is downgraded at the end.

ROOT_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def db_engine() -> Iterator[Engine]:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not set")

    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = url
    get_database_settings.cache_clear()
    alembic_cfg = AlembicConfig(str(ROOT_DIR / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")

    engine = create_engine(url)
    try:
        yield engine
    finally:
        engine.dispose()
        command.downgrade(alembic_cfg, "base")
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous


@pytest.fixture
def db_session(db_engine: Engine) -> Iterator[Session]:
    with db_engine.connect() as connection:
        transaction = connection.begin()
        session = Session(bind=connection, join_transaction_mode="create_savepoint")
        try:
            yield session
        finally:
            session.close()
            transaction.rollback()
