import pandas as pd
import streamlit as st
import altair as alt


source_url = 'https://en.wikipedia.org/wiki/Fuel_economy_in_aircraft#Example_values'
dfs = pd.read_html(source_url)

# Remove irrelevant tables (could be improved)
dfs = [table for table in dfs if any(str(col).startswith("Fuel") for col in table.columns)]
for table in dfs:
    # Rename "Fuel efficiency per seat" to "Fuel per seat"
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
st.title('Aircraft Fuel Economy Tables')

# user selection of table
df_index = st.selectbox(
    "Select a table to view",
    options=range(len(dfs)),
    format_func=lambda x: f"Table {x}"
)
selected_df = dfs[df_index]

print(selected_df.dtypes)

# PLOT
st.subheader('Fuel per seat vs First flight date')

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
