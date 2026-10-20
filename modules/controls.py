import pandas as pd
import streamlit as st

# 
TYPES = ["EL", "NO", "VASS"]
TYPE_NAMES = {"EL": "EL - price areas (NO1-NO5)", "NO": "NO - Norway total", "VASS": "VASS - watercourse areas"}
VARIABLES = ["filling_level", "filling_Twh", "filling_level_previous_week", "change_filling_level"]

# labels for the variables, used in the sidebar and in the plots
def area_label(area_type, number):
    return {"EL": f"NO{number}", "NO": "Norway", "VASS": f"VASS {number}"}[area_type]

# Create the sidebar controls
def sidebar_controls():
    """Slider = download interval, radio = area type. Remembered between pages."""
    this_month = pd.Timestamp.today().to_period("M")
    months = [p.strftime("%Y-%m") for p in pd.period_range("1995-01", this_month, freq="M")]

    interval = st.sidebar.select_slider(
        "Download interval (months)",
        options=months,
        value=st.session_state.get("interval", (months[-61], months[-1])),
    )
    area_type = st.sidebar.radio(
        "Area type",
        TYPES,
        index=TYPES.index(st.session_state.get("area_type", "EL")),
        format_func=lambda t: TYPE_NAMES[t],
    )
    st.session_state["interval"] = interval
    st.session_state["area_type"] = area_type

    start = pd.Period(interval[0], "M").start_time
    end = pd.Period(interval[1], "M").end_time
    return start, end, area_type