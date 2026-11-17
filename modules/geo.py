import json
from pathlib import Path

import streamlit as st
from shapely.geometry import Point, shape

# GeoJSON files made in the notebook (one per area type in Magasinstatistikk)
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
GEOJSON_FILES = {"EL": DATA_DIR / "price_areas.geojson", "VASS": DATA_DIR / "water_areas.geojson"}


@st.cache_data
def load_geojson(area_type):
    """Read the GeoJSON for price areas ('EL') or water areas ('VASS'). Cached: the files never change."""
    with open(GEOJSON_FILES[area_type], encoding="utf-8") as f:
        return json.load(f)


@st.cache_resource
def area_polygons(area_type):
    """Shapely polygons for each area, built once and reused for every click."""
    return [(f["properties"]["number"], shape(f["geometry"])) for f in load_geojson(area_type)["features"]]


def find_area(area_type, lat, lon):
    """Return the area number that contains the clicked point, or None if the click is outside all areas."""
    point = Point(lon, lat)                     # shapely uses (x, y) = (longitude, latitude)
    for number, polygon in area_polygons(area_type):
        if polygon.covers(point):               # covers() also counts points on the border
            return number
    return None