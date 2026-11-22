"""Command-line entry point.

weather-ingest fetch  <city>   # call OpenWeather and print the observation (no database)
weather-ingest ingest <city>   # call OpenWeather and store the observation in PostgreSQL
"""

import argparse
import json
import sys
from collections.abc import Sequence
from typing import get_args

from app.clients.openweather import OpenWeatherClient, OpenWeatherError
from app.core.config import Units, get_settings
from app.core.db import session_scope
from app.repositories.weather_readings import WeatherReadingRepository
from app.services.ingestion import WeatherIngestionService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="weather-ingest",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    commands = parser.add_subparsers(dest="command", required=True)

    for name, help_text in (
        ("fetch", "Fetch the current weather for a city and print it"),
        ("ingest", "Fetch the current weather for a city and store it"),
    ):
        cmd = commands.add_parser(name, help=help_text)
        cmd.add_argument(
            "city", help='City name, optionally with a country code: "Florianopolis,BR"'
        )
        cmd.add_argument("--units", choices=get_args(Units), help="Overrides DEFAULT_UNITS")
        cmd.add_argument("--lang", help="Overrides DEFAULT_LANG")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    with OpenWeatherClient.from_settings(get_settings()) as client:
        try:
            if args.command == "fetch":
                result = client.get_current_weather(args.city, units=args.units, lang=args.lang)
                output = result.data.model_dump(mode="json")
            else:
                with session_scope() as session:
                    service = WeatherIngestionService(client, WeatherReadingRepository(session))
                    reading = service.ingest(args.city, units=args.units, lang=args.lang)
                    output = {
                        "id": reading.id,
                        "city": reading.city_name,
                        "observed_at": reading.observed_at.isoformat(),
                        "temperature": str(reading.temperature),
                        "units": reading.units,
                    }
        except OpenWeatherError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
