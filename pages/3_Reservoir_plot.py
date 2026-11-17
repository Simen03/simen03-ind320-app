import plotly.express as px
import pandas as pd
import streamlit as st

from modules.controls import sidebar_controls, area_label
from modules.reservoir_data import load_reservoirs

st.title("Plot of reservoir data")
st.write("Choose a column. The period and area type are set in the sidebar.")

# Sidebar controls for selecting the download interval and area type, which are remembered between pages.
start, end, area_type = sidebar_controls()
df = load_reservoirs(start, end)
df = df[df["region_type"] == area_type].copy()

# Ensure the date column is in datetime format and sort the DataFrame by area number and date.
if df.empty:
    st.warning("No data for this selection.")
    st.stop()

# Convert the date column to datetime and sort by area number and date.
df['date_Id'] = pd.to_datetime(df['date_Id'])                      # make sure it is a real date type
df = df.sort_values(["region_number", 'date_Id']).reset_index(drop=True)  # sort by area number and date

# Identify numeric columns for plotting, excluding specific columns that are not relevant for the plots.
numeric_columns = df.select_dtypes(include="number").columns.difference(
    ["capacity_Twh", "region_number", "iso_year", "iso_week"]
).tolist()

column_choice = st.selectbox(
    "Choose a column to plot",
    options=["All columns"] + numeric_columns,
)

region_numbers = sorted(df["region_number"].unique())

# Readable area names (NO1, VASS 2, ...) for the legend
df["Area"] = df["region_number"].map(lambda n: area_label(area_type, n))

if column_choice != "All columns":
    # One line per area
    fig = px.line(df, x="date_Id", y=column_choice, color="Area",
                  labels={"date_Id": "Date"}, title=f"{column_choice} over time")
else:
    # One panel per area, all columns normalized to 0-1 so they can be compared
    long = []
    for number in region_numbers:
        g = df[df["region_number"] == number].set_index("date_Id")[numeric_columns]
        rng = (g.max() - g.min()).replace(0, 1)          # avoid dividing by zero
        norm = ((g - g.min()) / rng).reset_index()
        norm = norm.melt(id_vars="date_Id", var_name="Variable", value_name="Normalized (0-1)")
        norm["Area"] = area_label(area_type, number)
        long.append(norm)
    fig = px.line(pd.concat(long), x="date_Id", y="Normalized (0-1)", color="Variable",
                  facet_row="Area", labels={"date_Id": "Date"}, height=250 * len(region_numbers))
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))   # "Area=NO1" -> "NO1"

st.plotly_chart(fig)