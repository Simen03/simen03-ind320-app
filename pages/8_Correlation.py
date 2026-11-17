import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from modules.controls import area_label, get_selection
from modules.NVE_API import select_area
from modules.reservoir_data import load_reservoirs
from modules.style import COLORS, LAYOUT, page_header
from modules.weather import WEATHER_VARS, weekly_weather

page_header("Weather and reservoir correlation", "Predictive",
            "Sliding window correlation (SWC) between a weather property and the reservoir data for the selected area. "
            "A lag of *k* weeks compares the reservoir this week with the weather *k* weeks earlier.")

# Global selections: area and time interval (shared with the map and the other pages)
start, end, area_type, number = get_selection()
name = area_label(area_type, number)

# Representative variables from Magasinstatistikk
RESERVOIR_VARS = {
    "change_filling_level": "Weekly change in filling level",
    "filling_level": "Filling level",
}

# ---------- Local controls ----------
with st.container(border=True):
    c1, c2 = st.columns(2)
    prop = c1.selectbox("Weather property", list(WEATHER_VARS),
                        format_func=lambda v: WEATHER_VARS[v][0], key="swc_property")
    res_var = c2.selectbox("Reservoir variable", list(RESERVOIR_VARS),
                           format_func=RESERVOIR_VARS.get, key="swc_reservoir")
    c3, c4 = st.columns(2)
    window = c3.slider("Window length (weeks)", 4, 104, 26,
                       help="Number of weeks in each correlation window. Short windows show quick changes, long windows are more stable.")
    lag = c4.slider("Lag (weeks)", 0, 26, 0,
                    help="How many weeks earlier the weather is compared with the reservoir data.")
label, unit = WEATHER_VARS[prop]

# ---------- Data ----------
# Reservoir data for the selected area (weekly, Sunday dates)
reservoir = select_area(load_reservoirs(start, end), area_type, number)[res_var]

# Weather for the same years, at most the last 10 years to limit the number of API calls
last_year = min(end.year, pd.Timestamp.today().year)
years = range(max(start.year, last_year - 9), last_year + 1)
try:
    weather = weekly_weather(name, years)[prop]
except Exception as e:
    st.error(f"Could not download weather data from open-meteo: {e}")
    st.stop()

# Combine on the common weekly time axis
data = pd.concat([reservoir.rename("reservoir"), weather.rename("weather")], axis=1).dropna()
if len(data) < window + lag + 5:
    st.warning("Too few weeks for this window and lag. Increase the interval in the sidebar or reduce the window.")
    st.stop()

# ---------- Correlations ----------
# Lag: the weather `lag` weeks earlier is placed at the same date as the reservoir value
lagged = data["weather"].shift(lag)
swc = data["reservoir"].rolling(window, center=True).corr(lagged)    # local correlation in each window
overall = data["reservoir"].corr(lagged)                              # one correlation for the whole period

# Correlation over the whole period for every lag, to see where the connection is strongest
lag_corr = pd.Series({k: data["reservoir"].corr(data["weather"].shift(k)) for k in range(27)})
best_lag = int(lag_corr.abs().idxmax())

m1, m2, m3 = st.columns(3)
m1.metric(f"Correlation at lag {lag}", f"{overall:.2f}")
m2.metric("Strongest lag", f"{best_lag} weeks", f"r = {lag_corr[best_lag]:.2f}", delta_color="off")
m3.metric("Weeks in the analysis", len(data))

# ---------- Plot: data and sliding window correlation ----------
# Highlight one window, to show which weeks a single SWC value is based on
centre = st.select_slider("Highlight the window centred at", options=list(data.index),
                          value=data.index[len(data) // 2], format_func=lambda d: f"{d:%d %b %Y}")
half = pd.Timedelta(weeks=window / 2)

fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.07, subplot_titles=(
    f"{RESERVOIR_VARS[res_var]} – {name}",
    f"{label} ({unit}), {lag} weeks earlier",
    f"Sliding window correlation, window {window} weeks",
))
fig.add_scatter(x=data.index, y=data["reservoir"], mode="lines", line=dict(color=COLORS["main"]), row=1, col=1)
fig.add_scatter(x=data.index, y=lagged, mode="lines", line=dict(color=COLORS["secondary"]), row=2, col=1)
fig.add_scatter(x=swc.index, y=swc, mode="lines", line=dict(color=COLORS["main"]), row=3, col=1)
fig.add_hline(y=0, line=dict(color=COLORS["limit"], dash="dot"), row=3, col=1)          # no correlation
fig.add_vrect(x0=centre - half, x1=centre + half, fillcolor=COLORS["outlier"], opacity=0.12,
              line_width=0, row="all", col=1)                                          # the highlighted window
fig.add_scatter(x=[centre], y=[swc.get(centre)], mode="markers",
                marker=dict(color=COLORS["outlier"], size=10), row=3, col=1)
fig.update_yaxes(range=[-1, 1], row=3, col=1)
fig.update_layout(**LAYOUT, height=720, showlegend=False)
st.plotly_chart(fig)

# ---------- Plot: correlation for each lag ----------
fig_lag = go.Figure(go.Bar(
    x=lag_corr.index, y=lag_corr.values,
    marker_color=[COLORS["outlier"] if k == lag else COLORS["main"] for k in lag_corr.index],
))
fig_lag.update_layout(**LAYOUT, height=300, xaxis_title="Lag (weeks)", yaxis_title="Correlation",
                      title="Correlation over the whole period for each lag (orange = chosen lag)")
st.plotly_chart(fig_lag)

with st.expander("How to read the plots"):
    st.markdown(
        "- **Sliding window correlation** is the correlation inside a moving window of weeks. "
        "Values near +1 or -1 mean a strong connection in that period, values near 0 mean no connection.\n"
        "- If the correlation **changes sign or strength between seasons**, the weather affects the reservoirs "
        "differently through the year – useful to know when choosing exogenous variables for the forecast.\n"
        "- Correlation does not mean causation: both series may simply follow the same seasonal pattern."
    )