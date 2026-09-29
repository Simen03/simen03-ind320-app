import pandas as pd
import streamlit as st

from main import load_data

# Create a data table with one row for each column in the dataset.
st.title("Data table")
st.write("Table with one row for each column in the dataset.")

df = load_data()

first_month_period = df["date_Id"].dt.to_period("M").min()
first_month = df[df["date_Id"].dt.to_period("M") == first_month_period]

table_data = []

numeric_columns = [
    column
    for column in df.columns
    if pd.api.types.is_numeric_dtype(df[column])
    and first_month[column].notna().any()
]

for column in numeric_columns:
    table_data.append(
        {
            "Column": column,
            "First month trend": first_month[column].dropna().tolist(),
        }
    )

table_df = pd.DataFrame(table_data)

st.dataframe(
    table_df,
    column_config={
        "First month trend": st.column_config.LineChartColumn(
            "First month trend",
            width="medium",
        ),
    },
    hide_index=True,
    use_container_width=True,
)