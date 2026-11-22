"""Command-line entry point: ``weather-ingest fetch <city>``.

Useful to check the OpenWeather integration (and your API key) without starting the API.
"""

import argparse
import json
import sys
from collections.abc import Sequence
from typing import get_args

from app.clients.openweather import OpenWeatherClient, OpenWeatherError
from app.core.config import Units, get_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="weather-ingest", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    fetch = commands.add_parser("fetch", help="Fetch the current weather for a city")
    fetch.add_argument("city", help='City name, optionally with a country code: "Florianopolis,BR"')
    fetch.add_argument("--units", choices=get_args(Units), help="Overrides DEFAULT_UNITS")
    fetch.add_argument("--lang", help="Overrides DEFAULT_LANG")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    with OpenWeatherClient.from_settings(get_settings()) as client:
        try:
            result = client.get_current_weather(args.city, units=args.units, lang=args.lang)
        except OpenWeatherError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    print(json.dumps(result.data.model_dump(mode="json"), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
