from datetime import datetime, timedelta, timezone

import duckdb
import folium
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

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
def get_parquet_site_merged(index_parquet, site, time_granularity="Day"):
    index_parquet = duckdb.read_parquet(index_parquet)

    query = """
    SELECT *,
        COALESCE(
            TRY_STRPTIME(Name, '%Y-%m-%dT%H_%M_%S.%fZ.mp3'),
            TRY_STRPTIME(Name, '%Y-%m-%dT%H_%M_%SZ.mp3'),
            STRPTIME(Name, '%Y-%m-%dT%H_%MZ.mp3'),
        ) AS datetime,
    FROM index_parquet
    WHERE MimeType = 'audio/mpeg'
    """

    data_q = duckdb.sql(query)
    data = data_q.fetchdf()

    # Parse the device ID
    data["short_device_id"] = (
        data["Path"]
            .str.split("/")         
            .str[-3]              
            .str.split("-")        
            .str[-1]                 
            .str[-8:]               
    )

    ####################################
    ##### CLEAN UP THE WHITE SPACES ####
    ####################################
    data['clean_id'] = data['short_device_id'].str.strip()
    site['clean_id'] = site['DeviceID'].str.strip()

    df_merged = pd.merge(
        data, site, left_on="clean_id", right_on="clean_id", how="left"
    )

    # Create a time dimension - choose one based on your data density
    df_merged["week"] = df_merged["datetime"].dt.isocalendar().week
    df_merged["month"] = df_merged["datetime"].dt.month
    df_merged["year_month"] = df_merged["datetime"].dt.strftime("%Y-%m")


    #########################################################################
    ##### MAKE SURE EACH COUNTRY IS REPRESENTED IN THE SHORT_DEVICE_ID ######
    #########################################################################
    country_map = {
    'proj_tabmon_NINA': 'Norway',
    'proj_tabmon_NINA_ES': 'Spain',
    'proj_tabmon_NINA_NL': 'Netherlands',
    'proj_tabmon_NINA_FR': 'France',
    }

    for code, country_name in country_map.items():
        df_merged.loc[df_merged['country'] == code, 'Country'] = country_name


    #####################
    # SOME MORE CLEANUP #
    #####################
    # keep everything *from* 1 Jan 2025 (inclusive)
    start = pd.Timestamp('2025-01-01', tz=df_merged["datetime"].dt.tz)
    df_merged = df_merged[df_merged["datetime"] >= start].copy()

    ##########################################################
    ##### ADD TIME GRANULARITY FOR SUMMARIZING THE DATA ######
    ##########################################################
    if time_granularity == "Day":
        df_merged["time_period"] = df_merged["datetime"].dt.to_period("D").astype(str)
        period_title = "Day"
    elif time_granularity == "Week":
        df_merged["time_period"] = df_merged["datetime"].dt.to_period("W").astype(str)
        period_title = "Week"
    else:
        df_merged["time_period"] = df_merged["datetime"].dt.to_period("M").astype(str)
        period_title = "Month"


    ###############################
    ##### DATA IN MATRIX FORM #####
    ###############################
    matrix_data = pd.crosstab(
        index=[df_merged["Country"], df_merged["device"]],
        columns=df_merged["time_period"],
        values=df_merged["datetime"],
        aggfunc="count",
    ).fillna(0)

    matrix_data = matrix_data.sort_index()

    return matrix_data, period_title


@st.cache_data(ttl=3600, show_spinner=False)
def get_status_table(parquet_file, site_info, offline_threshold_days=3):
    df_status = get_device_status_by_recorded_at(parquet_file, offline_threshold_days)
    if df_status.empty:
        return pd.DataFrame()

    site_info["short_device"] = site_info["DeploymentID"].apply(
        lambda x: x.split("_")[-1].strip().lower())

    merged = pd.merge(site_info, df_status, on="short_device", how="left")
    merged["status"] = merged["status"].fillna("Offline")
    merged["last_recorded"] = merged["recorded_at"]

    now = datetime.now(timezone.utc)
    merged["time_diff"] = (merged["last_recorded"] - now).abs()

    return merged


