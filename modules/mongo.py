import pandas as pd
import streamlit as st
from pymongo import MongoClient


@st.cache_resource
def get_collection():
    client = MongoClient(st.secrets["MONGO_uri"])
    return client["ind320"]["crossborder_flow"]


@st.cache_data(ttl=3600)
def list_connections():
    return sorted(get_collection().distinct("connection"))


@st.cache_data(ttl=3600, show_spinner="Reading from MongoDB ...")
def load_flows(connection: str) -> pd.DataFrame:
    docs = list(get_collection().find({"connection": connection}, {"_id": 0}))
    df = pd.DataFrame(docs)
    if df.empty:
        return df
    df["time"] = pd.to_datetime(df["time"]).dt.tz_localize("UTC").dt.tz_convert("Europe/Oslo")
    df["year"] = df["time"].dt.year
    df["month"] = df["time"].dt.month
    return df.sort_values("time")