from pathlib import Path

import openmeteo_requests
import pandas as pd
import requests
import streamlit as st
from retry_requests import retry

# Path to the sampled coordinates made in the notebook (works from both notebooks/ and the app root)
COORDS_FILE = Path(__file__).resolve().parent.parent / "data" / "region_coords.csv"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
HOURLY_VARS = ["temperature_2m", "precipitation", "wind_speed_10m", "relative_humidity_2m"]

# Retrying session: open-meteo sometimes answers with temporary errors
client = openmeteo_requests.Client(session=retry(requests.Session(), retries=5, backoff_factor=0.2))


def download_weather(region_id, start, end, n_locations=10, coords_file=COORDS_FILE):
    """Download hourly ERA5 data for a region and return the hourly average over the sampled locations.
    region_id is 'NO1'..'NO5', 'VASS 1'..'VASS 3' or 'Norway' (all price areas combined)."""
    coords = pd.read_csv(coords_file)
    if region_id == "Norway":
        c = coords[coords["region_id"].str.startswith("NO")]
    else:
        c = coords[coords["region_id"] == region_id]

    # ERA5 grid is ~0.25 deg: round and drop duplicates so we don't download the same cell twice
    c = c.assign(lat=c.lat.round(2), lon=c.lon.round(2)).drop_duplicates(["lat", "lon"])
    # Only use n_locations of the 1000 points: keeps the URL short and stays within the API quota
    c = c.sample(min(n_locations, len(c)), random_state=1)

    params = {
            "latitude": c["lat"].tolist(),        # several locations in one request
            "longitude": c["lon"].tolist(),
            "start_date": str(start), "end_date": str(end),
            "hourly": HOURLY_VARS,
            "models": "era5",
            "timezone": "Europe/Oslo",
        }
    responses = client.weather_api(ARCHIVE_URL, params=params)   # one response per location
    
    frames = []
    for r in responses:
        h = r.Hourly()
        time = pd.date_range(start=pd.to_datetime(h.Time(), unit="s", utc=True),
                                end=pd.to_datetime(h.TimeEnd(), unit="s", utc=True),
                                freq=pd.Timedelta(seconds=h.Interval()), inclusive="left")
        frames.append(pd.DataFrame({v: h.Variables(i).ValuesAsNumpy() for i, v in enumerate(HOURLY_VARS)},
                                    index=time))
    # Average across locations, hour by hour
    return pd.concat(frames).groupby(level=0).mean()


# Streamlit wrapper: downloads once per (region, year, n_locations) and keeps the result for 24 hours.
@st.cache_data(ttl=24 * 3600, show_spinner="Downloading weather data from open-meteo ...")
def load_weather(region_id, year, n_locations=10):
    return download_weather(region_id, f"{year}-01-01", f"{year}-12-31", n_locations)