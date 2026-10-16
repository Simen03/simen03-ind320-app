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

# Each date contains several rows per area type. Average values within each
# area type so the types remain separate in the time series.
plot_df = (
    plot_df.groupby(["date_Id", "region_type"], as_index=False)[numeric_columns]
    .mean()
    .sort_values(["date_Id", "region_type"])
)
area_types = plot_df["region_type"].dropna().unique().tolist()

fig, ax = plt.subplots(figsize=(12, 6))

if column_choice == "All columns":
    # Normalize each column so columns with different units can be compared.
    plot_values = plot_df[numeric_columns].copy()
    plot_values = (plot_values - plot_values.min()) / (
        plot_values.max() - plot_values.min()
    )
    plot_values = plot_values.fillna(0)

    for column in numeric_columns:
        for area_type in area_types:
            area_mask = plot_df["region_type"] == area_type
            ax.plot(
                plot_df.loc[area_mask, "date_Id"],
                plot_values.loc[area_mask, column],
                label=f"{column} ({area_type})",
            )
    ax.set_ylabel("Normalized value (0-1)")
else:
    for area_type in area_types:
        area_mask = plot_df["region_type"] == area_type
        ax.plot(
            plot_df.loc[area_mask, "date_Id"],
            plot_df.loc[area_mask, column_choice],
            label=f"{column_choice} ({area_type})",
        )
    ax.set_ylabel(column_choice)

ax.set_title("Reservoir data over time")
ax.set_xlabel("Date")
ax.grid(True)
ax.legend()
fig.autofmt_xdate()

st.pyplot(fig)