import io
from datetime import datetime

import pandas as pd
import requests
import streamlit as st

from PIL import Image
from components.ui_styles import render_info_section_header


def render_site_filters(site_info: pd.DataFrame) -> tuple:
    """Render country and site selection filters."""
    st.markdown("### 🌍 Site Selection")

    # Country filter
    countries = site_info["Country"].dropna().unique().tolist()
    selected_country = st.selectbox(
        "📍 Select Country", sorted(countries), key="site_country_filter"
    )

    # Filter by country
    filtered_site_info = site_info[site_info["Country"] == selected_country]

    # Site filter
    sites = filtered_site_info["Site"].dropna().unique().tolist()
    selected_site = st.selectbox("🏞️ Select Site", sorted(sites), key="site_site_filter")

    return selected_country, selected_site, filtered_site_info


def render_site_details(filtered_data: pd.DataFrame, selected_site: str) -> None:
    """Render detailed site information."""
    site_data = filtered_data[filtered_data["Site"] == selected_site]

    if site_data.empty:
        st.error(f"❌ No data found for site: {selected_site}")
        return

    record = site_data.iloc[0]

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

@st.cache_data
def download_image(url):
    #TODO: create a thumbnail for faster loading
    response = requests.get(url)
    response.raise_for_status()

    image = Image.open(io.BytesIO(response.content))

    image_without_exif = Image.new(image.mode, image.size)
    image_without_exif.putdata(image.getdata())
    return image_without_exif

def render_image_grid(images_df: pd.DataFrame) -> None:
    """Render images in a responsive grid layout."""
    cols_per_row = 2

    for i in range(0, len(images_df), cols_per_row):
        cols = st.columns(cols_per_row)

        for j, (_, row) in enumerate(images_df.iloc[i : i + cols_per_row].iterrows()):
            with cols[j]:
                try:
                    # Get the original URL (already has /data/ prefix)

                    st.image(
                        download_image(row["url"]),
                        caption=row["picture_type"].title(),
                        use_container_width=True,
                    )

                except Exception as e:
                    st.error(f"Error loading image: {str(e)}")
                    # Fallback to broken link message
                    st.markdown(f"**{row['picture_type'].title()}**: Image unavailable")


def render_device_images(device_id: str, pictures_mapping: pd.DataFrame) -> None:
    """Render device images if available."""
    if pictures_mapping.empty:
        st.info("📸 No device images available for this site.")
        return

    render_info_section_header("📸 Device Images", style_class="site-images-header")

    # Filter images for this device
    # Check if deviceID column exists and filter accordingly
    if "deviceID" in pictures_mapping.columns:
        device_images = pictures_mapping[pictures_mapping["deviceID"] == device_id]
    else:
        st.info("📸 Device image mapping not available.")
        return

    if device_images.empty:
        st.info(f"📸 No images found for device {device_id}")
        return

    # Render images in a grid
    render_image_grid(device_images)
