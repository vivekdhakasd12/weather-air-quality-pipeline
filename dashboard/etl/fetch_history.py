from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CITIES_FILE = PROJECT_ROOT / "config" / "cities.json"
SEED_FILE = PROJECT_ROOT / "dbt" / "weather" / "seeds" / "cities.csv"
OUT_DIR = PROJECT_ROOT / "dashboard" / "data"

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

WEATHER_HOURLY = (
    "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code,"
    "precipitation,apparent_temperature"
)
AIR_QUALITY_HOURLY = (
    "pm2_5,pm10,european_aqi,ozone,nitrogen_dioxide,sulphur_dioxide,carbon_monoxide"
)

DEFAULT_START = "2025-06-01"
DEFAULT_END = "2026-06-01"
REQUEST_TIMEOUT = 90

AQI_BANDS = [
    (20, "Good"),
    (40, "Fair"),
    (60, "Moderate"),
    (80, "Poor"),
    (100, "Very poor"),
]

COLUMN_ORDER = [
    "city", "country", "country_name", "latitude", "longitude",
    "population", "timezone", "observed_at", "date", "month", "month_name",
    "hour", "weekday", "temperature_2m", "apparent_temperature",
    "relative_humidity_2m", "wind_speed_10m", "precipitation", "weather_code",
    "temperature_band", "pm2_5", "pm10", "european_aqi", "aqi_category",
    "ozone", "nitrogen_dioxide", "sulphur_dioxide", "carbon_monoxide",
    "pm25_exceeds_who_24h", "pm25_exceeds_who_annual",
]


def load_reference() -> dict:
    with open(CITIES_FILE, encoding="utf-8") as handle:
        cities = json.load(handle)
    seed = {}
    with open(SEED_FILE, encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            seed[row["city"]] = row
    for city in cities:
        meta = seed.get(city["city"], {})
        city["country_name"] = meta.get("country_name", city["country"])
        city["population"] = int(meta["population"]) if meta.get("population") else None
        city["timezone"] = meta.get("timezone", "UTC")
    return cities


def fetch_hourly(session, url, lat, lon, hourly, start, end) -> pd.DataFrame:
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": hourly,
        "start_date": start,
        "end_date": end,
        "timezone": "UTC",
    }
    response = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    block = response.json().get("hourly", {})
    if not block or "time" not in block:
        return pd.DataFrame()
    return pd.DataFrame(block)


def add_aqi_category(df: pd.DataFrame) -> None:
    aqi = df["european_aqi"]
    conditions = [aqi <= limit for limit, _ in AQI_BANDS] + [aqi > 100]
    choices = [label for _, label in AQI_BANDS] + ["Extremely poor"]
    df["aqi_category"] = np.select(conditions, choices, default="Unknown")
    df.loc[aqi.isna(), "aqi_category"] = "Unknown"


def add_temperature_band(df: pd.DataFrame) -> None:
    temp = df["temperature_2m"]
    conditions = [temp < 0, temp < 10, temp < 20, temp < 30, temp >= 30]
    choices = ["Freezing", "Cold", "Mild", "Warm", "Hot"]
    df["temperature_band"] = np.select(conditions, choices, default="Unknown")
    df.loc[temp.isna(), "temperature_band"] = "Unknown"


def build(start: str, end: str) -> pd.DataFrame:
    cities = load_reference()
    session = requests.Session()
    frames = []
    for city in cities:
        try:
            weather = fetch_hourly(
                session, ARCHIVE_URL, city["latitude"], city["longitude"],
                WEATHER_HOURLY, start, end,
            )
            air = fetch_hourly(
                session, AIR_QUALITY_URL, city["latitude"], city["longitude"],
                AIR_QUALITY_HOURLY, start, end,
            )
        except requests.RequestException as error:
            print(f"[etl] WARN  {city['city']}: {error}", file=sys.stderr)
            continue
        if weather.empty:
            print(f"[etl] WARN  {city['city']}: no weather rows", file=sys.stderr)
            continue
        frame = weather.merge(air, on="time", how="left") if not air.empty else weather
        frame["city"] = city["city"]
        frame["country"] = city["country"]
        frame["country_name"] = city["country_name"]
        frame["latitude"] = city["latitude"]
        frame["longitude"] = city["longitude"]
        frame["population"] = city["population"]
        frame["timezone"] = city["timezone"]
        frames.append(frame)
        print(f"[etl] OK    {city['city']}: {len(frame)} hourly rows")

    if not frames:
        raise SystemExit("[etl] ERROR no data fetched")

    df = pd.concat(frames, ignore_index=True)
    return clean(df)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df["observed_at"] = pd.to_datetime(df["time"], utc=True)
    df = df.drop(columns=["time"])

    for column in WEATHER_HOURLY.split(",") + AIR_QUALITY_HOURLY.split(","):
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    for column in ["relative_humidity_2m", "weather_code", "european_aqi"]:
        df[column] = df[column].round().astype("Int64")

    df = df.dropna(subset=["city", "observed_at", "temperature_2m"])
    df = df.drop_duplicates(subset=["city", "observed_at"])
    df = df.sort_values(["city", "observed_at"]).reset_index(drop=True)

    add_aqi_category(df)
    add_temperature_band(df)

    local = df["observed_at"]
    df["date"] = local.dt.date.astype("string")
    df["month"] = local.dt.month
    df["month_name"] = local.dt.strftime("%b")
    df["hour"] = local.dt.hour
    df["weekday"] = local.dt.day_name()

    df["pm25_exceeds_who_24h"] = df["pm2_5"] > 15
    df["pm25_exceeds_who_annual"] = df["pm2_5"] > 5

    ordered = [c for c in COLUMN_ORDER if c in df.columns]
    extra = [c for c in df.columns if c not in ordered]
    return df[ordered + extra]


def summarise(df: pd.DataFrame) -> None:
    print("\n[etl] validation summary")
    print(f"  rows           {len(df):,}")
    print(f"  cities         {df['city'].nunique()}")
    print(f"  date range     {df['observed_at'].min()} -> {df['observed_at'].max()}")
    key = ["city", "observed_at", "temperature_2m"]
    print(f"  key nulls      {int(df[key].isna().sum().sum())}")
    print(f"  aqi present    {df['european_aqi'].notna().mean() * 100:.1f}% of rows")
    print(f"  eaqi range     {df['european_aqi'].min()} -> {df['european_aqi'].max()}")
    print(f"  pm2_5 range    {df['pm2_5'].min():.1f} -> {df['pm2_5'].max():.1f}")
    print(f"  temp range     {df['temperature_2m'].min():.1f} -> {df['temperature_2m'].max():.1f}")
    print("\n  rows per city")
    for city, count in df.groupby("city").size().items():
        print(f"    {city:<12} {count:,}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--end", default=DEFAULT_END)
    args = parser.parse_args()

    df = build(args.start, args.end)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT_DIR / "weather_air_quality.parquet", index=False)
    df.to_csv(OUT_DIR / "weather_air_quality.csv", index=False)
    summarise(df)
    print(f"\n[etl] wrote {OUT_DIR / 'weather_air_quality.parquet'}")
    print(f"[etl] wrote {OUT_DIR / 'weather_air_quality.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
