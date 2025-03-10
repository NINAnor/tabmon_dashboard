from urllib.parse import unquote

import pandas as pd
import streamlit as st
import re
import subprocess
from urllib.parse import quote, unquote
import json
from pathlib import Path
import duckdb
import requests

from utils.data_loader import load_site_info

def get_encoded_title(title):
    if " " in title:
        return quote(title, safe="/")
    elif "%25" in title:
        return unquote(title)
    else:
        return title

def generate_pictures_mapping(base_url):

    index_parquet = duckdb.read_parquet("http://rclone:8081/data/index.parquet")
    query = "SELECT * FROM 'index_parquet' WHERE MimeType IN ('image/jpeg', 'image/png')"
    data_q = duckdb.sql(query)
    data = data_q.fetchdf()
    records = []

    data['deviceID'] = data["Name"].str.split("_").str[2]
    data['picture_type'] = data["Name"].str.split("_").str[3].str.split(".").str[0]
    data['url'] = base_url + data["Path"]

    return data

def show_site_dashboard(site_csv, mapping_csv):
    site_info = load_site_info(site_csv)
    pictures_mapping = pd.read_csv(mapping_csv)

    base_url = "/data/"
    
    try:
        pictures_mapping = generate_pictures_mapping(base_url)
    except Exception as e:
        st.error(f"Failed to generate pictures mapping: {e}")
        pictures_mapping = pd.DataFrame()

    countries = site_info["country"].dropna().unique().tolist()
    selected_country = st.sidebar.selectbox("Select Country", sorted(countries))

    filtered_site_info = site_info[site_info["country"] == selected_country]

    sites = filtered_site_info["site"].dropna().unique().tolist()
    selected_site = st.sidebar.selectbox("Select Site", sorted(sites))

    site_data = filtered_site_info[filtered_site_info["site"] == selected_site]
    if site_data.empty:
        st.error("No site data found for the selected site.")
        return
    record = site_data.iloc[0]

    st.title(f"Site: {selected_site}")

    st.write("### Site Details")
    st.markdown(f"**Country:** {record.get('country', 'N/A')}")
    st.markdown(f"**Site:** {record.get('site', 'N/A')}")
    st.markdown(f"**Device ID:** {record.get('deviceID', 'N/A')}")
    latitude, longitude = record.get("latitude", "N/A"), record.get("longitude", "N/A")
    st.markdown(f"**Coordinates:** Latitude: {latitude}, Longitude: {longitude}")
    st.markdown(f"**Date:** {record.get('2. Date', 'N/A')}")
    time_utc = record.get(
        "3. Time (UTC!!! Check here  https://www.utctime.net/)", "N/A"
    )
    st.markdown(f"**Time (UTC):** {time_utc}")
    uncertainty = record.get("6. Coordinates uncertainty (meters)", "N/A")
    st.markdown(f"**Coordinates Uncertainty (meters):** {uncertainty}")
    device = record.get(
        "7. GPS device (e.g. Garmin 63r, samsung galaxy S24 with google maps)", "N/A"
    )
    st.markdown(f"**GPS Device:** {device}")
    deployment = record.get(
        "9. DeploymentID: countryCode_deploymentNumber_DeviceID (ex: NO_1_ 7ft35sm)",
        "N/A",
    )
    st.markdown(f"**Deployment ID:** {deployment}")
    height = record.get("10. Microphone height (in cm)", "N/A")
    st.markdown(f"**Microphone Height (cm):** {height}")
    direction = record.get("11. Microphone direction", "N/A")
    st.markdown(f"**Microphone Direction:** {direction}")
    st.markdown(f"**Habitat:** {record.get('12. Habitat', 'N/A')}")
    st.markdown(f"**Email:** {record.get('Adresse e-mail', 'N/A')}")
    st.markdown(f"**Comment/Remark:** {record.get('Comment/remark', 'N/A')}")
    st.markdown(f"**Score:** {record.get('Score', 'N/A')}")

    full_device_id = record.get("deviceID", "")
    if "_" in full_device_id:
        short_device_id = full_device_id.split("_")[-1].strip()
    else:
        short_device_id = full_device_id[-8:]
    st.write(f"**Short Device ID:** {short_device_id}")

    device_images = pictures_mapping[pictures_mapping["deviceID"] == short_device_id]

    st.write(pictures_mapping)

    if not device_images.empty:
        st.write("### Device Images")
        for _idx, row in device_images.iterrows():
            # Use unquote to decode the URL so that double encoding is removed.
            decoded_url = unquote(row["url"])
            image = requests.get(f"http://rclone:8081/{decoded_url}")
            st.image(image = image.content, output_format=image.headers['content-type'])
            #st.image(
            #    decoded_url,
            #    caption=f"{row['picture_type']} view",
            #    use_container_width=True,
            #)
    else:
        st.write("No images found for this device.")
