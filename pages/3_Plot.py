import matplotlib.pyplot as plt
import streamlit as st

from main import load_data


st.title("Plot of reservoir data")
st.write("Velg kolonne og tidsperiode for grafen.")

df = load_data()

numeric_columns = df.select_dtypes(include="number").columns.difference(
    ["capacity_Twh", "region_number", "iso_year", "iso_week"]
).tolist()

column_choice = st.selectbox(
    "Choose a column to plot",
    options=["All columns"] + numeric_columns,
)

months = (
    df["date_Id"]
    .dt.to_period("M")
    .astype(str)
    .sort_values()
    .unique()
    .tolist()
)

selected_months = st.select_slider(
    "Choose a period",
    options=months,
    value=(months[0], months[0]),
)

start_month, end_month = selected_months

plot_df = df[
    (df["date_Id"].dt.to_period("M").astype(str) >= start_month)
    & (df["date_Id"].dt.to_period("M").astype(str) <= end_month)
].copy()

# Each date contains one row per region. Average the selected values by date
# so the chart shows a single continuous time series instead of connecting
# observations from different regions.
plot_df = plot_df.groupby("date_Id", as_index=False)[numeric_columns].mean()

fig, ax = plt.subplots(figsize=(12, 6))

if column_choice == "All columns":
    # Normalize each series so columns with different units can be compared.
    plot_values = plot_df[numeric_columns].copy()
    plot_values = (plot_values - plot_values.min()) / (
        plot_values.max() - plot_values.min()
    )
    plot_values = plot_values.fillna(0)

    for column in numeric_columns:
        ax.plot(
            plot_df["date_Id"],
            plot_values[column],
            label=column,
        )
    ax.set_ylabel("Normalized value (0-1)")
else:
    ax.plot(
        plot_df["date_Id"],
        plot_df[column_choice],
        label=column_choice,
    )
    ax.set_ylabel(column_choice)

ax.set_title("Reservoir data over time")
ax.set_xlabel("Date")
ax.grid(True)
ax.legend()
fig.autofmt_xdate()

st.pyplot(fig)