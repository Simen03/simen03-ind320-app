import requests
import pandas as pd

URL = "https://biapi.nve.no/magasinstatistikk/api/Magasinstatistikk/"

Column_names = ({
    'dato_Id': 'date_Id',
    'omrType': 'region_type',
    'omrnr': 'region_number',
    'iso_aar': 'iso_year',
    'iso_uke': 'iso_week',
    'fyllingsgrad': 'filling_level',
    'kapasitet_TWh': 'capacity_Twh',
    'fylling_TWh': 'filling_Twh',
    'neste_Publiseringsdato': 'next_publication_date',
    'fyllingsgrad_forrige_uke': 'filling_level_previous_week',
    'endring_fyllingsgrad': 'change_filling_level',
})  

Values = ['filling_level', 'capacity_Twh', 'filling_Twh',
           'filling_level_previous_week', 'change_filling_level']

def fetch_reservoirs():
    response = requests.get(URL + "HentOffentligData", timeout=30)
    response.raise_for_status()          # raise an error if NVE is unavailable
    df = pd.DataFrame(response.json()).rename(columns=Column_names)
    df["date_id"] = pd.to_datetime(df["date_Id"])
    return df

def areas():
    response = requests.get(URL + "HentOmr%C3%A5der", timeout=30)
    response.raise_for_status()
    groups = response.json()[0]          # unwrap the single-element list
    frames = [pd.DataFrame(groups[key]) for key in ("land", "elspot", "vassdrag")]
    return pd.concat(frames, ignore_index=True)

def select_area(df, region_type="NO", region_number=0):
    mask = (df["region_type"] == region_type) & (df["region_number"] == region_number)
    return df[mask].sort_values("date_id").set_index("date_id")[Values]

def pivot_filling(df, region_type):

    subset = df[df["region_type"] == region_type]
    wide = subset.pivot_table(index="date_id", columns="region_number",
                               values="filling_level", aggfunc="mean").sort_index()
    # Make the column names readable: EL 1 -> "NO1", VASS 1 -> "VASS 1", NO 0 -> "Norway"
    if region_type == "EL":
        wide.columns = [f"NO{n}" for n in wide.columns]
    elif region_type == "NO":
        wide.columns = ["Norway"]
    else:
        wide.columns = [f"{region_type} {n}" for n in wide.columns]
    return wide