def show_map_dashboard(site_csv, parquet_file):
    site_info = load_site_info(site_csv)
    site_info = site_info[site_info["Active"] == True]
    df_status = get_status_table(parquet_file, site_info, offline_threshold_days=3)

    ################################################
    ###### PLOT THE MAP WITH DEVICE LOCATIONS ######
    ################################################
    st.title("Interactive Device Locations Map")

    m = folium.Map(
        location=[site_info["Latitude"].mean(), site_info["Longitude"].mean()],
        zoom_start=6,
    )
    marker_cluster = MarkerCluster().add_to(m)

    for _idx, row in df_status.iterrows():
        loc_txt = row['Cluster'] + ": " + row['Site']
        popup_text = (
            f"<b>DeviceID:</b> {row['DeviceID']}<br>"
            f"<b>Site:</b> {loc_txt}<br>"
            f"<b>Country:</b> {row['Country']}<br>"
        )
        # Choose icon color based on status.
        if row["status"] == "Online":
            marker_icon = folium.Icon(color="green", icon="microphone", prefix="fa")
        else:
            marker_icon = folium.Icon(color="red", icon="microphone", prefix="fa")

        folium.Marker(
            location=[row["Latitude"], row["Longitude"]],
            popup=popup_text,
            tooltip=row["Site"],
            icon=marker_icon,
        ).add_to(marker_cluster)

    st_folium(m, width=1200, height=800)

    #################################################
    ###### PLOT THE STATUS TABLE OF DEVICES #########
    #################################################

    # Select and format columns for better readability
    if not df_status.empty:
        display_cols = ["Cluster", "Site", "DeploymentID", "Country", "status", "last_recorded"]
        
        # Create a copy to avoid modifying the original dataframe
        status_display = df_status[display_cols].copy()
        
        # Format the last_recorded date
        status_display["last_recorded"] = status_display["last_recorded"].dt.strftime("%Y-%m-%d %H:%M")
        
        # Add a column showing days since last recording
        status_display["days_since_last"] = round((datetime.now(timezone.utc) - df_status["last_recorded"]).dt.days, 0)
        
        # Color-code the status
        def highlight_status(row):
            if row.status == 'Online':
                return ['background-color: #c6efcd'] * len(row)
            else:
                return ['background-color: #ffc7ce'] * len(row)
        
        # Display the styled table
        st.dataframe(
            status_display.style.apply(highlight_status, axis=1),
            use_container_width=True,
            height=400
        )
    else:
        st.info("No device status data available")

    #################################################
    #### PLOT THE MATRIX FOR FILE AVAILABILITY ######
    #################################################

    time_granularity = st.sidebar.radio(
        "Time Granularity", ["Day", "Week", "Month"], horizontal=True
    )

    matrix_data, period_title = get_parquet_site_merged(parquet_file, 
                                                        site_info, 
                                                        time_granularity)

    # Create custom y-tick labels
    ytick_labels = []
    prev_country = None

    for country, device in matrix_data.index:
        if country != prev_country:
            ytick_labels.append(f"{country} - {device}")
            prev_country = country
        else:
            ytick_labels.append(f"     {device}")  # indent to be more visual

    # Reverse the order so countries start from the top
    ytick_labels = ytick_labels[::-1]
    z_data = matrix_data.values[::-1]  # Also reverse the data to match labels
    x_labels = matrix_data.columns.tolist()

    fig = go.Figure(
        data=go.Heatmap(
            z=z_data,
            x=x_labels,
            y=ytick_labels,
            colorbar=dict(title="Number of recordings"),
            hoverongaps=False,
            hovertemplate=f"{period_title}: %{{x}}<br>Device: %{{y}}<br>Recordings: %{{z}}<extra></extra>",
        )
    )

    # Update layout
    fig.update_layout(
        title=" ",
        xaxis_title=period_title,  # Use the period_title variable here
        yaxis_title="Country - Device",
        height=max(500, len(matrix_data) * 20),
        width=1000,
        yaxis={"side": "left", "automargin": True},
        xaxis={"side": "bottom", "automargin": True},
        margin=dict(l=150),
    )

    st.write(
        f"### Number of audio recordings per device per {period_title}"
    )
    st.plotly_chart(fig)


