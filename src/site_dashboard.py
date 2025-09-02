"""
Site Dashboard for TABMON - Modernized Version
Provides detailed site metadata exploration and device information.
"""

import streamlit as st

from components.sidebar import render_complete_sidebar
from components.site_components import (
    render_device_images,
    render_site_details,
    render_site_export_options,
    render_site_filters,
)
from components.ui_styles import load_custom_css, render_info_section_header
from config.settings import ASSETS_PARQUET_FILE, ASSETS_SITE_CSV
from services.data_service import DataService
from services.site_service import SiteMetadataService
from utils.data_loader import load_site_info


def show_site_dashboard(site_csv: str, parquet_file: str, base_dir: str) -> None:
    """Main site metadata dashboard function."""
    load_custom_css()

    st.title("🏞️ Site Metadata Dashboard")
    st.markdown(
        "Explore detailed information about recording sites and device deployments."
    )

    # Initialize services with correct URL parameters
    data_service = DataService(site_csv, parquet_file)
    site_metadata_service = SiteMetadataService(parquet_file)

    # Load data
    with st.spinner("🔄 Loading site and device information..."):
        site_info = load_site_info(site_csv)
        device_data = data_service.load_device_status()

    with st.spinner("🔄 Loading device images..."):
        pictures_mapping = site_metadata_service.generate_pictures_mapping()

    # Calculate metrics for the sidebar
    metrics = data_service.calculate_metrics(device_data)

    # Render complete sidebar with status information only
    with st.sidebar:
        render_complete_sidebar(
            metrics=metrics, site_csv=ASSETS_SITE_CSV, parquet_file=ASSETS_PARQUET_FILE
        )

    if site_info.empty:
        st.error("❌ No site information available.")
        return

    # Main site information section
    render_info_section_header("🏞️ Site Information", style_class="site-info-header")

    # Site selection controls in main page
    selected_country, selected_site, filtered_site_info = render_site_filters(site_info)

    # Get site data
    site_data = filtered_site_info[filtered_site_info["Site"] == selected_site]

    if site_data.empty:
        st.error(f"❌ No data found for site: {selected_site}")
        return

    # Get the first (and typically only) record for the site
    record = site_data.iloc[0]

    # Page header with site name
    st.markdown("---")
    render_info_section_header(
        f"📍 {selected_site}", level="h2", style_class="site-name-header"
    )
    st.markdown(
        f"**Country:** {selected_country} • **Active:** "
        f"{'✅ Yes' if record.get('Active', False) else '❌ No'}"
    )

    # Render site details as a subsection
    render_info_section_header(
        "📋 Site Details", level="h4", style_class="site-details-header"
    )
    render_site_details(filtered_site_info, selected_site)

    # Add spacing
    st.markdown("---")

    # Render device images
    # Extract short device ID for image matching
    short_device_id = site_metadata_service.extract_device_id(record)
    render_device_images(short_device_id, pictures_mapping)

    # Additional features and export options
    st.markdown("---")
    render_site_export_options(site_data, selected_site, record)
