"""
Site Dashboard Components
Provides reusable components for site metadata exploration and device information.
"""

import os
import requests
from datetime import datetime

import pandas as pd
import streamlit as st

from components.ui_styles import render_info_section_header


def get_auth_credentials():
    """Read authentication credentials from environment variables or Docker secret."""
    # Priority 1: Environment variables (from .env file in production via Portainer)
    username = os.getenv('AUTH_USERNAME')
    password = os.getenv('AUTH_PASSWORD')
    
    if username and password:
        return (username, password)
    
    # Priority 2: Try to read username from htpasswd secret if available
    try:
        with open('/run/secrets/htpasswd', 'r') as f:
            htpasswd_content = f.read().strip()
            lines = htpasswd_content.split('\n')
            for line in lines:
                if line.strip() and ':' in line:
                    username = line.split(':')[0]
                    # Note: Still need password from environment variables
                    # as htpasswd contains hashed passwords only
                    break
    except (FileNotFoundError, IOError):
        pass
    
    # No fallback - require explicit configuration
    raise ValueError("Authentication credentials not found. Please set AUTH_USERNAME and AUTH_PASSWORD environment variables.")


def render_site_filters(site_info: pd.DataFrame) -> tuple:
    """Render country and site selection filters."""
    st.markdown("### 🌍 Site Selection")
    
    # Country filter
    countries = site_info["Country"].dropna().unique().tolist()
    selected_country = st.selectbox(
        "📍 Select Country", 
        sorted(countries),
        key="site_country_filter"
    )
    
    # Filter by country
    filtered_site_info = site_info[site_info["Country"] == selected_country]
    
    # Site filter
    sites = filtered_site_info["Site"].dropna().unique().tolist()
    selected_site = st.selectbox(
        "🏞️ Select Site", 
        sorted(sites),
        key="site_site_filter"
    )
    
    return selected_country, selected_site, filtered_site_info


def render_site_details(filtered_data: pd.DataFrame, selected_site: str) -> None:
    """Render detailed site information."""
    site_data = filtered_data[filtered_data["Site"] == selected_site]
    
    if site_data.empty:
        st.error(f"❌ No data found for site: {selected_site}")
        return
    
    record = site_data.iloc[0]
    
    render_info_section_header("📋 Site Details", style_class="site-details-header")
    
    # Create two columns for better layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🌍 Location Information")
        st.markdown(f"**Country:** {record.get('Country', 'N/A')}")
        st.markdown(f"**Site:** {record.get('Site', 'N/A')}")
        st.markdown(f"**Cluster:** {record.get('Cluster', 'N/A')}")
        
        # Coordinates
        latitude = record.get("Latitude", "N/A")
        longitude = record.get("Longitude", "N/A")
        st.markdown(f"**Coordinates:** {latitude}, {longitude}")
        
        # Coordinate uncertainty
        uncertainty = record.get("Coordinates_uncertainty", "N/A")
        st.markdown(f"**Coordinate Uncertainty:** {uncertainty} meters")
        
        # GPS device
        gps_device = record.get("GPS_device", "N/A")
        st.markdown(f"**GPS Device:** {gps_device}")
    
    with col2:
        st.markdown("#### 🎙️ Device Information")
        st.markdown(f"**Device ID:** {record.get('DeviceID', 'N/A')}")
        st.markdown(f"**Deployment ID:** {record.get('DeploymentID', 'N/A')}")
        
        # Microphone details
        mic_height = record.get("Microphone_height", "N/A")
        st.markdown(f"**Microphone Height:** {mic_height} cm")
        
        mic_direction = record.get("Microphone_direction", "N/A")
        st.markdown(f"**Microphone Direction:** {mic_direction}")
        
        # Habitat
        habitat = record.get("12. Habitat", "N/A")
        st.markdown(f"**Habitat:** {habitat}")
        
        # Score
        score = record.get("Score", "N/A")
        st.markdown(f"**Quality Score:** {score}")
    
    # Deployment timeline
    st.markdown("#### ⏰ Deployment Timeline")
    col1, col2 = st.columns(2)
    
    with col1:
        begin_date = record.get("deploymentBeginDate", "N/A")
        begin_time = record.get("deploymentBeginTime", "N/A")
        st.markdown(f"**Start:** {begin_date} {begin_time}")
    
    with col2:
        end_date = record.get("deploymentEndDate", "N/A")
        end_time = record.get("deploymentEndTime", "N/A")
        st.markdown(f"**End:** {end_date} {end_time}")
    
    # Contact and comments
    st.markdown("#### 📝 Additional Information")
    email = record.get("Adresse e-mail", "N/A")
    if email != "N/A":
        st.markdown(f"**Contact:** {email}")
    
    comments = record.get("Comments", "N/A")
    if comments != "N/A":
        st.markdown(f"**Comments:** {comments}")


def render_image_grid(images_df: pd.DataFrame) -> None:
    """Render images in a responsive grid layout."""
    cols_per_row = 2
    
    for i in range(0, len(images_df), cols_per_row):
        cols = st.columns(cols_per_row)
        
        for j, (_, row) in enumerate(images_df.iloc[i:i+cols_per_row].iterrows()):
            with cols[j]:
                try:
                    # Get the original URL (already has /data/ prefix)
                    image_url = row["url"]
                    
                    # Check if we're dealing with a local or remote URL
                    if image_url.startswith('/data/'):
                        # This is a remote URL that needs authentication
                        # Use the reverse proxy service name from within Docker (port 80 internal)
                        full_url = f"http://reverseproxy:80{image_url}"
                        
                        # Use Streamlit's image function with authentication
                        auth = get_auth_credentials()
                        response = requests.get(full_url, auth=auth, timeout=10)
                        
                        if response.status_code == 200:
                            st.image(
                                response.content,
                                caption=row['picture_type'].title(),
                                use_container_width=True
                            )
                        else:
                            st.error(f"Failed to load image: {image_url}")
                    else:
                        # Local image or direct URL
                        st.image(
                            image_url,
                            caption=row['picture_type'].title(),
                            use_container_width=True
                        )
                except Exception as e:
                    st.error(f"Error loading image: {str(e)}")
                    # Fallback to broken link message
                    st.markdown(f"**{row['picture_type'].title()}**: Image unavailable")


def render_device_images(filtered_data: pd.DataFrame, selected_site: str) -> None:
    """Render device images if available."""
    site_data = filtered_data[filtered_data["Site"] == selected_site]
    
    if site_data.empty:
        return
    
    render_info_section_header("� Device Images", style_class="site-images-header")


def render_site_export_options(site_data: pd.DataFrame, selected_site: str, record: pd.Series) -> None:
    """Render site export and additional options."""
    render_info_section_header("🔧 Export & Tools", level="h4", style_class="export-tools-header")
    
    # Export functionality
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Export Site Data", key="export_site_data"):
            site_csv_data = site_data.to_csv(index=False)
            st.download_button(
                label="💾 Download as CSV",
                data=site_csv_data,
                file_name=f"site_data_{selected_site}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key="download_site_csv"
            )
    
    with col2:
        # Link to map view
        if record.get("Latitude") and record.get("Longitude"):
            lat, lon = record["Latitude"], record["Longitude"]
            maps_url = f"https://www.google.com/maps?q={lat},{lon}"
            st.markdown(f"[🗺️ View on Google Maps]({maps_url})")
