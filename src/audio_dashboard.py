import re
from datetime import datetime, timezone

import requests

import duckdb
import streamlit as st

from utils.data_loader import load_site_info, parse_file_datetime


def get_filtered_audio_data_by_device(parquet_file, short_device_id):
    query = """
        SELECT *
        FROM read_parquet(?)
        WHERE RIGHT(device, 8) = ?
    """
    df = duckdb.execute(query, (parquet_file, short_device_id)).df()
    return df


def show_audio_dashboard(parquet_file, site_csv):
    site_info = load_site_info(site_csv)

    # Select country
    countries = site_info["country"].unique().tolist()
    selected_country = st.sidebar.selectbox("Select Country", sorted(countries))

    # Select site in a country
    filtered_sites = site_info[site_info["country"] == selected_country]
    sites = filtered_sites["site"].unique().tolist()
    selected_site = st.sidebar.selectbox("Select Site", sorted(sites))

    # Filter site_info to the selected site.
    site_data = filtered_sites[filtered_sites["site"] == selected_site]
    if site_data.empty:
        st.error("No site data found for the selected site.")
        return
    record = site_data.iloc[0]

    st.title(f"Audio Dashboard for Site: {selected_site}")
    st.write("### Site Details")
    st.markdown(f"**Country:** {record.get('country', 'N/A')}")
    st.markdown(f"**Site:** {record.get('site', 'N/A')}")
    st.markdown(f"**Device ID:** {record.get('deviceID', 'N/A')}")

    # Extract short device id
    full_device_id = record.get("deviceID", "")
    if "_" in full_device_id:
        short_device_id = full_device_id.split("_")[-1].strip()
    else:
        short_device_id = full_device_id[-8:]
    st.write(f"**Short Device ID:** {short_device_id}")

    # Query audio data for the selected site's device.
    df = get_filtered_audio_data_by_device(parquet_file, short_device_id)
    if df.empty:
        st.write("No audio files found for this site/device.")
        return

    # Let the user select a recording date and time using separate inputs.
    selected_date = st.sidebar.date_input(
        "Select Recording Date", value=datetime.utcnow().date()
    )
    selected_time = st.sidebar.time_input(
        "Select Recording Time", value=datetime.utcnow().time()
    )
    selected_datetime = datetime.combine(selected_date, selected_time).replace(
        tzinfo=timezone.utc
    )

    # Parse the recording time from the file name.
    df["recorded_at"] = df["Name"].apply(parse_file_datetime)
    df = df.dropna(subset=["recorded_at"])
    if df.empty:
        st.write("No valid recording timestamps could be determined.")
        return

    # Compute the absolute time difference between each file's recorded time
    # and the selected datetime.
    df["time_diff"] = (df["recorded_at"] - selected_datetime).abs()

    # Sort the dataframe by time difference and take the top 10 closest files.
    closest_df = df.sort_values(by="time_diff").head(10)

    st.write(f"**Selected Time:** {selected_datetime}")
    st.write("### 10 Closest Files to Specified Date")
    st.dataframe(closest_df[["Name", "recorded_at", "time_diff", "Path"]])

    # Let the user select a file to play from the 10 closest files.
    selected_file = st.selectbox("Select a File to Play", closest_df["Path"].tolist())
    if selected_file:
        file_url = f"/data/{selected_file}"
        st.write(f"[{file_url}]({file_url})")
        audio = requests.get(f"http://rclone:8081/{file_url}")
        st.audio(audio.content, audio.headers['content-type'])
        #st.html(f'<audio src="{file_url}" controls />')