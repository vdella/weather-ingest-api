from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.api.deps import get_session
from app.main import create_app


class FakeSession:
    def __init__(self, fail: bool) -> None:
        self.fail = fail

    def execute(self, *args: Any) -> None:
        if self.fail:
            raise OperationalError("SELECT 1", {}, Exception("connection refused"))


def make_client(fail: bool) -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: FakeSession(fail)
    with TestClient(app) as client:
        yield client


@pytest.fixture
def healthy_client() -> Iterator[TestClient]:
    yield from make_client(fail=False)


@pytest.fixture
def unhealthy_client() -> Iterator[TestClient]:
    yield from make_client(fail=True)


def test_health_ok(healthy_client: TestClient) -> None:
    response = healthy_client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database"] == "ok"


def test_health_reports_database_outage(unhealthy_client: TestClient) -> None:
    response = unhealthy_client.get("/health")

    assert response.status_code == 503
    assert response.json()["database"] == "unavailable"
