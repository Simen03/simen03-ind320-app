import calendar

import matplotlib.pyplot as plt
import streamlit as st

from modules.mongo import list_connections, load_flows

st.title("Cross-border flows")

Colours = {"import": "#2a78d6", "export": "#eb6834"}   # same colour per direction in both plots
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
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.pie(
            pie.values,
            labels=[f"{Labels[d]}\n{v:.0f} GWh" for d, v in pie.items()],
            colors=[Colours[d] for d in pie.index],
            autopct="%1.1f%%",
            startangle=90,
            wedgeprops={"edgecolor": "white", "linewidth": 2},
        )
        ax.set_title(f"{connection}, {year}")
        st.pyplot(fig)

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
        fig2, ax2 = plt.subplots(figsize=(7, 5))
        for d in ["export", "import"]:
            first = True
            for m in sorted(months):
                g = df[(df["year"] == year) & (df["month"] == m) & (df["direction"] == d)]
                if g.empty:
                    continue
                # one segment per month, so non-adjacent months are not joined by a line
                ax2.plot(g["time"], g["mw"], color=Colours[d], linewidth=1,
                         label=Labels[d] if first else None)
                first = False
        ax2.set_title(f"{connection}, {year}")
        ax2.set_xlabel("Time (Europe/Oslo)")
        ax2.set_ylabel("MW")
        ax2.grid(alpha=0.3)
        ax2.legend()
        fig2.autofmt_xdate()
        st.pyplot(fig2)

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