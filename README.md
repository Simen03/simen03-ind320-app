# IND320 – Reservoirs, weather and power exchange in Norway

Course project in IND320 (NMBU). A Streamlit app and four Jupyter Notebooks that combine
reservoir filling in Norway with weather data, exchange rates and cross-border power flows.
The app is used to explore the data, find anomalies, study the connection between weather and
reservoirs, and forecast the filling level.

- **Streamlit app:** https://simen03-ind320-app-hkg3slagiyz8dtmwljxdtd.streamlit.app/
- **GitHub repository:** https://github.com/Simen03/simen03-ind320-app

## Data sources

| Source | Data | Used for |
|---|---|---|
| NVE Magasinstatistikk (API) | Weekly reservoir filling per price area (EL), water area (VASS) and Norway | All reservoir pages and the forecast |
| open-meteo (API) | Hourly ERA5 reanalysis weather (temperature, precipitation, wind, humidity) and elevation | Map, weather anomalies, correlation, forecast |
| Norges Bank (API) | Daily EUR/NOK and USD/NOK exchange rates | Data overview and as exogenous variables in the forecast |
| ENTSO-E (via Cassandra and MongoDB) | Hourly cross-border power flows, stored in MongoDB in part 2 | Cross-border flows |
| NVE Atlas (shapefiles) | Price areas and NVE regions, converted to GeoJSON | Map and random sample points for the weather data |

All time series are aligned to weeks ending on Sunday in Norwegian time, as in Magasinstatistikk.

## App structure

The pages are grouped by type of task. The area and time interval are global selections in the sidebar,
shared by all pages through the session state, and can also be set by clicking on the map.
Settings that only matter for one analysis are chosen on that page.

| Group | Page | Content |
|---|---|---|
| – | Home | Overview, current selection and links to all pages |
| Explore | Map and area selection | Areas coloured by filling level or weather for a chosen week; click to select an area; elevation of sample points |
| Explore | Data overview | First month of each variable (LineChartColumn), time series for all areas, exchange rates |
| Explore | Cross-border flows | Yearly totals and hourly flows per connection |
| Anomalies | Reservoir analysis | STL decomposition and spectrogram of the filling level |
| Anomalies | Weather anomalies | Outliers with SPC on DCT-filtered data, and anomalies with Local Outlier Factor |
| Predictive | Weather–reservoir correlation | Sliding window correlation with selectable lag and window |
| Predictive | Forecast of reservoir filling | SNARIMAX (River) with selectable parameters and exogenous variables, animated forecast |

## Repository layout

| Path | Content |
|---|---|
| `main.py` | Page configuration, menu and global sidebar selections |
| `pages/` | One file per page in the app |
| `modules/` | Shared code: data download (NVE, open-meteo, Norges Bank, MongoDB), analysis functions, forecast, map helpers and styling |
| `data/` | GeoJSON files, sampled coordinates and reservoir data |
| `notebooks/` | Jupyter Notebooks for part 1–4 (development and documentation) |
| `.streamlit/config.toml` | App theme |

## Running the app locally

Install the packages with `pip install -r requirements.txt` and start the app with `streamlit run main.py`.

The Cross-border flows page needs a MongoDB connection string in `.streamlit/secrets.toml`
(`MONGO_uri = "..."`). This file is not in the repository.
