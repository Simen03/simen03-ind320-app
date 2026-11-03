# Analysis functions shared by the Jupyter Notebook and the Streamlit app.
# Every function returns a matplotlib figure (and summaries where relevant), so the app can show it with st.pyplot().
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.fft import dct, idct
from scipy.stats import median_abs_deviation
from scipy.signal import spectrogram
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.seasonal import STL


def spc_outliers(series, cutoff=0.01, n_std=3.0):
    """SPC outlier detection on DCT high-pass filtered data (SATV).
    cutoff: fraction of DCT coefficients treated as low-frequency (seasonal) and removed.
    n_std: number of robust standard deviations for the control limits."""
    x = series.to_numpy()
    coefs = dct(x, norm="ortho")
    k = int(cutoff * len(coefs))                 

    low = coefs.copy(); low[k:] = 0              
    trend = idct(low, norm="ortho")
    satv = x - trend                             

    med = np.median(satv)
    sigma = median_abs_deviation(satv, scale="normal")  
    upper = trend + med + n_std * sigma          
    lower = trend + med - n_std * sigma
    is_out = (satv > med + n_std * sigma) | (satv < med - n_std * sigma)

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(series.index, x, lw=0.6, label="Precipitation")
    ax.plot(series.index, upper, "--", label="Upper limit")
    ax.plot(series.index, lower, "--", label="Lower limit")
    ax.scatter(series.index[is_out], x[is_out], color="red", s=10, zorder=3, label="Outlier")
    ax.legend(); ax.set_ylabel("mm")

    summary = {"n_outliers": int(is_out.sum()), "share": float(is_out.mean()),
               "median_satv": med, "robust_std": sigma}
    outliers = series[is_out].to_frame("precipitation")
    plt.close(fig)  
    return fig, summary, outliers



def lof_anomalies(series, contamination=0.01, n_neighbors=20):
    """Temperature anomalies using Local Outlier Factor. contamination = expected share of outliers."""
    t = np.arange(len(series))                                      
    X = StandardScaler().fit_transform(np.column_stack([t, series.to_numpy()]))
    lof = LocalOutlierFactor(n_neighbors=n_neighbors, contamination=contamination)
    is_out = lof.fit_predict(X) == -1                               

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(series.index, series, lw=0.6, label="Temperature")
    ax.scatter(series.index[is_out], series[is_out], color="red", s=10, zorder=3, label="Anomaly")
    ax.legend(); ax.set_ylabel("°C")

    summary = {"n_anomalies": int(is_out.sum()), "share": float(is_out.mean()),
               "min": float(series[is_out].min()), "max": float(series[is_out].max())}
    plt.close(fig)  
    return fig, summary, series[is_out].to_frame("temperature")


def stl_plot(series, period=52, seasonal=13, trend=89, robust=True):
    """STL decomposition of weekly filling level. seasonal and trend must be odd integers."""
    s = series.asfreq("W-SUN").interpolate()
    res = STL(s, period=period, seasonal=seasonal, trend=trend, robust=robust).fit()
    fig = res.plot()
    fig.set_size_inches(12, 8)
    plt.close(fig)        
    return fig


def spectrogram_plot(series, window_length=104, overlap=78):
    """Spectrogram of weekly data. window_length and overlap are in weeks."""
    s = series.asfreq("W-SUN").interpolate()
    f, t, Sxx = spectrogram(s.to_numpy(), fs=52,          
                            nperseg=window_length, noverlap=overlap, detrend="linear")
    times = s.index[0] + pd.to_timedelta(t * 365.25, unit="D")   

    fig, ax = plt.subplots(figsize=(12, 4))
    m = ax.pcolormesh(times, f, 10 * np.log10(Sxx + 1e-12), shading="auto")
    fig.colorbar(m, ax=ax, label="Power (dB)")
    ax.set_ylabel("Cycles per year"); ax.set_xlabel("Time")
    plt.close(fig)  
    return fig