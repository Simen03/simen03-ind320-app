import streamlit as st

from modules.analysis import lof_anomalies, spc_outliers
from modules.controls import area_label, region_selector, sidebar_controls
from modules.weather import load_weather, WEATHER_VARS

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

tab_spc, tab_lof = st.tabs(["Outliers (SPC)", "Anomalies (LOF)"])

# Local selector in each tab: which weather property to analyse (temperature is the default, as it is listed first)
PROPERTIES = list(WEATHER_VARS)

with tab_spc:
    prop = st.selectbox("Weather property", PROPERTIES, format_func=lambda v: WEATHER_VARS[v][0], key="spc_property")
    label, unit = WEATHER_VARS[prop]
    c1, c2 = st.columns(2)
    cutoff = c1.slider("DCT cut-off (share of low frequencies removed)", 0.001, 0.100, 0.010,
                       step=0.001, format="%.3f")
    n_std = c2.slider("Number of robust standard deviations", 1.0, 6.0, 3.0, step=0.5)

    fig, summary, outliers = spc_outliers(weather[prop], cutoff=cutoff, n_std=n_std, label=label, unit=unit)
    st.plotly_chart(fig)

    m1, m2, m3 = st.columns(3)
    m1.metric("Outliers", summary["n_outliers"])
    m2.metric("Share of hours", f"{summary['share']:.2%}")
    m3.metric(f"Robust std ({unit})", f"{summary['robust_std']:.3f}")
    st.dataframe(outliers.sort_values(label, ascending=False))

with tab_lof:
    prop = st.selectbox("Weather property", PROPERTIES, format_func=lambda v: WEATHER_VARS[v][0], key="lof_property")
    label, unit = WEATHER_VARS[prop]
    c1, c2 = st.columns(2)
    contamination = c1.slider("Proportion of outliers", 0.001, 0.100, 0.010, step=0.001, format="%.3f")
    n_neighbors = c2.slider("Number of neighbours", 5, 100, 20)

    fig, summary, anomalies = lof_anomalies(weather[prop], contamination=contamination,
                                            n_neighbors=n_neighbors, label=label, unit=unit)
    st.plotly_chart(fig)

    m1, m2, m3 = st.columns(3)
    m1.metric("Anomalies", summary["n_anomalies"])
    m2.metric(f"Lowest anomaly ({unit})", f"{summary['min']:.1f}")
    m3.metric(f"Highest anomaly ({unit})", f"{summary['max']:.1f}")
    st.dataframe(anomalies)