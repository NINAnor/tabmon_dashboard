import streamlit as st
import environ
import os

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

BASE_DATA_DIR=env('BASE_DATA_DIR')

if option == "Map Viz":
    show_map_dashboard(BASE_DATA_DIR) 
elif option == "Audio Data":
    show_audio_dashboard(BASE_DATA_DIR)
elif option == "Site Metadata":
    show_site_dashboard(BASE_DATA_DIR)
