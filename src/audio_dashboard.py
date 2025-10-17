"""
Audio Dashboard for TABMON - Modernized Version
Provides audio file browsing, filtering, and playback functionality.
"""

import streamlit as st

from components.audio import (
    render_audio_stats,
    render_site_details,
    render_site_selection,
)
from components.sidebar import render_complete_sidebar
from components.ui_styles import load_custom_css, render_info_section_header
from config.settings import SITE_CSV_URL, PARQUET_FILE_URL, BASE_DATA_URL
from services.audio_service import AudioService
from services.data_service import DataService
from utils.utils import extract_device_id


def show_audio_dashboard() -> None:
    """Main audio dashboard function."""
    load_custom_css()

    st.title("🎵 Audio Analysis Dashboard")
    st.markdown("Browse and analyze audio recordings metadata from monitoring devices.")

    # Initialize services
    data_service = DataService()
    audio_service = AudioService()

    # Load site information and device data for metrics
    with st.spinner("🔄 Loading site and device information..."):
        site_info = data_service.load_site_info()
        device_data = data_service.load_device_status()

    # Calculate metrics for the sidebar
    metrics = data_service.calculate_metrics(device_data)

    # Render complete sidebar with status information only
    with st.sidebar:
        render_complete_sidebar(metrics=metrics)

    if site_info.empty:
        st.error("❌ No site information available.")
        return

    # Site selection controls in main page
    col1, col2 = st.columns(2)

    with col1:
        selected_country, selected_site, filtered_site_info = render_site_selection(
            site_info
        )

    # Get site data
    site_data = filtered_site_info[filtered_site_info["Site"] == selected_site]

    if site_data.empty:
        st.error(f"❌ No data found for site: {selected_site}")
        return

    # Get the first record for the site
    record = site_data.iloc[0]

    # Page header
    st.markdown("---")
    render_info_section_header(
        f"📍 {selected_site}", level="h2", style_class="site-name-header"
    )

    # Render site details
    render_site_details(record)

    # Extract device ID
    short_device_id = extract_device_id(record)

    if not short_device_id:
        st.error("❌ No device ID found for this site.")
        return

    # Load audio data and total dataset stats
    with st.spinner("🔄 Loading audio recordings and dataset statistics..."):
        total_stats = audio_service.get_total_dataset_stats()
        device_stats = audio_service.get_device_stats(short_device_id)

    # Always show audio statistics with dataset contribution using preprocessed stats
    if device_stats:
        render_audio_stats(device_stats, total_stats)
    else:
        st.warning(f"📂 No statistics found for device: {short_device_id}")
        if total_stats and total_stats.get("total_recordings", 0) > 0:
            total_recordings = total_stats["total_recordings"]
            total_size_gb = total_stats["total_size_gb"]
            st.info(
                f"💡 Total dataset contains {total_recordings:,} recordings "
                f"({total_size_gb:.2f} GB)"
            )
        return
