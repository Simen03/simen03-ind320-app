import streamlit as st

from modules.controls import area_label, get_selection

st.title("Reservoirs, weather and power exchange in Norway")
st.write("Explore reservoir filling from NVE's Magasinstatistikk together with weather data from open-meteo, "
         "exchange rates from Norges Bank and cross-border power flows from ENTSO-E (via MongoDB).")

# Current global selection (set in the sidebar or by clicking on the map)
start, end, area_type, number = get_selection()
st.info(f"**Selected area:** {area_label(area_type, number)}  ·  **Interval:** {start:%b %Y} – {end:%b %Y}. "
        "Change it in the sidebar or by clicking an area on the map.")

# One column per group of pages, with links
col1, col2, col3 = st.columns(3)
with col1, st.container(border=True):
    st.badge("Explore", icon=":material/explore:", color="blue")
    st.page_link("pages/7_Map.py", label="Map and area selection", icon=":material/map:")
    st.page_link("pages/2_Data_overview.py", label="Data overview", icon=":material/table_chart:")
    st.page_link("pages/4_Cross_border_flows.py", label="Cross-border flows", icon=":material/swap_horiz:")
with col2, st.container(border=True):
    st.badge("Anomalies", icon=":material/warning:", color="orange")
    st.page_link("pages/5_Reservoir_analysis.py", label="Reservoir analysis (STL, spectrogram)", icon=":material/insights:")
    st.page_link("pages/6_Weather_anomalies.py", label="Weather anomalies (SPC, LOF)", icon=":material/thunderstorm:")
with col3, st.container(border=True):
    st.badge("Predictive", icon=":material/trending_up:", color="violet")
    st.page_link("pages/8_Correlation.py", label="Weather–reservoir correlation", icon=":material/compare_arrows:")
    st.page_link("pages/9_Forecast.py", label="Forecast of reservoir filling", icon=":material/show_chart:")

st.caption("Global selections (area and interval) are shared by all pages. "
           "Settings that only matter for one analysis, such as year, weather property or model parameters, are chosen on that page.")