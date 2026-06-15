"""Load cleaned Parquet into BigQuery (raw.weather_readings).

Design choice for idempotency: the cleaned Parquet in data/processed is the
local source of truth and only grows. Each run reads ALL of it and loads it
with WRITE_TRUNCATE, so the raw table is always a faithful, duplicate-free
mirror of the processed data. Running this twice produces the same table, so
the step is safe to retry (which Airflow may do).

Uses the google-cloud-bigquery client directly. No gcloud CLI is required;
authentication comes from the GOOGLE_APPLICATION_CREDENTIALS key file.
"""

from __future__ import annotations

import glob
import os
import sys
from pathlib import Path

import pandas as pd
from google.cloud import bigquery

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = os.environ.get("PROCESSED_DIR", str(PROJECT_ROOT / "data" / "processed"))

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
DATASET = os.environ.get("BQ_RAW_DATASET", "raw")
TABLE = os.environ.get("BQ_RAW_TABLE", "weather_readings")
LOCATION = os.environ.get("BQ_LOCATION", "US")

# Explicit schema so dbt always sees stable column types.
SCHEMA = [
    bigquery.SchemaField("city", "STRING"),
    bigquery.SchemaField("country", "STRING"),
    bigquery.SchemaField("latitude", "FLOAT"),
    bigquery.SchemaField("longitude", "FLOAT"),
    bigquery.SchemaField("observed_at", "TIMESTAMP"),
    bigquery.SchemaField("temperature_2m", "FLOAT"),
    bigquery.SchemaField("relative_humidity_2m", "INTEGER"),
    bigquery.SchemaField("wind_speed_10m", "FLOAT"),
    bigquery.SchemaField("weather_code", "INTEGER"),
    bigquery.SchemaField("pm10", "FLOAT"),
    bigquery.SchemaField("pm2_5", "FLOAT"),
    bigquery.SchemaField("european_aqi", "INTEGER"),
    bigquery.SchemaField("ozone", "FLOAT"),
    bigquery.SchemaField("aqi_category", "STRING"),
    bigquery.SchemaField("ingested_at", "TIMESTAMP"),
]
COLUMN_ORDER = [field.name for field in SCHEMA]


def read_processed() -> pd.DataFrame:
    """Read every Parquet part file in the processed directory into one frame."""
    files = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.parquet")))
    if not files:
        return pd.DataFrame(columns=COLUMN_ORDER)
    frames = [pd.read_parquet(path) for path in files]
    data = pd.concat(frames, ignore_index=True)
    # Normalise timestamps to UTC so BigQuery stores them unambiguously.
    for column in ("observed_at", "ingested_at"):
        data[column] = pd.to_datetime(data[column], utc=True)
    return data[COLUMN_ORDER]


def main() -> int:
    if not PROJECT_ID or PROJECT_ID == "REPLACE_WITH_YOUR_PROJECT_ID":
        print(
            "[load] ERROR GCP_PROJECT_ID is not set. Source config/settings.env "
            "after filling in your project ID.",
            file=sys.stderr,
        )
        return 1

    data = read_processed()
    if data.empty:
        print("[load] no processed Parquet found yet, nothing to load")
        return 0

    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)

    # Create the raw dataset if it does not exist (BigQuery Data Editor allows this).
    dataset_ref = bigquery.Dataset(f"{PROJECT_ID}.{DATASET}")
    dataset_ref.location = LOCATION
    client.create_dataset(dataset_ref, exists_ok=True)

    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"
    job_config = bigquery.LoadJobConfig(
        schema=SCHEMA,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    job = client.load_table_from_dataframe(data, table_id, job_config=job_config)
    job.result()  # wait for completion

    table = client.get_table(table_id)
    print(f"[load] loaded {table.num_rows} rows into {table_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
