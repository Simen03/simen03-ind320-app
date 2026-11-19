import pandas as pd
import requests
import streamlit as st

from modules.weather import COORDS_FILE

ELEVATION_URL = "https://api.open-meteo.com/v1/elevation"                     # the API accepts at most 100 coordinates per request


@st.cache_data(show_spinner="Looking up elevation (open-meteo) ...")
def get_elevation(lats, lons):
    """Elevation in metres for each (lat, lon) pair from open-meteo's elevation API (max 100 points per request).
    lats and lons are tuples, so the result can be cached (elevation does not change)."""
    params = {"latitude": ",".join(f"{v:.4f}" for v in lats),
              "longitude": ",".join(f"{v:.4f}" for v in lons)}
    response = requests.get(ELEVATION_URL, params=params, timeout=30)
    response.raise_for_status()                      # clear error if the API is unavailable
    return response.json()["elevation"]


@st.cache_data(show_spinner="Looking up elevation of sample points ...")
def elevation_points(region_id, n=100):
    """n of the randomly sampled points from part 3 for one area, with their elevation.
    Fixed random_state, so the same points are shown every time."""
    coords = pd.read_csv(COORDS_FILE)
    points = coords[coords["region_id"] == region_id].sample(n, random_state=1).reset_index(drop=True)
    points["elevation"] = get_elevation(tuple(points["lat"]), tuple(points["lon"]))
    return points