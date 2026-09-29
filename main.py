from pathlib import Path

import pandas as pd
import streamlit as st

# Set the path to the data file
DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / "course_material"
    / "D2Dbook"
    / "data"
    / "reservoirs.csv"
)

# Load the data from the CSV file and changes the column names to English. The date_Id column is converted to a datetime type.
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)

    df = df.rename(columns={
        "dato_Id": "date_Id",
        "omrType": "region_type",
        "omrnr": "region_number",
        "iso_aar": "iso_year",
        "iso_uke": "iso_week",
        "fyllingsgrad": "filling_percentage",
        "kapasitet_TWh": "capacity_Twh",
        "fylling_TWh": "filling_Twh",
        "neste_Publiseringsdato": "next_publication_date",
        "fyllingsgrad_forrige_uke": "filling_percentage_previous_week",
        "endring_fyllingsgrad": "change_filling_percentage",
    })

    df["date_Id"] = pd.to_datetime(df["date_Id"])

    return df

# Main application, which sets the page configuration and defines the available pages in the Streamlit app. 
# The navigation is handled by the st.navigation function, which allows users to switch between different pages of the app.
if __name__ == "__main__":
    st.set_page_config(
        page_title="Reservoir data",
        page_icon=":bar_chart:",
        layout="wide",
    )

    pages = [
        st.Page("pages/1_Home_page.py", title="Home"),
        st.Page("pages/2_Data_table.py", title="Data table"),
        st.Page("pages/3_Plot.py", title="Plot"),
        st.Page("pages/4_Extra.py", title="Extra"),
    ]

    navigation = st.navigation(pages)
    navigation.run()