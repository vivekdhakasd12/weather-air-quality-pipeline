from __future__ import annotations

from pathlib import Path

import streamlit as st

import charts
import data as dataio
import theme

HERE = Path(__file__).resolve().parent
LOGO = str(HERE / "assets" / "srh_logo.jpg")

st.set_page_config(
    page_title="European Air Quality and Public Health",
    page_icon="🌍",
    layout="wide",
)
st.markdown(theme.CSS, unsafe_allow_html=True)

df = dataio.load_data()
months = dataio.month_order(df)

col_logo, col_title = st.columns([1, 9], vertical_alignment="center")
with col_logo:
    st.image(LOGO, width=78)
with col_title:
    st.markdown(
        "<div class='srh-title'>European Air Quality <span class='srh-accent'>and "
        "Public Health</span></div>"
        "<div class='srh-sub'>Hourly weather and air quality across ten European "
        "cities, June 2025 to May 2026</div>"
        "<hr class='srh-rule'>",
        unsafe_allow_html=True,
    )

st.sidebar.image(LOGO, width=120)
st.sidebar.markdown("### Filters")

countries = sorted(df["country_name"].unique())
sel_countries = st.sidebar.multiselect("Country", countries, default=countries)
avail_cities = sorted(df.loc[df["country_name"].isin(sel_countries), "city"].unique())
sel_cities = st.sidebar.multiselect("City", avail_cities, default=avail_cities)

metric_label = st.sidebar.selectbox("Pollutant metric", list(theme.METRICS), index=0)
metric = theme.METRICS[metric_label]

min_day = df["day"].min().date()
max_day = df["day"].max().date()
date_range = st.sidebar.date_input(
    "Date range", value=(min_day, max_day), min_value=min_day, max_value=max_day,
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_day, end_day = date_range
else:
    start_day, end_day = min_day, max_day

if not sel_cities:
    st.warning("Select at least one city in the sidebar to see the dashboard.")
    st.stop()

fdf = dataio.apply_filters(df, sel_cities, start_day, end_day)
if fdf.empty:
    st.warning("No readings match the current filters. Widen the date range or city selection.")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.download_button(
    "Download filtered data (CSV)",
    data=fdf.to_csv(index=False).encode("utf-8"),
    file_name="weather_air_quality_filtered.csv",
    mime="text/csv",
)
st.sidebar.caption(
    f"{len(fdf):,} hourly readings  |  {fdf['city'].nunique()} cities  |  "
    "Source: Open-Meteo archive (CAMS Europe). WHO 2021 PM2.5 guidelines: "
    "5 ug/m3 annual, 15 ug/m3 daily."
)

city_eaqi = dataio.per_city(fdf, "european_aqi")
avg_eaqi = float(fdf["european_aqi"].mean())
pct_unhealthy = fdf["aqi_category"].isin(theme.UNHEALTHY_BANDS).mean() * 100
who_hours = int(fdf["pm25_exceeds_who_24h"].sum())
worst = city_eaqi.iloc[0]
cleanest = city_eaqi.iloc[-1]

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Average European AQI", f"{avg_eaqi:.1f}")
k2.metric("Share of hours unhealthy", f"{pct_unhealthy:.1f}%")
k3.metric("Worst city (avg AQI)", worst["city"], f"{worst['value']:.0f}")
k4.metric("Cleanest city (avg AQI)", cleanest["city"], f"{cleanest['value']:.0f}",
          delta_color="inverse")
k5.metric("Hours over WHO limit", f"{who_hours:,}")

tabs = st.tabs([
    "Overview", "Where", "When", "Who is worst", "Health lens", "Weather vs pollution",
])

with tabs[0]:
    c1, c2 = st.columns([1.1, 1.4], vertical_alignment="center")
    with c1:
        st.plotly_chart(charts.gauge_eaqi(avg_eaqi), use_container_width=True)
    with c2:
        st.markdown(
            f"<div class='srh-note'><b>The story in one paragraph.</b> Across the "
            f"selected cities and dates, the average European AQI is "
            f"<b>{avg_eaqi:.1f}</b>. Air is rated Poor or worse for "
            f"<b>{pct_unhealthy:.1f}%</b> of hours. <b>{worst['city']}</b> carries the "
            f"heaviest air pollution burden (avg AQI {worst['value']:.0f}), while "
            f"<b>{cleanest['city']}</b> is the cleanest (avg AQI {cleanest['value']:.0f}). "
            f"PM2.5 exceeded the WHO daily guideline of 15 ug/m3 in "
            f"<b>{who_hours:,}</b> city-hours.</div>",
            unsafe_allow_html=True,
        )
        st.caption(
            "The gauge bands follow the official European Air Quality Index scale "
            "(Good, Fair, Moderate, Poor, Very poor, Extremely poor)."
        )

with tabs[1]:
    st.subheader(f"Where is the air worst? Average {metric_label} by city")
    agg = dataio.per_city(fdf, metric)
    st.plotly_chart(charts.city_map(agg, metric_label), use_container_width=True)
    st.caption("Bubble size shows city population, colour shows the average pollutant level.")

with tabs[2]:
    st.subheader(f"When does pollution peak? {metric_label} over time")
    st.plotly_chart(
        charts.daily_lines(dataio.daily_series(fdf, metric), metric_label),
        use_container_width=True,
    )
    st.subheader("Daily and seasonal rhythm")
    matrix = dataio.hour_month_matrix(fdf, metric, months)
    st.plotly_chart(charts.hour_month_heatmap(matrix, metric_label), use_container_width=True)
    st.caption("Each cell is the average across the selected cities for that hour and month.")

with tabs[3]:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader(f"Ranked: average {metric_label}")
        st.plotly_chart(
            charts.ranked_bar(dataio.per_city(fdf, metric), metric_label),
            use_container_width=True,
        )
    with c2:
        st.subheader("Air quality band mix per city")
        st.plotly_chart(charts.category_stack(dataio.category_mix(fdf)), use_container_width=True)
        st.caption("Share of hours each city spends in each European AQI band.")

with tabs[4]:
    exp = dataio.exposure(fdf)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Hours above the WHO PM2.5 daily limit")
        st.plotly_chart(charts.exceedance_bar(exp), use_container_width=True)
    with c2:
        st.subheader("Population-weighted exposure")
        st.plotly_chart(charts.exposure_bar(exp), use_container_width=True)
    st.markdown(
        "<div class='srh-note'>The <b>exposure index</b> combines how often a city "
        "breaches the WHO PM2.5 daily guideline with how many people live there "
        "(population x exceedance share). It surfaces where poor air affects the most "
        "people, not just where concentrations are highest.</div>",
        unsafe_allow_html=True,
    )

with tabs[5]:
    st.subheader("Does weather drive pollution? Wind speed vs PM2.5")
    daily = (
        fdf.groupby(["day", "city"]).agg(
            wind=("wind_speed_10m", "mean"), pm25=("pm2_5", "mean")
        ).dropna()
    )
    corr = daily["wind"].corr(daily["pm25"]) if len(daily) > 2 else float("nan")
    st.plotly_chart(charts.wind_vs_pm25(fdf), use_container_width=True)
    st.markdown(
        f"<div class='srh-note'>Each point is one city-day. The correlation between "
        f"daily mean wind speed and daily mean PM2.5 is <b>{corr:.2f}</b>. A negative "
        f"value supports the expectation that calm, still conditions let particulate "
        f"matter accumulate, while wind disperses it.</div>",
        unsafe_allow_html=True,
    )
