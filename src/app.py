import streamlit as st
import environ
import os
from urllib.parse import urljoin

from audio_dashboard import show_audio_dashboard
from map_dashboard import show_map_dashboard
from site_dashboard import show_site_dashboard

env_path = os.environ.get("ENV_PATH")
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(env_path)

st.sidebar.title("Dashboard Navigation")
option = st.sidebar.selectbox(
    "Choose Dashboard", ["Map Viz", "Site Metadata", "Audio Data"]
)

BASE_DIR=env('BASE_DATA_DIR')

site_csv = urljoin(BASE_DIR, "site_info.csv")
parquet_file = urljoin(BASE_DIR , "index.parquet")

if option == "Map Viz":
    show_map_dashboard(site_csv, parquet_file) 
elif option == "Audio Data":
    show_audio_dashboard(site_csv, parquet_file)
elif option == "Site Metadata":
    show_site_dashboard(site_csv, parquet_file, BASE_DIR)
