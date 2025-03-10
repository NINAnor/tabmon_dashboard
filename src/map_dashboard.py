import re
from datetime import datetime, timedelta, timezone

import duckdb
import folium
import pandas as pd
import streamlit as st
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

from utils.data_loader import load_site_info, parse_file_datetime


def get_device_status_by_recorded_at(parquet_file, offline_threshold_days=16):
    # Load the full audio index using DuckDB.
    df = duckdb.execute("SELECT * FROM read_parquet(?)", (parquet_file,)).df()

    # Parse the recording time from the 'file' column.
    df["recorded_at"] = df["Name"].apply(parse_file_datetime)
    df = df.dropna(subset=["recorded_at"])
    if df.empty:
        return pd.DataFrame()

    # Normalize and extract the short device id
    # (last 8 characters, lower-case, stripped).
    df["short_device"] = df["device"].apply(lambda x: x[-8:].strip().lower())

    # Group by short device and get the maximum (latest) recorded_at time.
    df_latest = df.groupby("short_device")["recorded_at"].max().reset_index()

    now = datetime.now(timezone.utc)
    threshold = timedelta(days=offline_threshold_days)

    df_latest["status"] = df_latest["recorded_at"].apply(
        lambda t: "Offline" if now - t > threshold else "Online"
    )
    return df_latest


@st.cache_data(show_spinner=False)
def get_status_table(parquet_file, site_csv, offline_threshold_days=5):
    """
    Merge device status (from the audio index) with site info,
    using normalized short device IDs.
    """
    df_status = get_device_status_by_recorded_at(parquet_file, offline_threshold_days)
    if df_status.empty:
        return pd.DataFrame()

    # Load site info.
    site_info = load_site_info(site_csv)

    # Normalize the short device id in site_info.
    site_info["short_device"] = site_info["deviceID"].apply(
        lambda x: x.split("_")[-1].strip().lower()
        if "_" in x
        else x[-8:].strip().lower()
    )

    merged = pd.merge(site_info, df_status, on="short_device", how="left")
    merged["status"] = merged["status"].fillna("Offline")
    merged["last_recorded"] = merged["recorded_at"]

    now = datetime.now(timezone.utc)
    merged["time_diff"] = (merged["last_recorded"] - now).abs()

    return merged


def show_map_dashboard(site_csv, parquet_file):
    # Load site_info.
    site_info = load_site_info(site_csv)

    df_status = get_status_table(parquet_file, site_csv, offline_threshold_days=16)

    st.title("Interactive Device Locations Map")

    m = folium.Map(
        location=[site_info["latitude"].mean(), site_info["longitude"].mean()],
        zoom_start=6,
    )
    marker_cluster = MarkerCluster().add_to(m)

    for _idx, row in df_status.iterrows():
        popup_text = (
            f"<b>DeviceID:</b> {row['deviceID']}<br>"
            f"<b>Site:</b> {row['site']}<br>"
            f"<b>Country:</b> {row['country']}<br>"
        )
        # Choose icon color based on status.
        if row["status"] == "Online":
            marker_icon = folium.Icon(color="green", icon="microphone", prefix="fa")
        else:
            marker_icon = folium.Icon(color="red", icon="microphone", prefix="fa")

        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=popup_text,
            tooltip=row["site"],
            icon=marker_icon,
        ).add_to(marker_cluster)

    st_folium(m, width=1200, height=800)

    st.write("### Device Status (no data for more than 3 days)")
    st.dataframe(df_status[["site", "country", "status", "time_diff"]])
