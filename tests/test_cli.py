from typing import Any

import pytest
import respx

from app.cli import main

URL = "https://api.openweathermap.org/data/2.5/weather"


@respx.mock
def test_fetch_prints_the_observation(
    capsys: pytest.CaptureFixture[str], openweather_payload: dict[str, Any]
) -> None:
    route = respx.get(URL).respond(200, json=openweather_payload)

    exit_code = main(["fetch", "Florianopolis,BR", "--units", "imperial"])

    assert exit_code == 0
    assert route.calls.last.request.url.params["units"] == "imperial"
    assert '"name": "Florianópolis"' in capsys.readouterr().out


@respx.mock
def test_fetch_reports_errors_on_stderr(capsys: pytest.CaptureFixture[str]) -> None:
    respx.get(URL).respond(404, json={"cod": "404", "message": "city not found"})

    exit_code = main(["fetch", "Atlantis"])

    assert exit_code == 1
    assert "City not found" in capsys.readouterr().err
