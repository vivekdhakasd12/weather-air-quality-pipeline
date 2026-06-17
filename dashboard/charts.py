from __future__ import annotations

import numpy as np
import plotly.express as px
import plotly.graph_objects as go

import theme


def gauge_eaqi(value: float) -> go.Figure:
    steps = [
        {"range": [0, 20], "color": theme.AQI_COLORS["Good"]},
        {"range": [20, 40], "color": theme.AQI_COLORS["Fair"]},
        {"range": [40, 60], "color": theme.AQI_COLORS["Moderate"]},
        {"range": [60, 80], "color": theme.AQI_COLORS["Poor"]},
        {"range": [80, 100], "color": theme.AQI_COLORS["Very poor"]},
        {"range": [100, 140], "color": theme.AQI_COLORS["Extremely poor"]},
    ]
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(value, 1),
        number={"font": {"size": 40, "color": theme.INK}},
        gauge={
            "axis": {"range": [0, 140], "tickwidth": 1},
            "bar": {"color": theme.INK, "thickness": 0.18},
            "steps": steps,
        },
        title={"text": "Average European AQI", "font": {"size": 15, "color": theme.GRAY}},
    ))
    return theme.style_fig(fig, height=300)


def city_map(agg, metric_label: str) -> go.Figure:
    fig = px.scatter_geo(
        agg,
        lat="latitude",
        lon="longitude",
        color="value",
        size="population",
        size_max=42,
        hover_name="city",
        custom_data=["country_name", "value", "population"],
        color_continuous_scale=theme.SEQUENTIAL,
        scope="europe",
    )
    fig.update_traces(hovertemplate=(
        "<b>%{hovertext}</b><br>%{customdata[0]}<br>"
        + metric_label + ": %{customdata[1]}<br>"
        "Population: %{customdata[2]:,.0f}<extra></extra>"
    ))
    fig.update_geos(
        showcountries=True, countrycolor=theme.RULE,
        showland=True, landcolor="#F7F7F7",
        showocean=True, oceancolor="#FFFFFF",
        lataxis_range=[35, 60], lonaxis_range=[-12, 26],
    )
    fig.update_layout(coloraxis_colorbar=dict(title=metric_label))
    return theme.style_fig(fig, height=480)


def daily_lines(series, metric_label: str) -> go.Figure:
    fig = px.line(series, x="day", y="value", color="city")
    fig.update_traces(line=dict(width=1.4))
    fig.update_layout(
        xaxis_title=None,
        yaxis_title=metric_label,
        hovermode="x unified",
    )
    return theme.style_fig(fig, height=420, legend_title="City")


def hour_month_heatmap(matrix, metric_label: str) -> go.Figure:
    fig = px.imshow(
        matrix,
        labels=dict(x="Month", y="Hour of day", color=metric_label),
        color_continuous_scale=theme.SEQUENTIAL,
        aspect="auto",
        origin="lower",
    )
    fig.update_layout(yaxis=dict(dtick=3))
    return theme.style_fig(fig, height=440)


def ranked_bar(agg, metric_label: str) -> go.Figure:
    data = agg.sort_values("value")
    fig = px.bar(
        data, x="value", y="city", orientation="h",
        color="value", color_continuous_scale=theme.SEQUENTIAL,
        text="value",
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(
        xaxis_title=metric_label, yaxis_title=None, coloraxis_showscale=False,
    )
    return theme.style_fig(fig, height=440)


def category_stack(mix) -> go.Figure:
    fig = px.bar(
        mix, x="share", y="city", color="aqi_category", orientation="h",
        category_orders={"aqi_category": theme.AQI_ORDER},
        color_discrete_map=theme.AQI_COLORS,
        custom_data=["aqi_category", "hours"],
    )
    fig.update_traces(hovertemplate=(
        "<b>%{y}</b><br>%{customdata[0]}: %{x}% of hours"
        "<br>(%{customdata[1]:,} hours)<extra></extra>"
    ))
    fig.update_layout(
        barmode="stack", xaxis_title="Share of hours (%)", yaxis_title=None,
        legend_title="AQI band", xaxis=dict(range=[0, 100]),
    )
    return theme.style_fig(fig, height=440, legend_title="AQI band")


def exposure_bar(exp) -> go.Figure:
    data = exp.sort_values("exposure_index")
    fig = px.bar(
        data, x="exposure_index", y="city", orientation="h",
        color="exposure_index", color_continuous_scale=theme.SEQUENTIAL,
        custom_data=["population", "exceedance_pct"],
        text="exposure_index",
    )
    fig.update_traces(
        textposition="outside", cliponaxis=False,
        hovertemplate=(
            "<b>%{y}</b><br>Exposure index: %{x:,.0f}"
            "<br>Population: %{customdata[0]:,.0f}"
            "<br>Hours over WHO 24h limit: %{customdata[1]}%<extra></extra>"
        ),
    )
    fig.update_layout(
        xaxis_title="Exposure index (population x exceedance share, thousands)",
        yaxis_title=None, coloraxis_showscale=False,
    )
    return theme.style_fig(fig, height=440)


def exceedance_bar(exp) -> go.Figure:
    data = exp.sort_values("exceedance_pct")
    fig = px.bar(
        data, x="exceedance_pct", y="city", orientation="h",
        color="exceedance_pct", color_continuous_scale=theme.SEQUENTIAL,
        text="exceedance_pct",
    )
    fig.update_traces(
        texttemplate="%{text}%", textposition="outside", cliponaxis=False,
    )
    fig.update_layout(
        xaxis_title="Share of hours above WHO PM2.5 24h guideline (%)",
        yaxis_title=None, coloraxis_showscale=False,
    )
    return theme.style_fig(fig, height=440)


def wind_vs_pm25(df) -> go.Figure:
    daily = (
        df.groupby(["day", "city"])
        .agg(wind=("wind_speed_10m", "mean"), pm25=("pm2_5", "mean"))
        .reset_index()
        .dropna(subset=["wind", "pm25"])
    )
    fig = px.scatter(
        daily, x="wind", y="pm25", color="city", opacity=0.55,
        labels={"wind": "Daily mean wind speed (km/h)", "pm25": "Daily mean PM2.5 (ug/m3)"},
    )
    fig.update_traces(marker=dict(size=6))
    if len(daily) > 2:
        coef = np.polyfit(daily["wind"], daily["pm25"], 1)
        line_x = np.linspace(daily["wind"].min(), daily["wind"].max(), 50)
        line_y = np.polyval(coef, line_x)
        fig.add_trace(go.Scatter(
            x=line_x, y=line_y, mode="lines", name="Trend",
            line=dict(color=theme.INK, width=3, dash="dash"),
        ))
    fig.update_layout(xaxis_title="Daily mean wind speed (km/h)", yaxis_title="Daily mean PM2.5 (ug/m3)")
    return theme.style_fig(fig, height=460, legend_title="City")
