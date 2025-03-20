import os
import tempfile
from urllib.parse import urljoin

import environ
import requests
import streamlit as st
from requests.auth import HTTPBasicAuth

from audio_dashboard import show_audio_dashboard
from map_dashboard import show_map_dashboard
from site_dashboard import show_site_dashboard

env = environ.Env(DEBUG=(bool, False))

st.sidebar.title("Dashboard Navigation")
option = st.sidebar.selectbox(
    "Choose Dashboard", ["Map Viz", "Site Metadata", "Audio Data"]
)


@st.cache_data(show_spinner=False)
def fetch_csv(url, username, password):
    response = requests.get(url, auth=HTTPBasicAuth(username, password))
    response.raise_for_status()

    with tempfile.NamedTemporaryFile(
        suffix=".csv", delete=False, mode="w", encoding="utf-8"
    ) as tmp_csv:
        tmp_csv.write(response.text)
        tmp_csv_path = tmp_csv.name
    return tmp_csv_path


@st.cache_data(show_spinner=False)
def fetch_parquet(url, username, password):
    response = requests.get(url, auth=HTTPBasicAuth(username, password))
    response.raise_for_status()
    # Write to a temporary file and return its path.
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
        tmp.write(response.content)
        return tmp.name


BASE_DIR = "http://rclone:8081/data/" #os.environ.get("BASE_DATA_DIR")
USER = os.environ.get("USER")
PASSWORD = os.environ.get("PASSWORD")

site_csv_url = urljoin(BASE_DIR, "site_info.csv")
parquet_file_url = urljoin(BASE_DIR, "index.parquet")

# Cache the fetched file contents using stable URLs.
site_csv_text = fetch_csv(site_csv_url, USER, PASSWORD)
parquet_file_path = fetch_parquet(parquet_file_url, USER, PASSWORD)

# Now pass the temporary file paths to your dashboard functions.
if option == "Map Viz":
    show_map_dashboard(site_csv_text, parquet_file_path)
elif option == "Audio Data":
    show_audio_dashboard(site_csv_text, parquet_file_path, USER, PASSWORD)
elif option == "Site Metadata":
    show_site_dashboard(site_csv_text, parquet_file_path, BASE_DIR, USER, PASSWORD)
