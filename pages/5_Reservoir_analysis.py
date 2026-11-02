import streamlit as st

from modules.analysis import spectrogram_plot, stl_plot
from modules.controls import area_label, region_selector, sidebar_controls
from modules.NVE_API import select_area
from modules.reservoir_data import load_reservoirs

st.title("Reservoir analysis")
st.write("Seasonal-trend decomposition (STL) and spectrogram of the filling level. "
         "Period, area type and area are set in the sidebar.")

# Global controls (shared with the other pages)
start, end, area_type = sidebar_controls()
number = region_selector(area_type)
name = area_label(area_type, number)

# Weekly filling level for the chosen area and interval
df = load_reservoirs(start, end)
fill = select_area(df, area_type, number)["filling_level"]

# STL with period 52 needs at least two full years of data
if len(fill) < 2 * 52 + 1:
    st.warning("STL and spectrogram need at least two years of data. Increase the download interval in the sidebar.")
    st.stop()

st.caption(f"Filling level for {name}, {start:%Y-%m} to {end:%Y-%m} ({len(fill)} weeks)")

tab_stl, tab_spec = st.tabs(["STL decomposition", "Spectrogram"])

with tab_stl:
    c1, c2, c3 = st.columns(3)
    # step=2 keeps the values odd, which STL requires
    seasonal = c1.slider("Seasonal smoother", 7, 51, 13, step=2,
                         help="Odd number. Larger values give a more stable seasonal pattern.")
    trend = c2.slider("Trend smoother", 53, 209, 89, step=2,
                      help="Odd number larger than the period (52 weeks). Larger values give a smoother trend.")
    robust = c3.checkbox("Robust", value=True,
                         help="Down-weights unusual weeks so they do not distort trend and season.")
    st.pyplot(stl_plot(fill, seasonal=seasonal, trend=trend, robust=robust))

with tab_spec:
    c1, c2 = st.columns(2)
    window = c1.slider("Window length (weeks)", 26, min(260, len(fill)), 104)
    # Overlap must be smaller than the window, so its max depends on the first slider
    overlap = c2.slider("Window overlap (weeks)", 0, window - 1, min(78, window - 1))
    st.pyplot(spectrogram_plot(fill, window_length=window, overlap=overlap))
    st.caption("The bright band at 1 cycle per year is the yearly filling/emptying cycle of the reservoirs.")