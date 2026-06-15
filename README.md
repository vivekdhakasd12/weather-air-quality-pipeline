# DM2 Final Project: Weather + Air Quality Data Pipeline

An end-to-end data pipeline that ingests real-time weather and air quality data,
cleans it with Apache Spark, loads it into Google BigQuery, transforms it with
dbt, and runs automatically on a 5 minute schedule with Apache Airflow.

Module: Data Management 2 (Data Curation and Data Management), SRH.

## Exam requirement coverage

| # | Requirement | How this project meets it |
|---|-------------|---------------------------|
| 1 | At least 2 data sources, one real-time | Open-Meteo weather + air quality APIs (real-time, polled every 5 min) and a static city reference CSV loaded as a dbt seed |
| 2 | Extract, clean, load into BigQuery | `producer.py` extracts, Spark cleans, `load_bigquery.py` loads `raw.weather_readings` |
| 3 | Transformation with dbt | seed + staging + marts (ELT, all SQL in BigQuery) with data-quality tests |
| 4 | Include Spark | Spark Structured Streaming cleaning job (`spark_clean.py`) |
| 5 | Pipeline runs automatically | Airflow DAG `weather_pipeline`, schedule `*/5 * * * *` (cron fallback: `scripts/run_pipeline.sh`) |
| 6 | Presentation | `presentation/` builds the PPTX deck |

## Architecture

```
config/cities.json
       |
       v
producer.py  --->  data/landing/*.json          (real-time stream, one file per 5-min poll)
       |
       v
spark_clean.py (Spark Structured Streaming, Trigger.AvailableNow)
   flatten, cast, parse timestamps, drop nulls, dedupe, derive aqi_category
       |
       v
data/processed/*.parquet
       |
       v
load_bigquery.py  --->  BigQuery  raw.weather_readings   (WRITE_TRUNCATE, idempotent)
                                       |
                                       v
                              dbt (seed cities.csv)
                              staging: stg_weather, stg_cities
                              marts:   fct_weather_readings,
                                       agg_weather_by_city,
                                       agg_air_quality_by_country
                              + tests: not_null, unique, accepted_values, relationships

Orchestration: Airflow DAG  ingest -> spark_clean -> load_bigquery -> dbt_run -> dbt_test
```

## Two isolated environments

To avoid dependency conflicts the project uses two Python 3.11 virtual envs:

- `.venv-pipeline` : pyspark 3.5, dbt-bigquery, google-cloud-bigquery, pandas, pyarrow, requests
- `airflow/.venv-airflow` : apache-airflow 2.10.5 (installed with the official constraints file)

Airflow tasks shell into `.venv-pipeline`, so Airflow's own dependencies never
collide with Spark and dbt.

## One-time setup

1. Google Cloud: create a project, enable the BigQuery API, create a dataset
   named `raw`, create a service account `dbt` with roles **BigQuery Job User**
   and **BigQuery Data Editor**, download its JSON key to
   `config/dbt-sa-key.json`.
2. Edit `config/settings.env`: set `GCP_PROJECT_ID` and confirm `BQ_LOCATION`
   matches the dataset location you chose (US or EU).

The two virtual environments are already created. To rebuild them from scratch:

```bash
uv venv --python 3.11 .venv-pipeline
uv pip install --python .venv-pipeline "pyspark==3.5.*" dbt-bigquery google-cloud-bigquery pandas pyarrow requests

uv venv --python 3.11 airflow/.venv-airflow
uv pip install --python airflow/.venv-airflow "apache-airflow==2.10.5" \
  --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.5/constraints-3.11.txt"
```

## Run the whole pipeline once (standalone)

```bash
./scripts/run_pipeline.sh
```

This sources `config/settings.env` and runs ingest, Spark clean, BigQuery load,
dbt run, dbt test in order. This is also the cron fallback for automation:

```cron
*/5 * * * * "/Users/dev/Agentic Workflows /dm2-weather-pipeline/scripts/run_pipeline.sh" >> /tmp/weather_pipeline.log 2>&1
```

## Run with Airflow (the primary automation)

```bash
export AIRFLOW_HOME="/Users/dev/Agentic Workflows /dm2-weather-pipeline/airflow"
source "$AIRFLOW_HOME/.venv-airflow/bin/activate"
airflow standalone
```

Then open http://localhost:8080 , log in with the credentials Airflow prints,
enable the `weather_pipeline` DAG, and it runs every 5 minutes. The login
password is written to `airflow/standalone_admin_password.txt`.

## Run individual steps

```bash
source config/settings.env
./.venv-pipeline/bin/python scripts/producer.py        # extract -> data/landing
./.venv-pipeline/bin/python scripts/spark_clean.py     # clean   -> data/processed
./.venv-pipeline/bin/python scripts/load_bigquery.py   # load    -> raw.weather_readings
cd dbt/weather && ../../.venv-pipeline/bin/dbt run  --profiles-dir .
cd dbt/weather && ../../.venv-pipeline/bin/dbt test --profiles-dir .
```

## Repository layout

```
config/        settings.env, cities.json, dbt-sa-key.json (you add this, gitignored)
scripts/       producer.py, spark_clean.py, load_bigquery.py, run_pipeline.sh
dbt/weather/   dbt_project.yml, profiles.yml, seeds/, models/staging/, models/marts/
airflow/       dags/weather_pipeline.py, .venv-airflow/
data/          landing/ (json), processed/ (parquet), checkpoints/ (spark state)
presentation/  build_pptx.py and the generated deck
```
