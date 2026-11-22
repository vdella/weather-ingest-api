"""Helpers to match user-typed city names against stored ones."""

import unicodedata
from dataclasses import dataclass


def search_key(name: str) -> str:
    """Case- and accent-insensitive key: ``"  Florianópolis "`` -> ``"florianopolis"``."""
    decomposed = unicodedata.normalize("NFKD", name.strip())
    without_accents = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return " ".join(without_accents.casefold().split())


@dataclass(frozen=True, slots=True)
class CityQuery:
    name: str
    country_code: str | None = None

    @classmethod
    def parse(cls, raw: str) -> "CityQuery":
        """Parse OpenWeather's ``"City[,State][,CC]"`` format into a lookup key."""
        parts = [part.strip() for part in raw.split(",") if part.strip()]
        if not parts:
            raise ValueError("city must not be empty")
        country = parts[-1].upper() if len(parts) > 1 and len(parts[-1]) == 2 else None
        return cls(name=search_key(parts[0]), country_code=country)
