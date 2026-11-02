import streamlit as st

# Set the page configuration for the home page
st.set_page_config(
    page_title="Reservoir data",
    page_icon=":bar_chart:",
    layout="wide",
)

# Display the title and subheader for the home page
st.title("Reservoir and cross-border flow data")
st.subheader("Chose a page from the menu to the left to explore the data.")

st.write("**Reservoir overview:** Reservoir levels from NVE for each area, with a small line chart of the selected period.")
st.write("**Reservoir plot:** Reservoir data over time, either one column for all areas or all columns scaled to 0-1.")
st.write("**Cross-border flows:** Hourly electricity flows between Norway and its neighbours, shown as a yearly pie chart and a monthly line plot.")
st.write("**Reservoir analysis:** STL decomposition and spectrogram of the filling level for the selected area.")
st.write("**Weather anomalies:** Hourly ERA5 weather for the selected area, with precipitation outliers (SPC) and temperature anomalies (LOF).")