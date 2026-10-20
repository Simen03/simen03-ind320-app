import pandas as pd
import streamlit as st
from modules.controls import sidebar_controls, area_label, VARIABLES
from modules.reservoir_data import load_reservoirs

st.title("Reservoir overview")

start, end, area_type = sidebar_controls()
variable = st.selectbox("Column", VARIABLES)

df = load_reservoirs(start, end)
df = df[df["region_type"] == area_type]
df["date_Id"] = pd.to_datetime(df["date_Id"])
if df.empty:
    st.warning("No data for this selection.")
    st.stop()

rows = []
for number, g in df.groupby("region_number"):
    g = g.sort_values("date_Id")
    rows.append({
        "Area": area_label(area_type, number),
        "Selected period": g[variable].tolist(),     # whole interval, not just the first month
        "Mean": g[variable].mean(),
        "Latest": g[variable].iloc[-1],
    })
table = pd.DataFrame(rows)

period_text = f"{start:%Y-%m-%d} to {end:%Y-%m-%d}"

lo, hi = df[variable].min(), df[variable].max()
st.dataframe(
    table,
    hide_index=True,
    column_config={
        "Selected period": st.column_config.LineChartColumn(
            period_text, y_min=float(lo), y_max=float(hi)),
    },
)
st.caption(f"{start.date()} to {end.date()}, {len(df)} rows from NVE")