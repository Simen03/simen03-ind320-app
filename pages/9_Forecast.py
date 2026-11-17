import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from modules.controls import area_label, get_selection
from modules.forecast import DEFAULTS, build_weekly, snarimax_forecast
from modules.reservoir_data import load_reservoirs
from modules.style import COLORS, LAYOUT, page_header
from modules.weather import WEATHER_VARS

page_header("Forecast of reservoir filling", "Predictive",
            "River's SNARIMAX model learns the weekly filling level one week at a time and forecasts dynamically: "
            "each predicted week is used as input for the next. The defaults are the best settings from the notebook tests.")

# Global selections: area (also set by clicking on the map) and the interval of weeks to choose from
start, end, area_type, number = get_selection()
name = area_label(area_type, number)

# Selectable exogenous variables: weather from open-meteo and exchange rates from Norges Bank
EXOG_LABELS = {**{k: v[0] for k, v in WEATHER_VARS.items()}, "EUR": "EUR/NOK", "USD": "USD/NOK"}

# ---------- Time frame, synced with the map ----------
weeks = list(pd.to_datetime(sorted(load_reservoirs(start, end)["date_Id"].unique())))
if not weeks:
    st.warning("No data in the selected interval.")
    st.stop()
saved_week = st.session_state.get("map_week")

with st.container(border=True):
    st.markdown("**Time frame** – the chosen week is shared with the map page")
    c1, c2, c3 = st.columns([2, 1, 1])
    origin = c1.select_slider("Last week of training data", options=weeks,
                              value=saved_week if saved_week in weeks else weeks[-1],
                              format_func=lambda d: f"Week {d.isocalendar().week}, {d:%d %b %Y}")
    st.session_state["map_week"] = origin                    # keep the map in sync
    history_years = c2.slider("Training history (years)", 1, 10, DEFAULTS["history_years"])
    horizon = c3.slider("Forecast horizon (weeks)", 4, 52, DEFAULTS["horizon"])

# ---------- Model settings ----------
with st.container(border=True):
    st.markdown("**Model**")
    exog = st.multiselect("Exogenous variables", list(EXOG_LABELS), default=list(DEFAULTS["exog"]),
                          format_func=EXOG_LABELS.get)
    c = st.columns(7)
    p = c[0].number_input("p (AR)", 0, 5, DEFAULTS["p"], help="Number of previous weeks used")
    d = c[1].number_input("d (differencing)", 0, 2, DEFAULTS["d"], help="Model the change instead of the level")
    q = c[2].number_input("q (MA)", 0, 5, DEFAULTS["q"], help="Number of previous forecast errors used")
    m = c[3].number_input("m (season length)", 1, 52, DEFAULTS["m"], help="52 = one year of weeks")
    sp = c[4].number_input("sp (seasonal AR)", 0, 2, DEFAULTS["sp"], help="Use the same week in earlier years")
    sd = c[5].number_input("sd (seasonal diff.)", 0, 1, DEFAULTS["sd"])
    sq = c[6].number_input("sq (seasonal MA)", 0, 2, DEFAULTS["sq"])

# ---------- Data and forecast ----------
first_year = (origin - pd.DateOffset(years=history_years)).year
last_year = min((origin + pd.Timedelta(weeks=horizon)).year, pd.Timestamp.today().year)
try:
    data = build_weekly(area_type, number, first_year, last_year, tuple(exog))
except Exception as e:
    st.error(f"Could not download the data for the selected variables: {e}")
    st.stop()

with st.spinner("Training the model and forecasting ..."):
    result, train = snarimax_forecast(data, origin, horizon, history_years, exog, p, d, q, m, sp, sd, sq)

if len(train) < m * max(sp, sd, sq) + p + 10:
    st.warning("Very little training data for these settings. Increase the training history.")

# ---------- Key numbers ----------
m1, m2, m3 = st.columns(3)
m1.metric("Training weeks", len(train))
m2.metric(f"Forecast for week {result.index[-1].isocalendar().week}", f"{result['forecast'].iloc[-1]:.1%}")
if result["actual"].notna().all():
    # The forecast lies in the past: compare with the actual values and a naive forecast (no change)
    mae = (result["forecast"] - result["actual"]).abs().mean()
    naive = (train["filling_level"].iloc[-1] - result["actual"]).abs().mean()
    m3.metric("Mean absolute error", f"{mae * 100:.1f} pp", f"naive: {naive * 100:.1f} pp", delta_color="off")
else:
    m3.metric("Mean absolute error", "–", "forecast into the future", delta_color="off")

# ---------- Animated plot ----------
history = train["filling_level"].iloc[-104:] * 100           # last two years of training data
forecast = result["forecast"] * 100
actual = result["actual"] * 100

# The forecast line starts at the last observed week, so it connects to the history
fc_x = [history.index[-1]] + list(forecast.index)
fc_y = [history.iloc[-1]] + list(forecast.values)

# One frame per forecast week: the forecast line grows one week at a time (dynamic forecasting)
frames = [go.Frame(data=[go.Scatter(x=fc_x[:k + 1], y=fc_y[:k + 1])], traces=[2], name=str(k))
          for k in range(1, len(fc_x))]

fig = go.Figure(
    data=[
        go.Scatter(x=history.index, y=history.values, mode="lines", name="History",
                   line=dict(color=COLORS["main"])),
        go.Scatter(x=actual.index, y=actual.values, mode="lines", name="Actual",
                   line=dict(color="black", dash="dash")),
        go.Scatter(x=fc_x[:2], y=fc_y[:2], mode="lines+markers", name="Forecast",
                   line=dict(color=COLORS["outlier"])),
    ],
    frames=frames,
)

# Fixed axes, so the plot does not rescale during the animation
y_values = pd.concat([history, forecast, actual.dropna()])
fig.update_layout(
    **LAYOUT, height=500, yaxis_title="Filling level (%)",
    title=f"{name}: forecast for {horizon} weeks after {origin:%d %b %Y}",
    xaxis=dict(range=[history.index[0], forecast.index[-1]]),
    yaxis=dict(range=[max(0, y_values.min() - 5), min(100, y_values.max() + 5)]),
    updatemenus=[dict(type="buttons", showactive=False, x=0, y=-0.15, xanchor="left", buttons=[
        dict(label="▶ Play", method="animate",
             args=[None, {"frame": {"duration": 150, "redraw": False}, "fromcurrent": True}]),
        dict(label="⏸ Pause", method="animate",
             args=[[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}]),
    ])],
    sliders=[dict(x=0.15, len=0.85, y=-0.08, currentvalue=dict(prefix="Forecast week: "), steps=[
        dict(method="animate", label=str(k),
             args=[[str(k)], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}])
        for k in range(1, len(fc_x))])],
)
fig.update_layout(margin=dict(l=10, r=10, t=60, b=110))     # room for the play button and slider
st.plotly_chart(fig)

with st.expander("Forecast values and notes"):
    st.dataframe((result * 100).round(1).rename(columns={"forecast": "Forecast (%)", "actual": "Actual (%)"}))
    st.markdown(
        "- **Exogenous variables in the forecast weeks:** observed values are used where they exist; "
        "for future weeks the mean of the same week in the training years is used.\n"
        "- **Naive forecast:** the filling level stays as in the last training week. "
        "A useful model should have a lower error than this."
    )

