import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime


st.set_page_config(page_title="Temperature monitoring", layout="wide")


def get_current_season():
    month = datetime.now().month
    if month in (12, 1, 2):
        return "winter"
    elif month in (3, 4, 5):
        return "spring"
    elif month in (6, 7, 8):
        return "summer"
    else:
        return "autumn"


def get_temperature_sync(city, api_key):
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": api_key, "units": "metric"}
    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()
    return resp.status_code, data


def prepare_features(df):
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(["city", "timestamp"])

    df["rolling_mean"] = (
        df.groupby("city")["temperature"]
          .rolling(window=30, min_periods=1)
          .mean()
          .reset_index(level=0, drop=True)
    )

    df["rolling_mean_365"] = (
    df.groupby("city")["temperature"]
      .rolling(window=365, min_periods=1)
      .mean()
      .reset_index(level=0, drop=True)
    )

    df["season_mean"] = df.groupby(["city", "season"])["temperature"].transform("mean")
    df["season_std"] = df.groupby(["city", "season"])["temperature"].transform("std")

    df["is_anomaly"] = (
        (df["temperature"] < df["rolling_mean"] - 2 * df["season_std"]) |
        (df["temperature"] > df["rolling_mean"] + 2 * df["season_std"])
    )

    return df


def check_current_temp(dfp, city, current_temp):
    current_season = get_current_season()

    stats = dfp[(dfp["city"] == city) & (dfp["season"] == current_season)]
    if stats.empty:
        return None

    season_std = stats["season_std"].iloc[0]

    rolling_mean_current = (
        dfp[dfp["city"] == city]
          .sort_values("timestamp")["rolling_mean"]
          .iloc[-1]
    )

    lower = rolling_mean_current - 2 * season_std
    upper = rolling_mean_current + 2 * season_std

    if lower <= current_temp <= upper:
        status = "NORMAL"
    else:
        status = "ANOMALY"

    return {
        "season": current_season,
        "lower": lower,
        "upper": upper,
        "status": status,
        "rolling_mean_current": rolling_mean_current,
        "season_std": season_std,
    }


st.title("Temperature analysis and monitoring")

uploaded = st.sidebar.file_uploader("Upload temperature_data.csv", type=["csv"])
api_key = st.sidebar.text_input("OpenWeatherMap API key", type="password")
if uploaded is None:
    st.write("Upload temperature_data.csv to continue.")
    st.stop()

df = pd.read_csv(uploaded)

required_cols = {"city", "timestamp", "temperature", "season"}
if not required_cols.issubset(df.columns):
    st.error("CSV must contain columns: city, timestamp, temperature, season")
    st.stop()

dfp = prepare_features(df)

cities = sorted(dfp["city"].unique().tolist())
city = st.sidebar.selectbox("City", cities, index=0)
df_city = dfp[dfp["city"] == city].copy()

st.subheader("Descriptive statistics")
st.write(df_city["temperature"].describe())

st.subheader("Temperature time series and anomalies")
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df_city["timestamp"],
    y=df_city["temperature"],
    mode="lines",
    name="Daily temperature",
    opacity=0.6
))

fig.add_trace(go.Scatter(
    x=df_city["timestamp"],
    y=df_city["rolling_mean"],
    mode="lines",
    name="30-day rolling mean"
))

anom = df_city[df_city["is_anomaly"]]
fig.add_trace(go.Scatter(
    x=anom["timestamp"],
    y=anom["temperature"],
    mode="markers",
    name="Anomalies"
))

fig.update_layout(
    height=450,
    hovermode="x unified",
    xaxis_title="Date",
    yaxis_title="Temperature (°C)"
)

st.plotly_chart(fig, use_container_width=True)


st.subheader("Long-term temperature trend (365-day rolling mean)")

fig_long = go.Figure()
fig_long.add_trace(go.Scatter(
    x=df_city["timestamp"],
    y=df_city["rolling_mean_365"],
    mode="lines",
    name="365-day rolling mean"
))

fig_long.update_layout(
    height=450,
    hovermode="x unified",
    xaxis_title="Date",
    yaxis_title="Temperature (°C)"
)

st.plotly_chart(fig_long, use_container_width=True)

st.subheader("Seasonal profiles (mean ± std)")
season_stats = (
    dfp[dfp["city"] == city]
      .groupby("season")["temperature"]
      .agg(mean_temp="mean", std_temp="std", count="count")
      .reset_index()
)

order = ["winter", "spring", "summer", "autumn"]
season_stats["season"] = pd.Categorical(season_stats["season"], categories=order, ordered=True)
season_stats = season_stats.sort_values("season")

fig2 = px.bar(
    season_stats,
    x="season",
    y="mean_temp",
    error_y="std_temp",
    hover_data=["count"]
)
fig2.update_layout(height=450, xaxis_title="Season", yaxis_title="Temperature (°C)")
st.plotly_chart(fig2, use_container_width=True)

st.subheader("Current temperature (OpenWeatherMap)")
if api_key.strip() == "":
    st.write("Enter API key to show current temperature.")
else:
    status_code, data = get_temperature_sync(city, api_key)

    if status_code == 401:
        st.error(data)
    elif status_code != 200:
        st.error(data)
    else:
        current_temp = data["main"]["temp"]
        st.write(f"Current temperature in {data.get('name', city)}: {current_temp:.2f} °C")

        check = check_current_temp(dfp, city, current_temp)
        if check is None:
            st.write("No historical data for current season.")
        else:
            st.write(f"Season: {check['season']}")
            st.write(f"Normal range: [{check['lower']:.2f}, {check['upper']:.2f}] °C")
            st.write(check["status"])