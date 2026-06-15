---
name: run-weather-pipeline
description: Run, test, or troubleshoot the weather + air quality data pipeline (producer, Spark cleaning, BigQuery load, dbt run/test, Airflow). Use when the user wants to run the pipeline, ingest data, refresh BigQuery, run dbt, start Airflow, or debug any pipeline step.
---

# Run the weather pipeline

The pipeline: `producer.py` -> `data/landing/*.json` -> `spark_clean.py` ->
`data/processed/*.parquet` -> `load_bigquery.py` -> `raw.weather_readings` -> dbt
(seed + staging + marts + tests). Orchestrated by the Airflow DAG
`weather_pipeline` every 5 minutes.

## Before anything

Always load settings first (the path contains a space, so keep it quoted):

```bash
cd "/Users/dev/Agentic Workflows /dm2-weather-pipeline"
source config/settings.env
```

The BigQuery steps need `GCP_PROJECT_ID` set in `config/settings.env` and the key
at `config/dbt-sa-key.json`. The producer and Spark steps work without GCP.

## Run everything

```bash
./scripts/run_pipeline.sh
```

This runs ingest, Spark clean, BigQuery load, `dbt run`, `dbt test` in order with
`set -euo pipefail`. It is also the cron fallback for automation.

## Run one step at a time

```bash
./.venv-pipeline/bin/python scripts/producer.py        # extract -> data/landing
./.venv-pipeline/bin/python scripts/spark_clean.py     # clean   -> data/processed
./.venv-pipeline/bin/python scripts/load_bigquery.py   # load    -> raw.weather_readings
cd dbt/weather && ../../.venv-pipeline/bin/dbt run  --profiles-dir .
cd dbt/weather && ../../.venv-pipeline/bin/dbt test --profiles-dir .
```

## Airflow (primary automation)

```bash
export AIRFLOW_HOME="/Users/dev/Agentic Workflows /dm2-weather-pipeline/airflow"
source "$AIRFLOW_HOME/.venv-airflow/bin/activate"
airflow standalone     # UI at http://localhost:8080, password in airflow/standalone_admin_password.txt
```

Enable the `weather_pipeline` DAG in the UI. To validate the DAG without starting
the scheduler:

```bash
./airflow/.venv-airflow/bin/python -c "from airflow.models import DagBag; \
db=DagBag('airflow/dags', include_examples=False); print(db.import_errors or 'no errors')"
```

## Inspect local output

```bash
./.venv-pipeline/bin/python -c "import pandas as pd, glob; \
print(pd.concat([pd.read_parquet(f) for f in glob.glob('data/processed/*.parquet')]).head())"
```

## Troubleshooting

- **`GCP_PROJECT_ID is not set`**: fill it into `config/settings.env`, then re-source.
- **Spark timestamps look shifted**: the session timezone is pinned to UTC in
  `spark_clean.py`; do not remove that config (Open-Meteo returns naive UTC strings).
- **Spark reprocesses nothing**: it only reads new landing files (checkpoint in
  `data/checkpoints/spark`). To reprocess from scratch, delete `data/processed/*`
  and `data/checkpoints/spark`, then rerun. Hourly readings polled twice in one
  hour share `observed_at` and are deduped (in Spark per batch, in dbt globally).
- **Java errors**: `JAVA_HOME` (Java 11) is set in `config/settings.env`.
- **dbt cannot connect**: check `config/dbt-sa-key.json` exists and `BQ_LOCATION`
  matches the dataset location. The load and dbt must use the same location.
- Never use Python 3.13 here. PySpark needs 3.11 (the venvs already pin it).
