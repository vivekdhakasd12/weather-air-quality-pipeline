#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

source "$ROOT/config/settings.env"

PY="$ROOT/.venv-pipeline/bin/python"
DBT="$ROOT/.venv-pipeline/bin/dbt"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"; }

log "1/6 ingest";        "$PY" "$ROOT/scripts/producer.py"
log "2/6 spark_clean";   "$PY" "$ROOT/scripts/spark_clean.py"
log "3/6 load_bigquery"; "$PY" "$ROOT/scripts/load_bigquery.py"
log "4/6 dbt seed";      ( cd "$ROOT/dbt/weather" && "$DBT" seed --profiles-dir . )
log "5/6 dbt run";       ( cd "$ROOT/dbt/weather" && "$DBT" run  --profiles-dir . )
log "6/6 dbt test";      ( cd "$ROOT/dbt/weather" && "$DBT" test --profiles-dir . )
log "pipeline complete"
