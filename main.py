import streamlit as st

from modules.controls import global_controls

# Page configuration for the whole app (only set here, not on the single pages)
st.set_page_config(page_title="Reservoirs, weather and power", page_icon=":material/water_drop:", layout="wide")

# Pages grouped by type of task: explore the data, find anomalies, and analyse/predict.
# The group names become headers in the menu.
pages = {
    "": [
        st.Page("pages/1_Home_page.py", title="Home", icon=":material/home:", default=True),
    ],
    "Explore": [
        st.Page("pages/7_Map.py", title="Map and area selection", icon=":material/map:"),
        st.Page("pages/2_Data_overview.py", title="Data overview", icon=":material/table_chart:"),
        st.Page("pages/4_Cross_border_flows.py", title="Cross-border flows", icon=":material/swap_horiz:"),
    ],
    "Anomalies": [
        st.Page("pages/5_Reservoir_analysis.py", title="Reservoir analysis", icon=":material/insights:"),
        st.Page("pages/6_Weather_anomalies.py", title="Weather anomalies", icon=":material/thunderstorm:"),
    ],
    "Predictive": [
        st.Page("pages/8_Correlation.py", title="Weather–reservoir correlation", icon=":material/compare_arrows:"),
        st.Page("pages/9_Forecast.py", title="Forecast of reservoir filling", icon=":material/show_chart:"),
    ],
}

navigation = st.navigation(pages)
global_controls()        # global sidebar selections, shared by all pages through the session state
navigation.run()