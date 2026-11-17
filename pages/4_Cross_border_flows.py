import calendar

import plotly.express as px
import plotly.graph_objects as go
from modules.style import COLORS
import streamlit as st

from modules.mongo import list_connections, load_flows

st.title("Cross-border flows")

Colours = {"import": COLORS["import"], "export": COLORS["export"]}   
Labels = {"import": "Into Norway", "export": "Out of Norway"}

left, right = st.columns(2)

# Left: pie chart of total flow per year, with selection of connection and year
with left:
    st.subheader("Total per year")

    connection = st.radio("Connection", list_connections())
    df = load_flows(connection)
    if df.empty:
        st.warning("No data for this connection.")
        st.stop()

    years = sorted(df["year"].unique())
    year = st.selectbox("Year", years, index=years.index(2025) if 2025 in years else 0)

    # Hourly MW summed over the year = MWh. Divided by 1000 to get GWh
    pie = df[df["year"] == year].groupby("direction")["mw"].sum() / 1000

    if pie.sum() == 0:
        st.info("No flow in this year.")
    else:
        # Donut chart of total flow in and out of Norway; hover shows GWh
        fig = go.Figure(go.Pie(
            labels=[Labels[d] for d in pie.index],
            values=pie.values,
            marker=dict(colors=[Colours[d] for d in pie.index], line=dict(color="white", width=2)),
            hole=0.4,
            textinfo="percent+label",
            hovertemplate="%{label}: %{value:.0f} GWh<extra></extra>",
        ))
        fig.update_layout(title=f"{connection}, {year}", showlegend=False, height=420)
        st.plotly_chart(fig)

# Right: line plot of hourly flow per month, with selection of months
with right:
    st.subheader("Hourly flow")

    months = st.pills(
        "Months",
        options=list(range(1, 13)),
        format_func=lambda m: calendar.month_abbr[m],
        selection_mode="multi",
        default=[1],
    )

    if not months:
        st.info("Select at least one month.")
    else:
        # Selected months; line_group="month" draws one line per month,
        # so non-adjacent months are not joined by a line
        sel = df[(df["year"] == year) & (df["month"].isin(months))].copy()
        sel["Direction"] = sel["direction"].map(Labels)
        fig2 = px.line(sel, x="time", y="mw", color="Direction", line_group="month",
                       color_discrete_map={Labels[d]: c for d, c in Colours.items()},
                       labels={"time": "Time (Europe/Oslo)", "mw": "MW"},
                       title=f"{connection}, {year}")
        st.plotly_chart(fig2)

# Explain the data source and processing in an expander, so it can be hidden if the user wants to focus on the plots.
with st.expander("About the data"):
    st.markdown(
        """
**Source:** ENTSO-E Transparency Platform, *physical cross-border flows* (document type A11),
fetched with the `entsoe-py` package.

**Coverage:** Norway's international connections (NO1-SE3, NO3-SE2, NO4-SE1, NO4-SE2, NO4-FI,
NO2-DK1, NO2-NL, NO2-DE_LU, NO2-GB), both directions, about two years up to October 2026.

**Processing:** values were converted to hourly means in UTC, written to Cassandra with Spark,
read back with Spark, and stored in MongoDB, which is where this page reads from.
Times are shown in Europe/Oslo.

**Reading the charts:** *Out of Norway* is flow from the Norwegian area to the neighbour,
*Into Norway* the opposite direction. The line plot shows MW per hour.
The pie chart sums the hourly MW values over the chosen year to MWh and shows them as GWh.
        """
    )