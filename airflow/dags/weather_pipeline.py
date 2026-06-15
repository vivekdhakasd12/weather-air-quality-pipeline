"""Airflow DAG: weather_pipeline.

Runs the whole chain every 5 minutes:

    ingest -> spark_clean -> load_bigquery -> dbt_run -> dbt_test

Each task is a BashOperator that sources config/settings.env and then shells
into the isolated .venv-pipeline interpreter. Airflow itself lives in its own
.venv-airflow, so Airflow's dependencies never collide with PySpark / dbt.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

# Absolute path because Airflow may run from anywhere. settings.env exports
# PROJECT_ROOT, which every command below then reuses.
SETTINGS = "/Users/dev/Agentic Workflows /dm2-weather-pipeline/config/settings.env"


def step(command: str) -> str:
    """Wrap a command so it fails fast and has the project env loaded."""
    return f'set -euo pipefail\nsource "{SETTINGS}"\n{command}'


default_args = {
    "owner": "dm2",
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    dag_id="weather_pipeline",
    description="Weather + air quality: ingest, Spark clean, load BigQuery, dbt.",
    default_args=default_args,
    schedule="*/5 * * * *",  # every 5 minutes
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,  # never let two runs overlap
    tags=["dm2", "weather", "bigquery", "spark", "dbt"],
) as dag:

    ingest = BashOperator(
        task_id="ingest",
        bash_command=step('"$PROJECT_ROOT/.venv-pipeline/bin/python" "$PROJECT_ROOT/scripts/producer.py"'),
    )

    spark_clean = BashOperator(
        task_id="spark_clean",
        bash_command=step('"$PROJECT_ROOT/.venv-pipeline/bin/python" "$PROJECT_ROOT/scripts/spark_clean.py"'),
    )

    load_bigquery = BashOperator(
        task_id="load_bigquery",
        bash_command=step('"$PROJECT_ROOT/.venv-pipeline/bin/python" "$PROJECT_ROOT/scripts/load_bigquery.py"'),
    )

    dbt_seed = BashOperator(
        task_id="dbt_seed",
        bash_command=step('cd "$PROJECT_ROOT/dbt/weather" && "$PROJECT_ROOT/.venv-pipeline/bin/dbt" seed --profiles-dir .'),
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=step('cd "$PROJECT_ROOT/dbt/weather" && "$PROJECT_ROOT/.venv-pipeline/bin/dbt" run --profiles-dir .'),
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=step('cd "$PROJECT_ROOT/dbt/weather" && "$PROJECT_ROOT/.venv-pipeline/bin/dbt" test --profiles-dir .'),
    )

    ingest >> spark_clean >> load_bigquery >> dbt_seed >> dbt_run >> dbt_test
