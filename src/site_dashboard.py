from urllib.parse import unquote
from datetime import datetime
import base64
import requests

import duckdb
import pandas as pd
import streamlit as st

from config.settings import COUNTRY_MAP
from services.data_service import DataService
from components.ui_styles import load_custom_css
from utils.data_loader import load_site_info


class SiteMetadataService:
    """Service for handling site metadata and image operations."""
    
    def __init__(self, parquet_file: str):
        self.parquet_file = parquet_file
    
    def generate_pictures_mapping(self) -> pd.DataFrame:
        """Generate mapping of device pictures from parquet data."""
        try:
            # Check if we're dealing with a URL or local file
            if self.parquet_file.startswith(('http://', 'https://')):
                # For URLs, we need to load the data first then filter
                data = pd.read_parquet(self.parquet_file)
                # Filter for image files
                data = data[data["MimeType"].isin(['image/jpeg', 'image/png'])]
            else:
                # For local files, use DuckDB for efficient filtering
                query = """
                SELECT * FROM read_parquet(?)
                WHERE MimeType IN ('image/jpeg', 'image/png')
                """
                data = duckdb.execute(query, (self.parquet_file,)).df()
            
            if data.empty:
                return pd.DataFrame()
            
            # Extract device ID and picture type from filename
            data["deviceID"] = data["Name"].str.split("_").str[2]
            data["picture_type"] = data["Name"].str.split("_").str[3].str.split(".").str[0]
            data["url"] = "/data/" + data["Path"]
            
            return data
        except Exception as e:
            st.error(f"Failed to generate pictures mapping: {e}")
            return pd.DataFrame()


def render_site_filters(site_info: pd.DataFrame) -> tuple:
    """Render country and site selection filters."""
    st.sidebar.markdown("### 🌍 Site Selection")
    
    # Country filter
    countries = site_info["Country"].dropna().unique().tolist()
    selected_country = st.sidebar.selectbox(
        "📍 Select Country", 
        sorted(countries),
        key="site_country_filter"
    )
    
    # Filter by country
    filtered_site_info = site_info[site_info["Country"] == selected_country]
    
    # Site filter
    sites = filtered_site_info["Site"].dropna().unique().tolist()
    selected_site = st.sidebar.selectbox(
        "🏞️ Select Site", 
        sorted(sites),
        key="site_site_filter"
    )
    
    return selected_country, selected_site, filtered_site_info


def render_site_details(record: pd.Series) -> None:
    """Render detailed site information."""
    st.markdown("### 📋 Site Details")
    
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


def render_device_images(device_id: str, pictures_mapping: pd.DataFrame) -> None:
    """Render device images in an organized layout."""
    if pictures_mapping.empty:
        st.info("📷 No images found for this device.")
        return
    
    # Extract short device ID for matching
    if "_" in device_id:
        short_device_id = device_id.split("_")[-1].strip()
    else:
        short_device_id = device_id[-8:] if len(device_id) >= 8 else device_id
    
    device_images = pictures_mapping[pictures_mapping["deviceID"] == short_device_id]
    
    if device_images.empty:
        st.info(f"📷 No images found for device ID: {short_device_id}")
        return
    
    st.markdown("### 📸 Device Images")
    
    # Group images by type
    image_types = device_images["picture_type"].unique()
    
    if len(image_types) > 1:
        # Multiple image types - use tabs
        tabs = st.tabs([f"📷 {img_type.title()}" for img_type in sorted(image_types)])
        
        for i, img_type in enumerate(sorted(image_types)):
            with tabs[i]:
                type_images = device_images[device_images["picture_type"] == img_type]
                render_image_grid(type_images)
    else:
        # Single type - show directly
        render_image_grid(device_images)


def get_auth_credentials():
    """Read authentication credentials from environment variables or Docker secret."""
    import os
    
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
                                use_column_width=True
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


def show_site_dashboard(site_csv: str, parquet_file: str, base_dir: str) -> None:
    """Main site metadata dashboard function."""
    load_custom_css()
    
    st.title("🏞️ Site Metadata Dashboard")
    st.markdown("Explore detailed information about recording sites and device deployments.")
    
    # Initialize services with correct URL parameters
    data_service = DataService(site_csv, parquet_file)
    site_metadata_service = SiteMetadataService(parquet_file)
    
    # Load data
    with st.spinner("🔄 Loading site information..."):
        site_info = load_site_info(site_csv)
        
    with st.spinner("🔄 Loading device images..."):
        pictures_mapping = site_metadata_service.generate_pictures_mapping()
    
    if site_info.empty:
        st.error("❌ No site information available.")
        return
    
    # Render filters
    selected_country, selected_site, filtered_site_info = render_site_filters(site_info)
    
    # Get site data
    site_data = filtered_site_info[filtered_site_info["Site"] == selected_site]
    
    if site_data.empty:
        st.error(f"❌ No data found for site: {selected_site}")
        return
    
    # Get the first (and typically only) record for the site
    record = site_data.iloc[0]
    
    # Page header with site name
    st.markdown(f"## 📍 {selected_site}")
    st.markdown(f"**Country:** {selected_country} • **Active:** {'✅ Yes' if record.get('Active', False) else '❌ No'}")
    
    # Render main content
    render_site_details(record)
    
    # Add spacing
    st.markdown("---")
    
    # Render device images
    device_id = record.get("DeviceID", "")
    render_device_images(device_id, pictures_mapping)
    
    # Additional features
    st.markdown("---")
    
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
