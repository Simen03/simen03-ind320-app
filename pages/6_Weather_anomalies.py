import streamlit as st

from modules.analysis import lof_anomalies, spc_outliers
from modules.controls import area_label, region_selector, sidebar_controls
from modules.weather import load_weather

st.title("Weather outliers and anomalies")
st.write("Hourly ERA5 reanalysis data from open-meteo, averaged over sampled locations in the chosen area.")

# Global controls: the weather area follows the same selector as the reservoir data
start, end, area_type = sidebar_controls()
number = region_selector(area_type)
name = area_label(area_type, number)

# Local control: the year only matters on this page
year = st.selectbox("Year", list(range(2025, 1999, -1)), index=1)   

# Download settings are hidden in an expander; downloading happens automatically and is cached
with st.expander("Download settings"):
    n_locations = st.slider("Number of locations to average", 1, 25, 10,
                            help="More locations = more representative, but slower and uses more of the API quota.")

weather = load_weather(name, year, n_locations)
st.caption(f"{name}, {year}: {len(weather)} hourly values, average of {n_locations} locations")

tab_spc, tab_lof = st.tabs(["Outliers (SPC) – precipitation", "Anomalies (LOF) – temperature"])

with tab_spc:
    c1, c2 = st.columns(2)
    cutoff = c1.slider("DCT cut-off (share of low frequencies removed)", 0.001, 0.100, 0.010,
                       step=0.001, format="%.3f")
    n_std = c2.slider("Number of robust standard deviations", 1.0, 6.0, 3.0, step=0.5)

    fig, summary, outliers = spc_outliers(weather["precipitation"], cutoff=cutoff, n_std=n_std)
    st.pyplot(fig)

    m1, m2, m3 = st.columns(3)
    m1.metric("Outliers", summary["n_outliers"])
    m2.metric("Share of hours", f"{summary['share']:.2%}")
    m3.metric("Robust std (mm)", f"{summary['robust_std']:.3f}")
    st.dataframe(outliers.sort_values("precipitation", ascending=False))

with tab_lof:
    c1, c2 = st.columns(2)
    contamination = c1.slider("Proportion of outliers", 0.001, 0.100, 0.010, step=0.001, format="%.3f")
    n_neighbors = c2.slider("Number of neighbours", 5, 100, 20)

    fig, summary, anomalies = lof_anomalies(weather["temperature_2m"],
                                            contamination=contamination, n_neighbors=n_neighbors)
    st.pyplot(fig)

    m1, m2, m3 = st.columns(3)
    m1.metric("Anomalies", summary["n_anomalies"])
    m2.metric("Lowest anomaly (°C)", f"{summary['min']:.1f}")
    m3.metric("Highest anomaly (°C)", f"{summary['max']:.1f}")
    st.dataframe(anomalies)