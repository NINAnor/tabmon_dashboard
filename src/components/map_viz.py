"""
Map visualization components for the TABMON dashboard.
"""

import folium
import pandas as pd
import streamlit as st
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

from config.settings import DEFAULT_ZOOM, MAP_HEIGHT, MAP_WIDTH


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
        tiles="OpenStreetMap",
    )

    # Create marker cluster with optimal settings
    marker_cluster = MarkerCluster(
        maxClusterRadius=40,
        showCoverageOnHover=False,
        spiderfyOnMaxZoom=True,
        removeOutsideVisibleBounds=False,
    ).add_to(m)

    marker_count = 0

    # Add markers for each device
    for _, row in status_df.iterrows():
        # Handle different possible column names
        site_name = row.get("site_name", row.get("Site", "Unknown Site"))
        cluster_name = row.get("cluster_name", row.get("Cluster", ""))
        location_text = f"{cluster_name}: {site_name}" if cluster_name else site_name

        # Skip if no coordinates
        if pd.isna(row.get("Latitude")) or pd.isna(row.get("Longitude")):
            continue

        popup_html = _create_popup_html(row, location_text)

        # Status-based styling
        status = row.get("status", "Unknown")
        icon_color = "green" if status == "Online" else "red"
        icon_symbol = "play" if status == "Online" else "pause"

        folium.Marker(
            location=[row["Latitude"], row["Longitude"]],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"🎙️ {site_name} ({status})",
            icon=folium.Icon(color=icon_color, icon=icon_symbol, prefix="fa"),
        ).add_to(marker_cluster)
        marker_count += 1

    return st_folium(
        m, width=MAP_WIDTH, height=MAP_HEIGHT, returned_objects=["last_object_clicked"]
    )


def _create_popup_html(row: pd.Series, location_text: str) -> str:
    """Create HTML content for map marker popups."""
    # Handle different possible column names and ensure we get scalar values
    device_id = row.get(
        "device_name", row.get("DeploymentID", row.get("device", "Unknown Device"))
    )

    # Ensure device_id is a string, not a pandas Series
    if hasattr(device_id, "iloc"):
        device_id = device_id.iloc[0] if len(device_id) > 0 else "Unknown Device"
    elif pd.isna(device_id):
        device_id = "Unknown Device"
    else:
        device_id = str(device_id)

    country = row.get("Country", "Unknown")
    if hasattr(country, "iloc"):
        country = country.iloc[0] if len(country) > 0 else "Unknown"
    elif pd.isna(country):
        country = "Unknown"
    else:
        country = str(country)

    status = row.get("status", "Unknown")
    if hasattr(status, "iloc"):
        status = status.iloc[0] if len(status) > 0 else "Unknown"
    elif pd.isna(status):
        status = "Unknown"
    else:
        status = str(status)

    last_recorded = row.get(
        "last_file", row.get("last_recorded", row.get("recorded_at", "N/A"))
    )
    if hasattr(last_recorded, "iloc"):
        last_recorded = last_recorded.iloc[0] if len(last_recorded) > 0 else "N/A"

    if pd.notna(last_recorded) and hasattr(last_recorded, "strftime"):
        last_recorded = last_recorded.strftime("%Y-%m-%d %H:%M")
    elif pd.isna(last_recorded):
        last_recorded = "N/A"

    days_since = row.get("days_since_last", "N/A")
    if hasattr(days_since, "iloc"):
        days_since = days_since.iloc[0] if len(days_since) > 0 else "N/A"

    if pd.notna(days_since) and days_since != "N/A":
        try:
            days_since = f"{float(days_since):.1f} days"
        except (ValueError, TypeError):
            days_since = "N/A"

    total_recordings = row.get("total_recordings", "N/A")
    if hasattr(total_recordings, "iloc"):
        total_recordings = (
            total_recordings.iloc[0] if len(total_recordings) > 0 else "N/A"
        )

    if pd.notna(total_recordings) and total_recordings != "N/A":
        try:
            total_recordings = int(total_recordings)
        except (ValueError, TypeError):
            total_recordings = "N/A"

    return f"""
    <div style="font-family: Arial, sans-serif; min-width: 200px;">
        <h4 style="margin: 0; color: #2E86AB; text-align: center;">🎙️ {device_id}</h4>
        <hr style="margin: 10px 0;">
        <p style="margin: 5px 0;"><b>📍 Site:</b> {location_text}</p>
        <p style="margin: 5px 0;"><b>🌍 Country:</b> {country}</p>
        <p style="margin: 5px 0;"><b>📶 Status:</b>
            <span style="color: {"green" if status == "Online" else "red"};
                         font-weight: bold;">
                {status}
            </span>
        </p>
        <p style="margin: 5px 0;"><b>🕒 Last Recorded:</b> {last_recorded}</p>
        <p style="margin: 5px 0;"><b>⏱️ Days Since:</b> {days_since}</p>
        <p style="margin: 5px 0;"><b>🎵 Total Recordings:</b> {total_recordings}</p>
    </div>
    """
