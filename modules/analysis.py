# Analysis functions used by the Streamlit app.
# Every function returns a Plotly figure (and summaries where relevant), shown with st.plotly_chart().
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.fft import dct, idct
from scipy.signal import spectrogram
from scipy.stats import median_abs_deviation
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler

from statsmodels.tsa.seasonal import STL
from modules.style import COLORS, LAYOUT


def spc_outliers(series, cutoff=0.01, n_std=3.0, label="Temperature", unit="°C"):
    """SPC outlier detection on DCT high-pass filtered data (SATV).
    cutoff: fraction of DCT coefficients treated as low-frequency (seasonal) and removed.
    n_std:  number of robust standard deviations for the control limits.
    label, unit: name and unit of the weather property, used in the plot and the outlier table."""
    x = series.to_numpy()
    coefs = dct(x, norm="ortho")                 # time series -> cosine coefficients
    k = int(cutoff * len(coefs))                 # number of low-frequency coefficients to remove

    # Low-pass: keep only the first k coefficients -> slow/seasonal part
    low = coefs.copy(); low[k:] = 0
    trend = idct(low, norm="ortho")
    satv = x - trend                             # high-pass = original - low-pass (SATV)

    # Robust centre and spread of the SATV, and limits moved back to the original scale
    med = np.median(satv)
    sigma = median_abs_deviation(satv, scale="normal")
    upper = trend + med + n_std * sigma
    lower = trend + med - n_std * sigma
    is_out = (satv > med + n_std * sigma) | (satv < med - n_std * sigma)

    # Plot the original series with the limits; outliers in a contrasting colour (SATV is not plotted)
    fig = go.Figure()
    fig.add_scatter(x=series.index, y=x, mode="lines", name=label,
                    line=dict(color=COLORS["main"], width=1))
    fig.add_scatter(x=series.index, y=upper, mode="lines", name="Upper limit",
                    line=dict(color=COLORS["limit"], dash="dash"))
    fig.add_scatter(x=series.index, y=lower, mode="lines", name="Lower limit",
                    line=dict(color=COLORS["limit"], dash="dash"))
    fig.add_scatter(x=series.index[is_out], y=x[is_out], mode="markers", name="Outlier",
                    marker=dict(color=COLORS["outlier"], size=6))
    fig.update_layout(**LAYOUT, height=420, xaxis_title="Time", yaxis_title=f"{label} ({unit})")

    summary = {"n_outliers": int(is_out.sum()), "share": float(is_out.mean()),
               "median_satv": float(med), "robust_std": float(sigma)}
    outliers = series[is_out].to_frame(label)
    return fig, summary, outliers


def lof_anomalies(series, contamination=0.01, n_neighbors=20, label="Temperature", unit="°C"):
    """Anomalies in a weather property using Local Outlier Factor.
    contamination: expected share of anomalies. Time is included as a feature, so an hour is an anomaly
    when it differs from the hours around it."""
    # Features: time and value, standardised so both have the same weight
    t = np.arange(len(series))
    X = StandardScaler().fit_transform(np.column_stack([t, series.to_numpy()]))
    lof = LocalOutlierFactor(n_neighbors=n_neighbors, contamination=contamination)
    is_out = lof.fit_predict(X) == -1            # -1 = anomaly

    fig = go.Figure()
    fig.add_scatter(x=series.index, y=series, mode="lines", name=label,
                    line=dict(color=COLORS["main"], width=1))
    fig.add_scatter(x=series.index[is_out], y=series[is_out], mode="markers", name="Anomaly",
                    marker=dict(color=COLORS["outlier"], size=6))
    fig.update_layout(**LAYOUT, height=420, xaxis_title="Time", yaxis_title=f"{label} ({unit})")

    summary = {"n_anomalies": int(is_out.sum()), "share": float(is_out.mean()),
               "min": float(series[is_out].min()), "max": float(series[is_out].max())}
    return fig, summary, series[is_out].to_frame(label)


def stl_plot(series, period=52, seasonal=13, trend=89, robust=True):
    """STL decomposition of weekly filling level, shown as four panels with a shared time axis.
    seasonal and trend must be odd integers."""
    s = series.asfreq("W-SUN").interpolate()     # regular weekly index (Sundays)
    res = STL(s, period=period, seasonal=seasonal, trend=trend, robust=robust).fit()

    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.04,
                        subplot_titles=("Observed", "Trend", "Seasonal", "Residual"))
    for row, component in enumerate([res.observed, res.trend, res.seasonal], start=1):
        fig.add_scatter(x=component.index, y=component, mode="lines",
                        line=dict(color=COLORS["main"]), row=row, col=1)
    # Residuals as bars, so single unusual weeks stand out
    fig.add_bar(x=res.resid.index, y=res.resid, marker_color=COLORS["secondary"], row=4, col=1)
    fig.update_layout(**LAYOUT, height=750, showlegend=False)
    return fig


def spectrogram_plot(series, window_length=104, overlap=78):
    """Spectrogram of weekly data as a heatmap. window_length and overlap are in weeks."""
    s = series.asfreq("W-SUN").interpolate()
    # fs=52 samples per year -> frequencies in cycles per year
    f, t, Sxx = spectrogram(s.to_numpy(), fs=52,
                            nperseg=window_length, noverlap=overlap, detrend="linear")
    times = s.index[0] + pd.to_timedelta(t * 365.25, unit="D")   # years from start -> dates

    # Power in decibels, so both strong and weak frequencies are visible
    fig = go.Figure(go.Heatmap(x=times, y=f, z=10 * np.log10(Sxx + 1e-12),
                               colorscale="Blues", colorbar=dict(title="dB")))
    fig.update_layout(**LAYOUT, height=420, xaxis_title="Time", yaxis_title="Cycles per year")
    return fig