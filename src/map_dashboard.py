from datetime import datetime, timedelta, timezone

import duckdb
import folium
import pandas as pd
import streamlit as st
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import plotly.graph_objects as go

from utils.data_loader import load_site_info, parse_file_datetime


def get_device_status_by_recorded_at(parquet_file, offline_threshold_days=16):
    df = duckdb.execute("SELECT * FROM read_parquet(?)", (parquet_file,)).df()
    df["recorded_at"] = df["Name"].apply(parse_file_datetime)
    df = df.dropna(subset=["recorded_at"])
    if df.empty:
        return pd.DataFrame()

    # extract the device ID (last 8 characters, lower-case, stripped).
    df["short_device"] = df["device"].apply(lambda x: x[-8:].strip().lower())

    df_latest = df.groupby("short_device")["recorded_at"].max().reset_index()

    now = datetime.now(timezone.utc)
    threshold = timedelta(days=offline_threshold_days)

    df_latest["status"] = df_latest["recorded_at"].apply(
        lambda t: "Offline" if now - t > threshold else "Online"
    )
    return df_latest

@st.cache_data(ttl=3600, show_spinner=False)
def get_parquet_site_merged(index_parquet, site):

    index_parquet = duckdb.read_parquet(index_parquet)  

    query = """
    SELECT *,
        COALESCE(
            TRY_STRPTIME(Name, '%Y-%m-%dT%H_%M_%S.%fZ.mp3'),
            TRY_STRPTIME(Name, '%Y-%m-%dT%H_%M_%SZ.mp3'),
            STRPTIME(Name, '%Y-%m-%dT%H_%MZ.mp3'),
        ) AS datetime,
        REGEXP_EXTRACT(device, '10000000(.+)$', 1) AS short_device_id
    FROM index_parquet
    WHERE MimeType = 'audio/mpeg'
    """

    data_q = duckdb.sql(query)
    data = data_q.fetchdf()

    site['short_device_id'] = site["9. DeploymentID: countryCode_deploymentNumber_DeviceID (e.g. NO_1_ 7ft35sm)"].str.split('_').str[-1]
    site = site.drop_duplicates("short_device_id")
    print(site)
    df_merged = pd.merge(
        data,
        site,
        left_on='short_device_id',
        right_on='short_device_id',
        how='left'
    )

    # Create a time dimension - choose one based on your data density
    df_merged['week'] = df_merged['datetime'].dt.isocalendar().week
    df_merged['month'] = df_merged['datetime'].dt.month
    df_merged['year_month'] = df_merged['datetime'].dt.strftime('%Y-%m')

    df_merged = df_merged.rename(columns={
        "4. Latitude: decimal degree, WGS84 (ex: 64.65746)": "latitude",
        "5. Longitude: decimal degree, WGS84 (ex: 5.37463)": "longitude"
    })

    return df_merged


@st.cache_data(ttl=3600, show_spinner=False)
def get_status_table(parquet_file, site_csv, offline_threshold_days=3):
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
    site_info = load_site_info(site_csv)
    df_status = get_status_table(parquet_file, site_csv, offline_threshold_days=3)
    df_merged = get_parquet_site_merged(parquet_file, site_info)

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

    time_granularity = st.sidebar.radio(
        "Time Granularity", 
        ["Day", "Week", "Month"], 
        horizontal=True
    )

    df_merged = df_merged[df_merged['datetime'] >= pd.Timestamp('2024-04-01')]

    if time_granularity == "Day":
        df_merged['time_period'] = df_merged['datetime'].dt.to_period('D').astype(str)
        period_title = "Day"
    elif time_granularity == "Week":
        df_merged['time_period'] = df_merged['datetime'].dt.to_period('W').astype(str)
        period_title = "Week"
    else:
        df_merged['time_period'] = df_merged['datetime'].dt.to_period('M').astype(str)
        period_title = "Month"

    matrix_data = pd.crosstab(
        index=[df_merged['country_y'], df_merged['device']],
        columns=df_merged['time_period'],
        values=df_merged['datetime'],
        aggfunc='count'
    ).fillna(0)

    matrix_data = matrix_data.sort_index()

    ytick_labels = []
    prev_country = None

    for country, device in matrix_data.index:
        if country != prev_country:
            ytick_labels.append(f"{country} - {device}")
            prev_country = country
        else:
            ytick_labels.append(f"     {device}") # indent to be more visual

    z_data = matrix_data.values
    x_labels = matrix_data.columns.tolist()

    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=x_labels,
        y=ytick_labels,
        #colorscale='Blues',
        colorbar=dict(title='Number of recordings'),
        hoverongaps=False,
        hovertemplate='{period_title}: %{x}<br>Device: %{y}<br>Recordings: %{z}<extra></extra>'
    ))

    # Update layout
    fig.update_layout(
        title=' ',
        xaxis_title='{period_title} - Week',
        yaxis_title='Country - Device',
        height=max(500, len(matrix_data) * 20),  # Dynamic height based on number of rows
        width=1000,
        yaxis={'side': 'left', 'automargin': True},
        xaxis={'side': 'bottom', 'automargin': True},
        margin=dict(l=150)  # Add left margin for long labels
    )

    st.write("### Number of audio recordings per device per {time_period} - Change time granularity in the sidebar!")
    st.plotly_chart(fig)

    #st.write("### Device Status (no data for more than 3 days)")
    #st.dataframe(df_status[["site", "country", "status", "time_diff"]])
            
