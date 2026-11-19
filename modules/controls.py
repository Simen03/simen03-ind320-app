import pandas as pd
import streamlit as st

# Area types and variables in Magasinstatistikk
TYPES = ["EL", "NO", "VASS"]
TYPE_NAMES = {"EL": "EL - price areas (NO1-NO5)", "NO": "NO - Norway total", "VASS": "VASS - water areas"}
VARIABLES = ["filling_level", "filling_Twh", "filling_level_previous_week", "change_filling_level"]
AREA_NUMBERS = {"EL": [1, 2, 3, 4, 5], "VASS": [1, 2, 3], "NO": [0]}


def area_label(area_type, number):
    """Readable area name, e.g. ('EL', 3) -> 'NO3' and ('VASS', 1) -> 'VASS 1'."""
    return {"EL": f"NO{number}", "NO": "Norway", "VASS": f"VASS {number}"}[area_type]


def global_controls():
    """Global selections in the sidebar, drawn once in main.py so they appear on every page.
    The widgets have keys, so their values live in st.session_state and are shared by all pages."""
    this_month = pd.Timestamp.today().to_period("M")
    months = [p.strftime("%Y-%m") for p in pd.period_range("1995-01", this_month, freq="M")]

    # Defaults the first time the app is opened: the last five years and the price areas
    # Saved interval, or the last five years the first time the app is opened.
    # Checked, so an invalid value from an earlier version of the app is replaced by the default.
    saved = st.session_state.get("interval")
    if not (isinstance(saved, (tuple, list)) and len(saved) == 2 and all(m in months for m in saved)):
        saved = (months[-61], months[-1])
    st.session_state.setdefault("area_type", "EL")

    # A click on the map is stored as 'pending_area' and applied here, BEFORE the widgets are drawn
    # (Streamlit does not allow changing a widget's value after the widget is created in the same run)
    if "pending_area" in st.session_state:
        st.session_state["area_type"], st.session_state["region_number"] = st.session_state.pop("pending_area")

    # Make sure the chosen area exists for the area type (e.g. NO5 is chosen and the type is changed to VASS)
    numbers = AREA_NUMBERS[st.session_state["area_type"]]
    if st.session_state.get("region_number") not in numbers:
        st.session_state["region_number"] = numbers[0]

    with st.sidebar:
        st.header("Selection")
        # No key: a select_slider only becomes a range slider (two handles) when `value` is a pair,
        # so the current interval is passed as value and stored in the session state afterwards
        st.session_state["interval"] = tuple(
        st.select_slider("Time interval (months)", options=months, value=saved))
        st.radio("Area type", TYPES, format_func=TYPE_NAMES.get, key="area_type")
        st.selectbox("Area", AREA_NUMBERS[st.session_state["area_type"]],
                     format_func=lambda n: area_label(st.session_state["area_type"], n), key="region_number")
        st.caption("The area can also be selected by clicking on the map.")


def get_selection():
    """Read the global selections: start and end of the interval, area type and area number."""
    first, last = st.session_state["interval"]
    start = pd.Period(first, "M").start_time
    end = pd.Period(last, "M").end_time
    return start, end, st.session_state["area_type"], st.session_state["region_number"]


def select_area_on_map(area_type, number):
    """Used by the map: remember the clicked area and rerun, so the sidebar and the other pages follow."""
    st.session_state["pending_area"] = (area_type, number)
    st.rerun()