import matplotlib.pyplot as plt
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

# Create the plot based on the user's selection. If a specific column is chosen, plot that column for each area number. 
# If "All columns" is selected, create a panel for each area number with all numeric columns normalized to a 0-1 range.
if column_choice != "All columns":
    # One line per area number
    fig, ax = plt.subplots(figsize=(12, 6))
    for number in region_numbers:
        g = df[df["region_number"] == number]
        ax.plot(g['date_Id'], g[column_choice], label=area_label(area_type, number))
    ax.set_ylabel(column_choice)
    ax.set_title(f"{column_choice} over time")
    ax.set_xlabel("Date")
    ax.grid(True)
    ax.legend()
    fig.autofmt_xdate()
else:
    # One panel per area number, all columns normalized to 0-1
    fig, axes = plt.subplots(
        len(region_numbers), 1,
        figsize=(12, 3.5 * len(region_numbers)),
        sharex=True, squeeze=False,
    )
    for ax, number in zip(axes[:, 0], region_numbers):
        g = df[df["region_number"] == number].set_index('date_Id')[numeric_columns]
        rng = (g.max() - g.min()).replace(0, 1)          # avoid dividing by zero
        norm = (g - g.min()) / rng
        for column in numeric_columns:
            ax.plot(norm.index, norm[column], label=column)
        ax.set_title(area_label(area_type, number))
        ax.set_ylabel("Normalized (0-1)")
        ax.grid(True)
    axes[0, 0].legend(fontsize=8, ncol=2)
    axes[-1, 0].set_xlabel("Date")
    fig.autofmt_xdate()
    fig.tight_layout()

st.pyplot(fig)