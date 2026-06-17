# European Air Quality and Public Health Dashboard

An interactive dashboard built for the Advanced Data Visualization module. It reuses
the DM2 weather pipeline's cities and cleaning rules, and visualizes one year of hourly
weather and air quality (June 2025 to May 2026) for ten European cities.

Built with Streamlit and Plotly. SRH Mobile University branding (orange accent, clean
white and charcoal, Arial).

## Business question

Where, when, and for whom is air quality a public health problem across major European
cities, and how does weather shape it?

## What is inside

```
dashboard/
  app.py            Streamlit app (layout, filters, KPIs, six tabs)
  theme.py          SRH colours, the official European AQI palette, Plotly styling
  data.py           cached data load, filtering, and all aggregations
  charts.py         every Plotly figure builder
  etl/
    fetch_history.py  pulls a year of hourly data and writes the analytics dataset
  data/
    weather_air_quality.parquet   the dataset the app reads (committed)
    weather_air_quality.csv       flat export for Tableau or Power BI (regenerable)
  assets/srh_logo.jpg
```

The six tabs: Overview, Where (Europe bubble map), When (time series plus an hour by
month heatmap), Who is worst (city ranking plus AQI band mix), Health lens (hours over
the WHO PM2.5 limit plus population-weighted exposure), and Weather vs pollution (wind
speed against PM2.5 with a trend line).

## Run it locally

From the project root (the parent of this folder):

```bash
./.venv-pipeline/bin/streamlit run dashboard/app.py
```

Then open http://localhost:8501 . If streamlit or plotly are missing, install them into
the pipeline environment:

```bash
uv pip install --python ./.venv-pipeline/bin/python streamlit plotly
```

## Refresh or change the data

The dataset is built from Open-Meteo's free archive APIs (no API key needed):

```bash
./.venv-pipeline/bin/python dashboard/etl/fetch_history.py
# or a custom window:
./.venv-pipeline/bin/python dashboard/etl/fetch_history.py --start 2024-06-01 --end 2025-05-31
```

This writes both the parquet (used by the app) and the CSV (Tableau or Power BI fallback).

## Deploy to Streamlit Community Cloud (free)

1. Make sure the oversized screen recordings are not pushed. They are already listed in
   `.gitignore` (`presentation/*.mov`); GitHub rejects files over 100 MB.
2. Push this repository to GitHub.
3. Go to https://share.streamlit.io , sign in with GitHub, and click "New app".
4. Pick this repository and branch, and set the main file path to `dashboard/app.py`.
5. Streamlit Cloud installs from the root `requirements.txt` and serves the live URL.

The light theme is pinned in `.streamlit/config.toml`, so the deployed app matches the
SRH branding regardless of the viewer's system theme.

## Data notes

- Source: Open-Meteo Historical Weather API and Air Quality API (CAMS Europe).
- Air quality band colours follow the official European Air Quality Index scale.
- Health thresholds use the WHO 2021 PM2.5 guidelines: 5 ug/m3 annual, 15 ug/m3 daily.
