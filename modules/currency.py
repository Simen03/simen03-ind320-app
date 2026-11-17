import io

import pandas as pd
import requests
import streamlit as st

NB_URL = "https://data.norges-bank.no/api/data/EXR/B.{currencies}.NOK.SP"


def download_exchange_rates(currencies=("EUR", "USD"), start="2015-01-01", end=None):
    """Daily exchange rates (NOK per 1 unit of foreign currency) from Norges Bank, business days only."""
    end = end or pd.Timestamp.today().strftime("%Y-%m-%d")
    params = {"format": "csv", "startPeriod": start, "endPeriod": end, "locale": "en"}   # decimal point
    response = requests.get(NB_URL.format(currencies="+".join(currencies)), params=params, timeout=30)
    response.raise_for_status()                              # clear error if the API is unavailable

    # Semicolon-separated CSV with one row per date and currency -> one column per currency
    raw = pd.read_csv(io.StringIO(response.text), sep=";")
    rates = raw.pivot(index="TIME_PERIOD", columns="BASE_CUR", values="OBS_VALUE")
    rates.index = pd.to_datetime(rates.index)
    rates.columns.name = None
    return rates.astype(float).sort_index()


# Cached for 6 hours: Norges Bank publishes new rates once per business day
@st.cache_data(ttl=6 * 3600, show_spinner="Downloading exchange rates from Norges Bank ...")
def load_exchange_rates(start="2015-01-01"):
    return download_exchange_rates(start=start)