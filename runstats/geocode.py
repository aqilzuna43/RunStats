from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .models import ActivityData

GEOCODE_CACHE_PATH = Path(".runstats_geocode_cache.json")
GEOCODER_URL = "https://nominatim.openstreetmap.org/reverse"
USER_AGENT = "runstats/0.1.0 (local reverse geocoder)"


def reverse_geocode_activity(activity: ActivityData, cache_path: str | Path = GEOCODE_CACHE_PATH) -> str | None:
    coordinate = activity.start_coordinate
    if coordinate is None:
        return None
    latitude, longitude = coordinate
    return reverse_geocode(latitude, longitude, cache_path=cache_path)


def reverse_geocode(latitude: float, longitude: float, cache_path: str | Path = GEOCODE_CACHE_PATH) -> str | None:
    cache_file = Path(cache_path)
    cache = _load_cache(cache_file)
    cache_key = _cache_key(latitude, longitude)

    if cache_key in cache:
        return cache[cache_key]

    payload = _fetch_reverse_geocode(latitude, longitude)
    label = _format_location_label(payload)
    if label is None:
        return None

    cache[cache_key] = label
    cache_file.write_text(json.dumps(cache, indent=2, sort_keys=True), encoding="utf-8")
    return label


def _fetch_reverse_geocode(latitude: float, longitude: float) -> dict[str, Any]:
    query = urlencode(
        {
            "format": "jsonv2",
            "lat": f"{latitude:.8f}",
            "lon": f"{longitude:.8f}",
            "zoom": "14",
            "addressdetails": "1",
            "accept-language": "en",
        }
    )
    request = Request(f"{GEOCODER_URL}?{query}", headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _format_location_label(payload: dict[str, Any]) -> str | None:
    address = payload.get("address")
    if not isinstance(address, dict):
        return None

    primary = _first_present(
        address,
        [
            "neighbourhood",
            "suburb",
            "quarter",
            "hamlet",
            "village",
            "town",
            "city_district",
            "city",
            "municipality",
            "county",
        ],
    )
    secondary = _first_present(
        address,
        [
            "city",
            "town",
            "municipality",
            "county",
            "state_district",
            "state",
            "country",
        ],
    )

    if primary and secondary:
        if primary == secondary:
            return _prefer_ascii_label(primary)
        return _prefer_ascii_parts(primary, secondary)
    return _prefer_ascii_label(primary or secondary)


def _first_present(address: dict[str, Any], keys: list[str]) -> str | None:
    for key in keys:
        value = address.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _prefer_ascii_parts(primary: str, secondary: str) -> str:
    ascii_parts = [_prefer_ascii_label(primary), _prefer_ascii_label(secondary)]
    ascii_parts = [part for part in ascii_parts if part]
    if ascii_parts:
        unique_parts: list[str] = []
        for part in ascii_parts:
            if part not in unique_parts:
                unique_parts.append(part)
        return ", ".join(unique_parts)
    return f"{primary}, {secondary}"


def _prefer_ascii_label(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    if value.isascii():
        return value

    ascii_chunks = [chunk.strip() for chunk in value.split(",") if chunk.strip() and chunk.strip().isascii()]
    if ascii_chunks:
        return ", ".join(ascii_chunks)

    return None


def _load_cache(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(key): str(value) for key, value in data.items()}


def _cache_key(latitude: float, longitude: float) -> str:
    return f"{latitude:.5f},{longitude:.5f}"


__all__ = [
    "GEOCODE_CACHE_PATH",
    "reverse_geocode",
    "reverse_geocode_activity",
]
