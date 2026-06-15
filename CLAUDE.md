# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this project is

Final project for "Data Management 2: Data Curation and Data Management" (SRH
Fernhochschule, The Mobile University). An end-to-end, automated data pipeline:
real-time weather + air quality (Open-Meteo) plus a static city reference, cleaned
with Spark, loaded into BigQuery, transformed with dbt, and scheduled with Airflow.
Individual project, 80% of the grade.

## Hard rules (do not break)

- **No em dashes anywhere.** Not in slides, docs, code comments, or prose. Use
  commas, colons, or parentheses. Hyphens in compound words ("real-time") are fine.
- **Visual deliverables match the SRH Mobile University brand:** SRH orange
  (~#F39200) as the single dominant accent, clean white / charcoal base, Arial,
  corporate minimalist. Reference: https://www.mobile-university.de/ . If the user
  gives a sample file, match that file instead.
- **Python 3.11 only** (via uv). Never 3.13: PySpark does not support it.
- **No Docker, no gcloud.** Use the google-cloud-bigquery Python client only.
- Favour reliability over flashiness. The user has not attended the classes, so
  explain things clearly.

## Architecture and data flow

```
config/cities.json -> producer.py -> data/landing/*.json   (real-time stream)
  -> spark_clean.py (Spark Structured Streaming) -> data/processed/*.parquet
  -> load_bigquery.py (WRITE_TRUNCATE) -> BigQuery raw.weather_readings
  -> dbt (seed cities.csv + staging + marts + tests)
Orchestrated by the Airflow DAG "weather_pipeline" every 5 minutes.
```

## Two isolated environments (already created)

- `.venv-pipeline`: pyspark 3.5, dbt-bigquery, google-cloud-bigquery, pandas,
  pyarrow, requests. Used by producer, Spark, load, and dbt.
- `airflow/.venv-airflow`: apache-airflow 2.10.5 (installed with the official
  constraints file). Airflow tasks shell into `.venv-pipeline`.

## Configuration

`config/settings.env` holds all settings (project root, GCP project ID, dataset
location, dataset/table names, key path, JAVA_HOME, data paths). Every script and
the Airflow DAG source this file. The service account key lives at
`config/dbt-sa-key.json` (gitignored, the user provides it).

## Common commands

Always `source config/settings.env` first.

```bash
# Full pipeline (cron fallback, runs every step in order)
./scripts/run_pipeline.sh

# Individual steps
./.venv-pipeline/bin/python scripts/producer.py
./.venv-pipeline/bin/python scripts/spark_clean.py
./.venv-pipeline/bin/python scripts/load_bigquery.py
cd dbt/weather && ../../.venv-pipeline/bin/dbt run  --profiles-dir .
cd dbt/weather && ../../.venv-pipeline/bin/dbt test --profiles-dir .

# Airflow (primary automation)
export AIRFLOW_HOME="$PROJECT_ROOT/airflow"
source "$AIRFLOW_HOME/.venv-airflow/bin/activate" && airflow standalone

# Rebuild the presentation
uv run --with python-pptx python presentation/build_pptx.py
```

## Conventions

- dbt: staging models are views, marts are tables. Dedupe authoritatively in
  `stg_weather` (cross-run); Spark only dedupes within a batch.
- Surrogate keys are built inline (`to_hex(md5(...))`), so no dbt_utils dependency.
- Source `config/settings.env` before running anything that touches BigQuery.
- After editing the deck, always re-render to images and visually QA before
  declaring it done (LibreOffice + pdftoppm are installed).

## Project-specific skills

- `run-weather-pipeline`: run or troubleshoot the pipeline end to end or per step.
- `weather-pipeline-deck`: build or edit the branded presentation.

## Current state

Built and verified locally: producer (live), Spark clean, dbt parse, Airflow DAG
import, the 14-slide branded deck. Blocked on the user: GCP project ID + service
account key (needed to actually run load + dbt), and the student name +
matriculation number for the slide title.
