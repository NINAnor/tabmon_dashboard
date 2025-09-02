"""
Audio Dashboard for TABMON - Modernized Version
Provides audio file browsing, filtering, and playback functionality.
"""

import streamlit as st

from config.settings import ASSETS_SITE_CSV, ASSETS_PARQUET_FILE
from services.data_service import DataService
from services.audio_service import AudioService
from components.ui_styles import load_custom_css, render_info_section_header
from components.sidebar import render_complete_sidebar
from components.audio import (
    render_site_selection, render_datetime_selector, render_site_details,
    render_audio_stats, render_recordings_table, render_audio_player,
    render_audio_export_options
)
from utils.data_loader import load_site_info


def show_audio_dashboard(site_csv: str, parquet_file: str, base_dir: str = None) -> None:
    """Main audio dashboard function.
    
    Args:
        site_csv: Path or URL to the site CSV file
        parquet_file: Path or URL to the parquet data file
        base_dir: Base directory for data files (optional, for backward compatibility)
    """
    load_custom_css()
    
    st.title("🎵 Audio Analysis Dashboard")
    st.markdown("Browse and play audio recordings from monitoring devices.")
    
    # Initialize services
    data_service = DataService(site_csv, parquet_file)
    audio_service = AudioService(parquet_file)
    
    # Load site information and device data for metrics
    with st.spinner("🔄 Loading site and device information..."):
        site_info = load_site_info(site_csv)
        device_data = data_service.load_device_status()
    
    # Calculate metrics for the sidebar
    metrics = data_service.calculate_metrics(device_data)
    
    # Render complete sidebar with status information only
    with st.sidebar:
        render_complete_sidebar(
            metrics=metrics,
            site_csv=ASSETS_SITE_CSV,
            parquet_file=ASSETS_PARQUET_FILE
        )
    
    if site_info.empty:
        st.error("❌ No site information available.")
        return
    
    # Site selection controls in main page
    col1, col2 = st.columns(2)
    
    with col1:
        selected_country, selected_site, filtered_site_info = render_site_selection(site_info)
    
    with col2:
        target_datetime = render_datetime_selector()
    
    # Get site data
    site_data = filtered_site_info[filtered_site_info["Site"] == selected_site]
    
    if site_data.empty:
        st.error(f"❌ No data found for site: {selected_site}")
        return
    
    # Get the first record for the site
    record = site_data.iloc[0]
    
    # Page header
    st.markdown("---")
    render_info_section_header(f"📍 {selected_site}", level="h2", style_class="site-name-header")
    
    # Render site details
    render_site_details(record)
    
    # Extract device ID
    short_device_id = audio_service.extract_device_id(record)
    
    if not short_device_id:
        st.error("❌ No device ID found for this site.")
        return
    
    # Load audio data and total dataset stats
    with st.spinner("🔄 Loading audio recordings and dataset statistics..."):
        audio_data = audio_service.get_audio_files_by_device(short_device_id)
        total_stats = audio_service.get_total_dataset_stats()
    
    if audio_data.empty:
        st.warning(f"📂 No audio recordings found for device: {short_device_id}")
        # Still show total dataset stats even if no recordings for this device
        if total_stats and total_stats.get('total_recordings', 0) > 0:
            st.info(f"💡 Total dataset contains {total_stats['total_recordings']:,} recordings ({total_stats['total_size_gb']:.2f} GB)")
        return
    
    # Show audio statistics with dataset contribution
    stats = audio_service.get_audio_stats(audio_data)
    render_audio_stats(stats, total_stats)
    
    st.markdown("---")
    
    # Find closest recordings
    closest_recordings = audio_service.find_closest_recordings(audio_data, target_datetime)
    
    # Show target time info
    st.markdown(f"**🎯 Target Time:** {target_datetime.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # Render recordings table and get selection
    selected_file_path = render_recordings_table(closest_recordings, target_datetime)
    
    # Render audio player
    if selected_file_path:
        st.markdown("---")
        render_audio_player(selected_file_path)
    
    # Additional features
    st.markdown("---")
    render_audio_export_options(closest_recordings, selected_site, audio_data)
