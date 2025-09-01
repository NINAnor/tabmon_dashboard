"""
Map visualization components for the TABMON dashboard.
"""

import folium
import pandas as pd
import streamlit as st
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

from config.settings import MAP_HEIGHT, MAP_WIDTH, DEFAULT_ZOOM


def render_device_map(site_info: pd.DataFrame, status_df: pd.DataFrame):
    """Render the interactive map with device locations."""
    if site_info.empty:
        st.warning("⚠️ No site information available")
        return None
    
    # Create map centered on device locations
    center_lat = site_info["Latitude"].mean()
    center_lon = site_info["Longitude"].mean()
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=DEFAULT_ZOOM,
        tiles="OpenStreetMap"
    )
    
    marker_cluster = MarkerCluster().add_to(m)
    
    # Add markers with improved styling
    for _, row in status_df.iterrows():
        # Handle different possible column names
        site_name = row.get('site_name', row.get('Site', 'Unknown Site'))
        cluster_name = row.get('cluster_name', row.get('Cluster', ''))
        location_text = f"{cluster_name}: {site_name}" if cluster_name else site_name
        
        # Ensure we have coordinates
        if pd.isna(row.get('Latitude')) or pd.isna(row.get('Longitude')):
            continue
            
        popup_html = _create_popup_html(row, location_text)
        
        # Status-based styling
        status = row.get('status', 'Unknown')
        icon_color = "green" if status == "Online" else "red"
        icon_symbol = "play" if status == "Online" else "pause"
        
        folium.Marker(
            location=[row["Latitude"], row["Longitude"]],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"🎙️ {site_name} ({status})",
            icon=folium.Icon(
                color=icon_color, 
                icon=icon_symbol, 
                prefix="fa"
            ),
        ).add_to(marker_cluster)
    
    return st_folium(m, width=MAP_WIDTH, height=MAP_HEIGHT)


def _create_popup_html(row: pd.Series, location_text: str) -> str:
    """Create HTML content for map marker popups."""
    # Handle different possible column names
    device_id = row.get('device_name', row.get('DeploymentID', row.get('device', 'Unknown Device')))
    country = row.get('Country', 'Unknown')
    status = row.get('status', 'Unknown')
    
    last_recorded = row.get('last_file', row.get('last_recorded', row.get('recorded_at', 'N/A')))
    if pd.notna(last_recorded) and hasattr(last_recorded, 'strftime'):
        last_recorded = last_recorded.strftime('%Y-%m-%d %H:%M')
    
    days_since = row.get('days_since_last', 'N/A')
    if pd.notna(days_since):
        days_since = f"{days_since:.1f} days"
    
    total_recordings = row.get('total_recordings', 'N/A')
    
    return f"""
    <div style="font-family: Arial, sans-serif; min-width: 200px;">
        <h4 style="margin: 0; color: #2E86AB; text-align: center;">🎙️ {device_id}</h4>
        <hr style="margin: 10px 0;">
        <p style="margin: 5px 0;"><b>📍 Site:</b> {location_text}</p>
        <p style="margin: 5px 0;"><b>🌍 Country:</b> {country}</p>
        <p style="margin: 5px 0;"><b>📶 Status:</b> 
            <span style="color: {'green' if status == 'Online' else 'red'}; font-weight: bold;">
                {status}
            </span>
        </p>
        <p style="margin: 5px 0;"><b>🕒 Last Recorded:</b> {last_recorded}</p>
        <p style="margin: 5px 0;"><b>⏱️ Days Since:</b> {days_since}</p>
        <p style="margin: 5px 0;"><b>🎵 Total Recordings:</b> {total_recordings}</p>
    </div>
    """
