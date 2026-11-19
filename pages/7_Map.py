import copy

import folium
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from branca.colormap import LinearColormap
from streamlit_folium import st_folium
import plotly.express as px
from modules.elevation import elevation_points, get_elevation

from modules.controls import AREA_NUMBERS, area_label, get_selection, select_area_on_map
from modules.geo import find_area, load_geojson
from modules.reservoir_data import load_reservoirs
from modules.style import COLORS, LAYOUT, page_header
from modules.weather import WEATHER_VARS, load_weather

page_header("Map and area selection", "Explore",
            "Colour the areas by filling level or weather for a chosen week. "
            "Click an area to select it - the selection is used on the other pages.")

# Global selections: the time interval limits which weeks can be chosen on the map
start, end, area_type, _ = get_selection()

df = load_reservoirs(start, end)

# ---------- Local controls, grouped in a frame ----------
with st.container(border=True):
    c1, c2 = st.columns([3, 2])
    colour_by = c1.radio("Colour areas by", ["Price area", "Water area", "Weather property"],
                         horizontal=True, key="map_colour_by")
    if colour_by == "Weather property":
        prop = c2.selectbox("Weather property", list(WEATHER_VARS),
                            format_func=lambda v: WEATHER_VARS[v][0], key="map_property")

    # Time selector: one of the weeks in the global interval (weeks end on Sunday, as in Magasinstatistikk).
    # Stored in the session state, so the forecast page can use the same time.
    weeks = list(pd.to_datetime(sorted(df["date_Id"].unique())))
    if not weeks:
        st.warning("No data in the selected interval.")
        st.stop()
    saved_week = st.session_state.get("map_week")
    week = st.select_slider("Week", options=weeks,
                            value=saved_week if saved_week in weeks else weeks[-1],
                            format_func=lambda d: f"Week {d.isocalendar().week}, {d:%d %b %Y}")
    show_elevation = st.checkbox("Show elevation of sample points in the selected area (open-meteo elevation API)",
                            key="map_elevation")
    st.session_state["map_week"] = week

# Which areas to draw: price areas or water areas. For weather, follow the global area type.
if colour_by == "Price area":
    map_type = "EL"
elif colour_by == "Water area":
    map_type = "VASS"
else:
    map_type = area_type if area_type in ("EL", "VASS") else "EL"   # Norway total has no sub-areas

# ---------- Weekly time series for every area ----------
series = {}                                     # area number -> weekly series
if colour_by in ("Price area", "Water area"):
    label, unit = "Filling level", "%"
    for number, g in df[df["region_type"] == map_type].groupby("region_number"):
        series[number] = g.set_index("date_Id")["filling_level"] * 100
else:
    label, unit = WEATHER_VARS[prop]
    try:
        for number in AREA_NUMBERS[map_type]:
            w = load_weather(area_label(map_type, number), week.year, n_locations=2)[prop]
            w.index = w.index.tz_convert("Europe/Oslo").tz_localize(None)    # UTC -> Norwegian time
            # Weekly total for precipitation, weekly mean for the other properties
            weekly = w.resample("W-SUN")
            series[number] = weekly.sum() if prop == "precipitation" else weekly.mean()
    except Exception as e:
        st.error(f"Could not download weather data from open-meteo: {e}")
        st.stop()

# Value for the chosen week in each area (areas without data are left out)
values = {n: s.get(week) for n, s in series.items() if pd.notna(s.get(week))}
selected = st.session_state.get("region_number") if st.session_state.get("area_type") == map_type else None

# ---------- Map ----------
vmin = min(values.values()) if values else 0
vmax = max(values.values()) if values else 1
cmap = LinearColormap(["#deebf7", COLORS["main"]], vmin=vmin, vmax=vmax if vmax > vmin else vmin + 1,
                      caption=f"{label} ({unit})")


# Copy the cached GeoJSON before adding values to it (cached objects must not be changed)
geojson = copy.deepcopy(load_geojson(map_type))
for feature in geojson["features"]:
    v = values.get(feature["properties"]["number"])
    feature["properties"]["value"] = "no data" if v is None else f"{v:.1f} {unit}"


