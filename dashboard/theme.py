from __future__ import annotations

ORANGE = "#F39200"
ORANGE_DARK = "#E64415"
INK = "#1A1A1A"
GRAY = "#555555"
FAINT = "#FAF6F4"
RULE = "#E3E3E3"
WHITE = "#FFFFFF"

AQI_ORDER = ["Good", "Fair", "Moderate", "Poor", "Very poor", "Extremely poor", "Unknown"]

AQI_COLORS = {
    "Good": "#50F0E6",
    "Fair": "#50CCAA",
    "Moderate": "#F0E641",
    "Poor": "#FF5050",
    "Very poor": "#960032",
    "Extremely poor": "#7D2181",
    "Unknown": "#BBBBBB",
}

UNHEALTHY_BANDS = ["Poor", "Very poor", "Extremely poor"]

SEQUENTIAL = "YlOrRd"

METRICS = {
    "European AQI": "european_aqi",
    "PM2.5": "pm2_5",
    "PM10": "pm10",
    "Ozone (O3)": "ozone",
    "Nitrogen dioxide (NO2)": "nitrogen_dioxide",
}

UNITS = {
    "european_aqi": "index",
    "pm2_5": "ug/m3",
    "pm10": "ug/m3",
    "ozone": "ug/m3",
    "nitrogen_dioxide": "ug/m3",
}

WHO_PM25_24H = 15
WHO_PM25_ANNUAL = 5

PLOTLY_FONT = "Arial, Helvetica, sans-serif"

CSS = """
<style>
  .stApp { background-color: #FFFFFF; }
  section.main > div { padding-top: 1rem; }
  h1, h2, h3, h4 { color: #1A1A1A; font-family: Arial, Helvetica, sans-serif; }
  .srh-title { font-size: 2.0rem; font-weight: 800; color: #1A1A1A; line-height: 1.1; }
  .srh-accent { color: #F39200; }
  .srh-sub { color: #555555; font-size: 1.0rem; margin-top: 0.15rem; }
  .srh-rule { height: 4px; width: 90px; background: #F39200; border: 0; margin: 0.5rem 0 0.25rem 0; }
  div[data-testid="stMetric"] {
      background: #FAF6F4; border-radius: 10px; padding: 14px 16px;
      border-top: 4px solid #F39200;
  }
  div[data-testid="stMetricValue"] { color: #1A1A1A; font-weight: 800; }
  div[data-testid="stMetricLabel"] { color: #555555; }
  .stTabs [data-baseweb="tab-list"] { gap: 6px; }
  .stTabs [aria-selected="true"] { color: #F39200; font-weight: 700; }
  .srh-note {
      background: #FAF6F4; border-left: 4px solid #F39200; padding: 10px 14px;
      border-radius: 6px; color: #1A1A1A; font-size: 0.92rem;
  }
</style>
"""


def style_fig(fig, height=420, legend_title=None):
    fig.update_layout(
        template="plotly_white",
        font=dict(family=PLOTLY_FONT, size=13, color=INK),
        height=height,
        margin=dict(l=10, r=10, t=40, b=10),
        title_text=None,
        legend=dict(title_text=legend_title, bgcolor="rgba(0,0,0,0)"),
        colorway=[ORANGE, ORANGE_DARK, "#7D2181", "#2E86AB", "#3CB44B",
                  "#555555", "#960032", "#F0A202", "#1B998B", "#8E7DBE"],
    )
    return fig
