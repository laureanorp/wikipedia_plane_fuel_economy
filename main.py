import pandas as pd
import streamlit as st
import altair as alt
import requests
from bs4 import BeautifulSoup


source_url = 'https://en.wikipedia.org/wiki/Fuel_economy_in_aircraft#Example_values'
dfs = pd.read_html(source_url)

# BS magic to match titles with tables
response = requests.get(source_url)
soup = BeautifulSoup(response.text, 'html.parser')

table_titles = []
current_title = None
for tag in soup.select("div.mw-heading, table.wikitable"):
    if "mw-heading" in tag.get("class", []):
        h_tag = tag.find(['h2', 'h3', 'h4'])
        if h_tag:
            current_title = h_tag.get_text(strip=True)
    elif tag.name == "table" and "wikitable" in tag.get("class", []):
        table_titles.append(current_title or "Untitled")

# Filter tables (remove irrelevant ones)
filtered_dfs = []
filtered_titles = []

for table, title in zip(dfs, table_titles):
    if any(str(col).startswith("Fuel") for col in table.columns):
        filtered_dfs.append(table)
        filtered_titles.append(title)

dfs = filtered_dfs
table_titles = filtered_titles

# Data cleaning
for table in dfs:
    # Rename "Fuel efficiency per seat" (some tables used this name) to "Fuel per seat"
    if "Fuel efficiency per seat" in table.columns:
        table.rename(columns={"Fuel efficiency per seat": "Fuel per seat"}, inplace=True)
    # Prepare new column for data representation
    if "Fuel per seat" in table.columns:
        table["Fuel per seat (L/100 km)"] = (
            table["Fuel per seat"]
            .astype(str)
            .str.extract(r'([\d.]+)\s*L/100\s*km')
            .astype(float)
        )
        # Remove wikipedia footnotes
        table['Fuel per seat'] = table["Fuel per seat"].str.replace(r'\[\d+\]', '', regex=True)
    # Sort by date by default
    table.sort_values(by="First flight", ascending=True, inplace=True)

# Streamlit app header
st.title('Plane Fuel Economy ✈️')

# User chooses the data to view
df_index = st.selectbox(
    "Select a category to view",
    options=range(len(dfs)),
    format_func=lambda x: table_titles[x] if x < len(table_titles) else f"Table {x}"
)
selected_df = dfs[df_index]

# PLOT
st.subheader(f'Fuel per seat vs First flight date ({table_titles[df_index]})')

# Scatter plot
chart_df = selected_df.copy()
min_year = int(chart_df["First flight"].min())
max_year = int(chart_df["First flight"].max())
scatter = alt.Chart(chart_df).mark_circle(size=80).encode(
        x=alt.X(
            "First flight:Q",
            title="First flight year",
            scale=alt.Scale(domain=[min_year, max_year]),
            axis=alt.Axis(format=".0f"),
        ),
        y=alt.Y(
            "Fuel per seat (L/100 km):Q",
            title="Fuel per seat (L/100 km)",
        ),
        tooltip=["Model", "First flight", "Fuel per seat (L/100 km)"]
    )

# Trend line
trend = alt.Chart(chart_df).transform_loess(
    "First flight", "Fuel per seat (L/100 km)", bandwidth=0.5
).mark_line(color='red').encode(
    x="First flight:Q",
    y="Fuel per seat (L/100 km):Q"
)

st.altair_chart(scatter + trend, use_container_width=True)

st.subheader(f'Data source · [Wikipedia]({source_url})')

# Table visualization, removing "Fuel per seat (L/100 km)" as it's redundant
st.dataframe(selected_df, hide_index=True, column_config={"Fuel per seat (L/100 km)": None})