def style(feature):
    """Transparent fill coloured by value; thicker outline in a contrast colour for the selected area."""
    number = feature["properties"]["number"]
    v = values.get(number)
    is_selected = number == selected
    return {
        "fillColor": cmap(v) if v is not None else "#cccccc",
        "fillOpacity": 0.55,
        "color": COLORS["outlier"] if is_selected else "#34495e",
        "weight": 4 if is_selected else 1,
    }


# OpenStreetMap tiles do not need an API key
m = folium.Map(location=[64.5, 13], zoom_start=4, tiles="OpenStreetMap")
folium.GeoJson(
    geojson,
    style_function=style,
    tooltip=folium.GeoJsonTooltip(fields=["region_id", "value"], aliases=["Area", "Value"]),
).add_to(m)
cmap.add_to(m)

# ---------- Elevation of sample points (bonus: open-meteo elevation API) ----------
points = None
if show_elevation and selected is not None:
    try:
        points = elevation_points(area_label(map_type, selected))
    except Exception as e:
        st.warning(f"Could not get elevation data from open-meteo: {e}")

if points is not None:
    # Colour scale from low (green) to high (brown/white), like a terrain map
    elev_cmap = LinearColormap(["#1a9850", "#fee08b", "#8c510a", "#f7f7f7"],
                               vmin=points["elevation"].min(), vmax=points["elevation"].max(),
                               caption="Elevation of sample points (m)")
    for _, pt in points.iterrows():
        folium.CircleMarker(
            location=[pt["lat"], pt["lon"]], radius=4, weight=1,
            color=elev_cmap(pt["elevation"]), fill=True, fill_opacity=0.9,
            tooltip=f"{pt['elevation']:.0f} m",
        ).add_to(m)
    elev_cmap.add_to(m)

map_col, side_col = st.columns([3, 2])
with map_col:
    # Only the last click is returned, so the app does not rerun when the map is moved or zoomed
    out = st_folium(m, height=520, use_container_width=True, returned_objects=["last_clicked"], key="map")

# ---------- Handle clicks ----------
# Only react to a NEW click; st_folium returns the last click again on every rerun
clicked = (out or {}).get("last_clicked")
if clicked and clicked != st.session_state.get("last_map_click"):
    st.session_state["last_map_click"] = clicked
    number = find_area(map_type, clicked["lat"], clicked["lng"])
    if number is not None:
        select_area_on_map(map_type, number)                                # redraw with the new outline and plots

# ---------- Side panel: selected area with its time series ----------
with side_col:
    if selected is None:
        st.info("Click an area on the map to select it.")
    else:
        st.metric(f"Selected area: {area_label(map_type, selected)}",
                  "no data" if selected not in values else f"{values[selected]:.1f} {unit}")

        # Elevation at the last clicked point, and mean elevation of the sample points
        click = st.session_state.get("last_map_click")
        e1, e2 = st.columns(2)
        if click:
            try:
                height = get_elevation((click["lat"],), (click["lng"],))[0]
                e1.metric("Elevation at clicked point", f"{height:.0f} m")
            except Exception:
                e1.metric("Elevation at clicked point", "–")
        if points is not None:
            e2.metric("Mean elevation, sample points", f"{points['elevation'].mean():.0f} m")

        # Time series of the selected area, with a dashed line at the chosen week
        if selected in series:
            s = series[selected]
            fig_line = go.Figure(go.Scatter(x=s.index, y=s.values, mode="lines",
                                            line=dict(color=COLORS["main"])))
            fig_line.add_vline(x=week, line=dict(color=COLORS["outlier"], dash="dash"))
            fig_line.update_layout(**LAYOUT, height=400, yaxis_title=f"{label} ({unit})",
                                   title=f"{label} over time")
            st.plotly_chart(fig_line)
            st.caption("The dashed line marks the chosen week.")

# ---------- Distribution of elevation in the selected area ----------
if points is not None:
    fig_elev = px.histogram(points, x="elevation", nbins=20, color_discrete_sequence=[COLORS["main"]],
                            labels={"elevation": "Elevation (m)"})
    fig_elev.update_layout(**LAYOUT, height=280, yaxis_title="Number of points",
                           title=f"Elevation of {len(points)} sample points in {area_label(map_type, selected)}")
    st.plotly_chart(fig_elev)