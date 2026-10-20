import pandas as pd
import streamlit as st
from modules.NVE_API import fetch_reservoirs

# Cache the data for 1 hour to avoid repeated downloads from NVE. The spinner message is shown while downloading.
@st.cache_data(ttl=3600, show_spinner="Downloading data from NVE ...")
def load_reservoirs(start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    df = fetch_reservoirs()
    df["date_Id"] = pd.to_datetime(df["date_Id"])          # real date type for all pages
    df = df[(df["date_Id"] >= start) & (df["date_Id"] <= end)]
    return df.sort_values(["region_type", "region_number", "date_Id"]).reset_index(drop=True)
