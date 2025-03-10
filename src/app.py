import streamlit as st

from audio_dashboard import show_audio_dashboard
from map_dashboard import show_map_dashboard
from site_dashboard import show_site_dashboard

st.sidebar.title("Dashboard Navigation")
option = st.sidebar.selectbox(
    "Choose Dashboard", ["Map Viz", "Site Metadata", "Audio Data"]
)

parquet_file = "http://rclone:8081/data/index.parquet"  # "assets/index.parquet"
site_csv = "http://rclone:8081/data/site_info.csv"  # "assets/site_info.csv"
picture_mapping = (
    "http://rclone:8081/data/pictures_mapping.csv"  # "assets/pictures_mapping.csv"
)

if option == "Map Viz":
    show_map_dashboard(site_csv, parquet_file)
elif option == "Audio Data":
    show_audio_dashboard(parquet_file, site_csv)
elif option == "Site Metadata":
    show_site_dashboard(site_csv, picture_mapping)
