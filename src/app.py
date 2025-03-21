from urllib.parse import urljoin

import streamlit as st

from audio_dashboard import show_audio_dashboard
from map_dashboard import show_map_dashboard
from site_dashboard import show_site_dashboard

# env = environ.Env(DEBUG=(bool, False))

st.sidebar.title("Dashboard Navigation")
option = st.sidebar.selectbox(
    "Choose Dashboard", ["Map Viz", "Site Metadata", "Audio Data"]
)

BASE_DIR = "http://rclone:8081/data/"  # os.environ.get("BASE_DATA_DIR")

site_csv_url = urljoin(BASE_DIR, "site_info.csv")
parquet_file_url = urljoin(BASE_DIR, "index.parquet")

if option == "Map Viz":
    show_map_dashboard(site_csv_url, parquet_file_url)
elif option == "Audio Data":
    show_audio_dashboard(site_csv_url, parquet_file_url)
elif option == "Site Metadata":
    show_site_dashboard(site_csv_url, parquet_file_url, BASE_DIR)
