import streamlit as st
import pandas as pd
import plotly.express as px
import json

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(page_title="India AQI Dashboard", layout="wide")

# -------------------------------
# LOAD DATA
# -------------------------------
aqi_df = pd.read_csv("aqi_data.csv")
ev_df = pd.read_csv("ev_data.csv")

# -------------------------------
# DATA CLEANING
# -------------------------------
aqi_df["aqi_value"] = pd.to_numeric(aqi_df["aqi_value"], errors="coerce")
aqi_df = aqi_df.dropna(subset=["aqi_value"])

# FIX DATE WARNING
aqi_df["date"] = pd.to_datetime(
    aqi_df["date"],
    format="%d-%m-%Y",
    errors="coerce"
)

aqi_df["year"] = aqi_df["date"].dt.year

# -------------------------------
# AQI AGGREGATION
# -------------------------------
state_avg = aqi_df.groupby("state")["aqi_value"].mean().reset_index()
state_avg.rename(columns={"aqi_value": "avg_aqi"}, inplace=True)

# -------------------------------
# EV FILTERING
# -------------------------------
ev_df = ev_df[ev_df["fuel"].str.contains("EV", case=False, na=False)]

ev_state = ev_df.groupby("state")["value"].sum().reset_index()
ev_state.rename(columns={"value": "ev_count"}, inplace=True)

# -------------------------------
# MERGE
# -------------------------------
merged_df = pd.merge(state_avg, ev_state, on="state", how="inner")

# -------------------------------
# AQI CATEGORY
# -------------------------------
def categorize_aqi(aqi):
    if aqi <= 50:
        return "Good"
    elif aqi <= 100:
        return "Moderate"
    elif aqi <= 150:
        return "Unhealthy for Sensitive"
    else:
        return "Unhealthy"

merged_df["aqi_category"] = merged_df["avg_aqi"].apply(categorize_aqi)

# -------------------------------
# YEAR TREND
# -------------------------------
yearly_trend = aqi_df.groupby("year")["aqi_value"].mean().reset_index()

# -------------------------------
# LOAD INDIA GEOJSON
# -------------------------------
with open("india_states.geojson") as f:
    india_geo = json.load(f)

# -------------------------------
# SIDEBAR
# -------------------------------
st.sidebar.header("Filters")

states = st.sidebar.multiselect(
    "Select State",
    options=merged_df["state"].unique(),
    default=merged_df["state"].unique()
)

filtered_df = merged_df[merged_df["state"].isin(states)]

if filtered_df.empty:
    st.warning("No data available")
    st.stop()

# -------------------------------
# KPI CALCULATIONS
# -------------------------------
most_polluted_global = merged_df.loc[merged_df["avg_aqi"].idxmax()]
cleanest_global = merged_df.loc[merged_df["avg_aqi"].idxmin()]
avg_aqi_global = merged_df["avg_aqi"].mean()

most_polluted_filtered = filtered_df.loc[filtered_df["avg_aqi"].idxmax()]
cleanest_filtered = filtered_df.loc[filtered_df["avg_aqi"].idxmin()]
avg_aqi_filtered = filtered_df["avg_aqi"].mean()

# -------------------------------
# TITLE
# -------------------------------
st.title("🇮🇳 India Air Quality & EV Analysis Dashboard")

# -------------------------------
# FILTERED KPIs
# -------------------------------
st.subheader("📊 Filtered Insights")

col1, col2, col3 = st.columns(3)

col1.metric("Average AQI", round(avg_aqi_filtered, 2))
col2.metric("Most Polluted", most_polluted_filtered["state"])
col3.metric("Cleanest", cleanest_filtered["state"])

st.divider()

# -------------------------------
# GLOBAL KPIs
# -------------------------------
st.subheader("🌍 Overall India Insights")

col4, col5, col6 = st.columns(3)

col4.metric("Overall Avg AQI", round(avg_aqi_global, 2))
col5.metric("Most Polluted", most_polluted_global["state"])
col6.metric("Cleanest", cleanest_global["state"])

# -------------------------------
# SCATTER PLOT
# -------------------------------
st.subheader("EV Adoption vs Air Quality")

fig = px.scatter(
    filtered_df,
    x="ev_count",
    y="avg_aqi",
    color="aqi_category",
    hover_name="state",
    title="EV Adoption vs AQI"
)

st.plotly_chart(fig, width="stretch")

# -------------------------------
# POLLUTED vs CLEAN
# -------------------------------
col7, col8 = st.columns(2)

with col7:
    st.subheader("Top Polluted States")

    top10 = filtered_df.sort_values("avg_aqi", ascending=False).head(10)

    fig2 = px.bar(
        top10,
        x="avg_aqi",
        y="state",
        orientation="h",
        color="avg_aqi",
        color_continuous_scale="Reds"
    )

    st.plotly_chart(fig2, width="stretch")

with col8:
    st.subheader("Top Cleanest States")

    clean10 = filtered_df.sort_values("avg_aqi", ascending=True).head(10)

    fig3 = px.bar(
        clean10,
        x="avg_aqi",
        y="state",
        orientation="h",
        color="avg_aqi",
        color_continuous_scale="Greens_r"
    )

    st.plotly_chart(fig3, width="stretch")

# -------------------------------
# AQI CATEGORY DISTRIBUTION
# -------------------------------
st.subheader("AQI Category Distribution")

fig4 = px.histogram(
    filtered_df,
    x="aqi_category",
    color="aqi_category"
)

st.plotly_chart(fig4, width="stretch")

# -------------------------------
# INDIA MAP
# -------------------------------
st.subheader("India AQI Map")

fig_map = px.choropleth(
    merged_df,
    geojson=india_geo,
    featureidkey="properties.NAME_1",
    locations="state",
    color="avg_aqi",
    color_continuous_scale="Reds"
)

fig_map.update_geos(fitbounds="locations", visible=False)

st.plotly_chart(fig_map, width="stretch")

# -------------------------------
# YEAR TREND
# -------------------------------
st.subheader("AQI Trend Over Years")

fig_trend = px.line(
    yearly_trend,
    x="year",
    y="aqi_value",
    markers=True
)

st.plotly_chart(fig_trend, width="stretch")