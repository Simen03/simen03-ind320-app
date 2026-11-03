import pandas as pd
import streamlit as st
from modules.controls import sidebar_controls, region_selector, area_label, VARIABLES
from modules.reservoir_data import load_reservoirs

st.title("Reservoir overview")

# Global sidebar controls: interval, area type and area (remembered between pages)
start, end, area_type = sidebar_controls()
number = region_selector(area_type)
name = area_label(area_type, number)

# Load data for the selected interval and keep only the chosen area
df = load_reservoirs(start, end)
df = df[(df["region_type"] == area_type) & (df["region_number"] == number)].copy()
df["date_Id"] = pd.to_datetime(df["date_Id"])
if df.empty:
    st.warning("No data for this selection.")
    st.stop()

# Keep only the first month that has data in the selected interval
first_month = df["date_Id"].min().to_period("M")
df = df[df["date_Id"].dt.to_period("M") == first_month].sort_values("date_Id")

rows = []
for variable in VARIABLES:
    rows.append({
        "Variable": variable,
        "First month": df[variable].tolist(),
        "Mean": df[variable].mean(),
        "Latest": df[variable].iloc[-1],
    })
table = pd.DataFrame(rows)


st.dataframe(
    table,
    hide_index=True,
    column_config={
        "First month": st.column_config.LineChartColumn(f"First month: {first_month}"),
    },
)
