from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

DATA_FILE = Path(__file__).resolve().parent / "data" / "weather_air_quality.parquet"

PLOT_FLOAT_COLS = ["european_aqi", "pm2_5", "pm10", "ozone", "nitrogen_dioxide"]


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    df = pd.read_parquet(DATA_FILE)
    df["observed_at"] = pd.to_datetime(df["observed_at"], utc=True)
    df["day"] = df["observed_at"].dt.tz_localize(None).dt.normalize()
    for column in PLOT_FLOAT_COLS:
        df[column] = df[column].astype("float64")
    return df


@st.cache_data(show_spinner=False)
def month_order(df: pd.DataFrame) -> list[str]:
    order = (
        df.groupby("month_name")["observed_at"].min().sort_values().index.tolist()
    )
    return order


def apply_filters(df, cities, start_day, end_day) -> pd.DataFrame:
    mask = (
        df["city"].isin(cities)
        & (df["day"] >= pd.Timestamp(start_day))
        & (df["day"] <= pd.Timestamp(end_day))
    )
    return df.loc[mask]


def per_city(df, metric) -> pd.DataFrame:
    agg = (
        df.groupby(["city", "country_name", "latitude", "longitude", "population"])
        .agg(value=(metric, "mean"), readings=(metric, "size"))
        .reset_index()
    )
    agg["value"] = agg["value"].round(1)
    return agg.sort_values("value", ascending=False)


def daily_series(df, metric) -> pd.DataFrame:
    series = (
        df.groupby(["day", "city"])[metric].mean().reset_index().rename(columns={metric: "value"})
    )
    return series


def hour_month_matrix(df, metric, months) -> pd.DataFrame:
    pivot = (
        df.pivot_table(index="hour", columns="month_name", values=metric, aggfunc="mean")
        .reindex(columns=months)
    )
    return pivot.round(1)


def category_mix(df) -> pd.DataFrame:
    counts = (
        df.groupby(["city", "aqi_category"]).size().reset_index(name="hours")
    )
    totals = counts.groupby("city")["hours"].transform("sum")
    counts["share"] = (counts["hours"] / totals * 100).round(1)
    return counts


def exposure(df) -> pd.DataFrame:
    grouped = df.groupby(["city", "population"]).agg(
        total_hours=("pm2_5", "size"),
        unhealthy_hours=("pm25_exceeds_who_24h", "sum"),
    ).reset_index()
    grouped["exceedance_pct"] = (
        grouped["unhealthy_hours"] / grouped["total_hours"] * 100
    ).round(1)
    grouped["exposure_index"] = (
        grouped["population"] * grouped["unhealthy_hours"] / grouped["total_hours"] / 1000
    ).round(0)
    return grouped.sort_values("exposure_index", ascending=False)
