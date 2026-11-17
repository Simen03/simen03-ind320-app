import pandas as pd
import plotly.express as px
import streamlit as st

from modules.controls import VARIABLES, area_label, get_selection
from modules.currency import load_exchange_rates
from modules.reservoir_data import load_reservoirs
from modules.style import COLORS, LAYOUT, page_header

page_header("Data overview", "Explore",
            "Reservoir data from Magasinstatistikk and exchange rates from Norges Bank, for the interval in the sidebar.")

start, end, area_type, number = get_selection()
name = area_label(area_type, number)

df = load_reservoirs(start, end)
df_type = df[df["region_type"] == area_type].copy()
if df_type.empty:
    st.warning("No data for this selection.")
    st.stop()

tab_first, tab_series, tab_rates = st.tabs(["First month", "Time series", "Exchange rates"])

# ---------- Tab 1: first month of each variable as a row-wise LineChartColumn ----------
with tab_first:
    st.caption(f"One row per variable for {name}, with the first month of the interval as a small line chart.")
    area_df = df_type[df_type["region_number"] == number].sort_values("date_Id")
    first_month = area_df["date_Id"].min().to_period("M")
    first = area_df[area_df["date_Id"].dt.to_period("M") == first_month]

    rows = [{"Variable": v, "First month": first[v].tolist(),
             "Mean": first[v].mean(), "Latest": first[v].iloc[-1]} for v in VARIABLES]
    st.dataframe(pd.DataFrame(rows), hide_index=True, column_config={
        "First month": st.column_config.LineChartColumn(f"First month: {first_month}"),
    })

# ---------- Tab 2: time series for all areas of the chosen type ----------
with tab_series:
    numeric_columns = df_type.select_dtypes(include="number").columns.difference(
        ["capacity_Twh", "region_number", "iso_year", "iso_week"]).tolist()
    column_choice = st.selectbox("Column", ["All columns"] + numeric_columns)
    df_type["Area"] = df_type["region_number"].map(lambda n: area_label(area_type, n))

    if column_choice != "All columns":
        # One line per area
        fig = px.line(df_type, x="date_Id", y=column_choice, color="Area",
                      labels={"date_Id": "Date"}, title=f"{column_choice} over time")
    else:
        # One panel per area, all columns normalized to 0-1 so they can be compared
        long = []
        for n, g in df_type.groupby("region_number"):
            g = g.set_index("date_Id")[numeric_columns]
            norm = ((g - g.min()) / (g.max() - g.min()).replace(0, 1)).reset_index()
            norm = norm.melt(id_vars="date_Id", var_name="Variable", value_name="Normalized (0-1)")
            norm["Area"] = area_label(area_type, n)
            long.append(norm)
        fig = px.line(pd.concat(long), x="date_Id", y="Normalized (0-1)", color="Variable", facet_row="Area",
                      labels={"date_Id": "Date"}, height=250 * df_type["region_number"].nunique())
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))   # "Area=NO1" -> "NO1"
    fig.update_layout(**LAYOUT)
    st.plotly_chart(fig)

# ---------- Tab 3: exchange rates from Norges Bank ----------
with tab_rates:
    try:
        rates = load_exchange_rates(start.strftime("%Y-%m-%d")).loc[start:end].rename_axis("Date")
    except Exception as e:
        st.error(f"Could not download exchange rates from Norges Bank: {e}")
    else:
        fig = px.line(rates, labels={"value": "NOK per unit", "variable": "Currency"},
                      color_discrete_sequence=[COLORS["main"], COLORS["outlier"]],
                      title="EUR and USD in NOK (business days)")
        fig.update_layout(**LAYOUT)
        st.plotly_chart(fig)