import streamlit as st
import duckdb
import pandas as pd
import re
from datetime import datetime, timezone
from utils.data_loader import load_site_info

def parse_file_datetime(file_str):
    """
    Parse the datetime from a file name like:
    "2024-05-24T15_24_05.762Z.mp3"
    and return a tz-aware datetime object in UTC.
    """
    pattern = re.compile(
        r"(?P<date>\d{4}-\d{2}-\d{2}T)"
        r"(?P<hour>\d{2})_(?P<minute>\d{2})_(?P<second>\d{2}\.\d+)"
        r"Z"
    )
    m = pattern.search(file_str)
    if m:
        iso_str = m.group("date") + m.group("hour") + ":" + m.group("minute") + ":" + m.group("second") + "Z"
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt
    return None

def get_filtered_audio_data_by_device(parquet_file, short_device_id):
    """
    Uses DuckDB to query the audio index Parquet file for rows whose 'device'
    field (when taking the RIGHT 8 characters) matches the given short device id.
    """
    query = f"""
        SELECT *
        FROM read_parquet('{parquet_file}')
        WHERE RIGHT(device, 8) = '{short_device_id}'
    """
    df = duckdb.query(query).to_df()
    return df

def show_audio_dashboard(parquet_file, site_csv):
    # Load site_info from CSV.
    site_info = load_site_info(site_csv)
    
    # Let the user select a country.
    countries = site_info['country'].unique().tolist()
    selected_country = st.sidebar.selectbox("Select Country", sorted(countries))
    
    # Then filter site_info by the selected country and let the user select a site.
    filtered_sites = site_info[site_info['country'] == selected_country]
    sites = filtered_sites['site'].unique().tolist()
    selected_site = st.sidebar.selectbox("Select Site", sorted(sites))
    
    # Filter site_info to the selected site.
    site_data = filtered_sites[filtered_sites['site'] == selected_site]
    if site_data.empty:
        st.error("No site data found for the selected site.")
        return
    record = site_data.iloc[0]
    
    st.title(f"Audio Dashboard for Site: {selected_site}")
    st.write("### Site Details")
    st.markdown(f"**Country:** {record.get('country', 'N/A')}")
    st.markdown(f"**Site:** {record.get('site', 'N/A')}")
    st.markdown(f"**Device ID:** {record.get('deviceID', 'N/A')}")
    
    # Extract a short device id from the deviceID.
    full_device_id = record.get('deviceID', '')
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
    selected_date = st.sidebar.date_input("Select Recording Date", value=datetime.utcnow().date())
    selected_time = st.sidebar.time_input("Select Recording Time", value=datetime.utcnow().time())
    selected_datetime = datetime.combine(selected_date, selected_time).replace(tzinfo=timezone.utc)
    
    # Parse the recording time from the file name.
    df['recorded_at'] = df['file'].apply(parse_file_datetime)
    df = df.dropna(subset=['recorded_at'])
    if df.empty:
        st.write("No valid recording timestamps could be determined.")
        return
    
    # Compute the absolute time difference between each file's recorded time and the selected datetime.
    df['time_diff'] = (df['recorded_at'] - selected_datetime).abs()
    
    # Sort the dataframe by time difference and take the top 10 closest files.
    closest_df = df.sort_values(by='time_diff').head(10)
    
    st.write(f"**Selected Time:** {selected_datetime}")
    st.write("### 10 Closest Files to Specified Date")
    st.dataframe(closest_df[['file', 'recorded_at', 'time_diff', 'Path']])
    
    # Let the user select a file to play from the 10 closest files.
    selected_file = st.selectbox("Select a File to Play", closest_df['Path'].tolist())
    if selected_file:
        file_url = f"http://localhost:8081/{selected_file}"
        st.audio(file_url)
