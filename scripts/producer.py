"""Real-time producer for the weather + air quality pipeline.

One run = one poll. For every city in config/cities.json it calls two
Open-Meteo endpoints (no API key required):

  - Weather:     current temperature, humidity, wind speed, weather code
  - Air quality: current pm10, pm2_5, european_aqi, ozone

Each city becomes one JSON record (with the two API "current" blocks kept
nested, so the Spark job does the real flattening/cleaning). All records for
a run are written as one newline-delimited JSON file into data/landing/.
Airflow (or cron) calls this every 5 minutes, which is what makes the source
"real-time": the landing folder is an append-only stream of observations.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CITIES_FILE = PROJECT_ROOT / "config" / "cities.json"
LANDING_DIR = Path(os.environ.get("LANDING_DIR", PROJECT_ROOT / "data" / "landing"))

WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

WEATHER_FIELDS = "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
AIR_QUALITY_FIELDS = "pm10,pm2_5,european_aqi,ozone"

REQUEST_TIMEOUT = 20  # seconds


def fetch_current(session: requests.Session, url: str, city: dict, fields: str) -> dict:
    """Call one Open-Meteo endpoint and return its 'current' block."""
    params = {
        "latitude": city["latitude"],
        "longitude": city["longitude"],
        "current": fields,
        "timezone": "UTC",  # UTC keeps observation timestamps comparable across cities
    }
    response = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json().get("current", {})


def main() -> int:
    with open(CITIES_FILE, encoding="utf-8") as handle:
        cities = json.load(handle)

    LANDING_DIR.mkdir(parents=True, exist_ok=True)
    ingested_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    records: list[dict] = []
    session = requests.Session()
    for city in cities:
        try:
            weather = fetch_current(session, WEATHER_URL, city, WEATHER_FIELDS)
            air_quality = fetch_current(session, AIR_QUALITY_URL, city, AIR_QUALITY_FIELDS)
        except requests.RequestException as error:
            # Skip a single failing city instead of failing the whole run.
            print(f"[producer] WARN  {city['city']}: {error}", file=sys.stderr)
            continue

        records.append(
            {
                "city": city["city"],
                "country": city["country"],
                "latitude": city["latitude"],
                "longitude": city["longitude"],
                "weather": weather,
                "air_quality": air_quality,
                "ingested_at": ingested_at,
            }
        )
        print(f"[producer] OK    {city['city']}")

    if not records:
        print("[producer] ERROR no records fetched this run", file=sys.stderr)
        return 1

    # Newline-delimited JSON: one record per line is what the Spark file
    # source reads most reliably.
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = LANDING_DIR / f"readings_{stamp}.json"
    with open(out_path, "w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")

    print(f"[producer] wrote {len(records)} records to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
