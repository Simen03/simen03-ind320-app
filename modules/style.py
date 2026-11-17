import streamlit as st

# Common colours for all Plotly figures, chosen to match the theme in .streamlit/config.toml
COLORS = {
    "main": "#1f6fb2",       # main data series (same as primaryColor in the theme)
    "secondary": "#7fb3d5",  # secondary series, e.g. STL residuals
    "limit": "#8a8f98",      # control limits and reference lines
    "outlier": "#e4572e",    # outliers and anomalies (contrasting colour)
    "import": "#1f6fb2",     # flow into Norway
    "export": "#e4572e",     # flow out of Norway
}

# Shared layout for all figures: legend on top and small margins
LAYOUT = dict(
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    margin=dict(l=10, r=10, t=40, b=10),
)

# Each group of pages has its own colour and icon, shown as a badge above the page title
GROUPS = {
    "Explore": ("blue", ":material/explore:"),
    "Anomalies": ("orange", ":material/warning:"),
    "Predictive": ("violet", ":material/trending_up:"),
}


def page_header(title, group, caption=None):
    """Page title with a coloured badge that shows which group of pages is active."""
    colour, icon = GROUPS[group]
    st.badge(group, icon=icon, color=colour)
    st.title(title)
    if caption:
        st.caption(caption)