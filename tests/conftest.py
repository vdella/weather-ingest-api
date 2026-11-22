from collections.abc import Iterator
from pathlib import Path

import pytest

from app.core.config import get_settings


@pytest.fixture(autouse=True)
def _isolated_settings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    """Keep tests independent from a developer's local `.env` and shell environment."""
    monkeypatch.chdir(tmp_path)  # no `.env` in an empty temp dir
    monkeypatch.setenv("OPENWEATHER_API_KEY", "test-api-key")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
