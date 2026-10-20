import streamlit as st

# Main application, which sets the page configuration and defines the available pages in the Streamlit app.
# The navigation is handled by the st.navigation function, which allows users to switch between different pages of the app.
if __name__ == "__main__":
    st.set_page_config(
        page_title="Reservoir data",
        page_icon=":bar_chart:",
        layout="wide",
    )

    pages = [
        st.Page("pages/1_Home_page.py", title="Home"),
        st.Page("pages/2_Reservoir_overview.py", title="Reservoir overview"),
        st.Page("pages/3_Reservoir_plot.py", title="Reservoir plot"),
        st.Page("pages/4_Cross_border_flows.py", title="Cross-border flows")
    ]

    navigation = st.navigation(pages)
    navigation.run()