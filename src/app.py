# app.py
import streamlit as st
from audio_dashboard import show_audio_dashboard
from map_dashboard import show_map_dashboard
from site_dashboard import show_site_dashboard

st.sidebar.title("Dashboard Navigation")
option = st.sidebar.selectbox("Choose Dashboard", ["Map Dashboard", "Site Dashboard", "Audio Dashboard"])

parquet_file = "assets/index.parquet"
site_csv = "assets/site_info.csv"

if option == "Map Dashboard":
    show_map_dashboard(site_csv)
elif option == "Audio Dashboard":
    show_audio_dashboard(parquet_file)
elif option == "Site Dashboard":
    show_site_dashboard(site_csv)
