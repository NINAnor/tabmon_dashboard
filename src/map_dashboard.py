# map_dashboard_folium.py
import streamlit as st
import folium
import pandas as pd
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from data_loader import load_site_info

def show_map_dashboard(site_csv):
    # Load and preprocess the site_info CSV.
    site_info = load_site_info(site_csv)
    
    st.title("Interactive Device Locations Map")
    st.write("Click on a marker to display the deviceID.")

    # Create a Folium map centered at the mean coordinates.
    m = folium.Map(
        location=[site_info["latitude"].mean(), site_info["longitude"].mean()], 
        zoom_start=6
    )
    
    # Initialize a MarkerCluster.
    marker_cluster = MarkerCluster().add_to(m)
    
    # Add markers for each device to the cluster.
    for idx, row in site_info.iterrows():
        popup_text = (
            f"<b>DeviceID:</b> {row['deviceID']}<br>"
            f"<b>Site:</b> {row['site']}<br>"
            f"<b>Country:</b> {row['country']}<br>"
        )
        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=popup_text,
            tooltip=row["deviceID"],
            icon=folium.DivIcon(
                html=f'<div style="font-size: 24px;">🎙️</div>'
            )
        ).add_to(marker_cluster)
    
    # Display the Folium map and capture click events.
    map_data = st_folium(m, width=1200, height=800)
    
    # If the user clicked on the map, try to determine which device was clicked.
    if map_data.get("last_clicked"):
        clicked_lat = map_data["last_clicked"]["lat"]
        clicked_lon = map_data["last_clicked"]["lng"]
        st.write("Clicked coordinates:", clicked_lat, clicked_lon)
        
        # Use a tolerance (in decimal degrees) to match the clicked point to a device.
        tolerance = 0.01  # adjust as needed (approx. 1km)
        matched = site_info[
            (site_info["latitude"].between(clicked_lat - tolerance, clicked_lat + tolerance)) &
            (site_info["longitude"].between(clicked_lon - tolerance, clicked_lon + tolerance))
        ]
        if not matched.empty:
            device_id = matched.iloc[0]["deviceID"]
            st.write("Clicked device:", device_id)
        else:
            st.write("No device found near the clicked location.")
    
