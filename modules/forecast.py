import numpy as np
import pandas as pd
import streamlit as st
from river import time_series

from modules.controls import area_label
from modules.currency import load_exchange_rates
from modules.NVE_API import select_area
from modules.reservoir_data import load_reservoirs
from modules.weather import WEATHER_VARS, weekly_weather

# Best settings from the tests in the notebook (part 4), used as defaults in the app
DEFAULTS = dict(horizon=12, history_years=8, exog=(), p=2, d=1, q=0, m=52, sp=1, sd=0, sq=0)


@st.cache_data(ttl=3600, show_spinner="Preparing weekly data ...")
def build_weekly(area_type, number, first_year, last_year, exog=()):
    """Weekly data set for one area: the filling level plus the selected exogenous variables.
    Weather and exchange rates are only downloaded if they are selected."""
    df = load_reservoirs(pd.Timestamp(f"{first_year}-01-01"), pd.Timestamp.today().normalize())
    data = select_area(df, area_type, number)[["filling_level"]]

    # Weather: weekly values in Norwegian time (same Sunday dates as Magasinstatistikk)
    weather_cols = [c for c in exog if c in WEATHER_VARS]
    if weather_cols:
        weather = weekly_weather(area_label(area_type, number), range(first_year, last_year + 1))
        data = data.join(weather[weather_cols], how="left")

    # Exchange rates: business days -> every day (last known rate) -> weekly mean
    currency_cols = [c for c in exog if c in ("EUR", "USD")]
    if currency_cols:
        rates = load_exchange_rates(f"{first_year}-01-01")
        data = data.join(rates.asfreq("D").ffill().resample("W-SUN").mean()[currency_cols], how="left")
    return data


def snarimax_forecast(data, origin, horizon=12, history_years=8, exog=(),
                      p=2, d=1, q=0, m=52, sp=1, sd=0, sq=0):
    """Train River's SNARIMAX on the weeks up to `origin` and forecast the next `horizon` weeks dynamically.
    Exogenous values in the forecast weeks: observed if available, otherwise the mean of the same week in the
    training years (climatology). Returns the forecast (with actual values where they exist) and the training data."""
    exog = list(exog)
    origin = pd.Timestamp(origin)
    train = data.loc[origin - pd.DateOffset(years=history_years):origin].dropna(subset=["filling_level"] + exog)
    future_index = pd.date_range(origin + pd.Timedelta(weeks=1), periods=horizon, freq="W-SUN")

    if exog:
        # Climatology: mean of each ISO week in the training years (week 53 -> 52)
        clim = train[exog].groupby(train.index.isocalendar().week).mean()
        weeks = future_index.isocalendar().week.clip(upper=52).values
        future_x = data[exog].reindex(future_index).fillna(clim.reindex(weeks).set_axis(future_index))
        x_train, xs = train[exog].to_dict("records"), future_x.to_dict("records")
    else:
        x_train, xs = [{}] * len(train), [{}] * horizon

    # Online learning, one week at a time in chronological order
    model = time_series.SNARIMAX(p=p, d=d, q=q, m=m, sp=sp, sd=sd, sq=sq)
    for y, x in zip(train["filling_level"], x_train):
        model.learn_one(y, x)

    # Dynamic forecast: each predicted week is used as input for the next
    forecast = np.clip(model.forecast(horizon=horizon, xs=xs), 0, 1)
    result = pd.DataFrame({"forecast": forecast}, index=future_index)
    result["actual"] = data["filling_level"].reindex(future_index)
    return result, train