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

st.write("**Data table:** Reservoir levels from NVE for each area, with a small line chart of the selected period.")
st.write("**Plot:** Reservoir data over time, either one column for all areas or all columns scaled to 0-1.")
st.write("**Cross-border flows:** Hourly electricity flows between Norway and its neighbours, shown as a yearly pie chart and a monthly line plot.")