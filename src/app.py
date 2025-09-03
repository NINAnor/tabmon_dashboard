"""
Main TABMON Dashboard Application
"""

import streamlit as st

from audio_dashboard import show_audio_dashboard
from config.settings import APP_TITLE
from map_dashboard import app as map_app
from site_dashboard import show_site_dashboard


def main():
    """Main application entry point."""

    # Page configuration
    st.set_page_config(
        page_title=APP_TITLE,
        layout="wide",
        initial_sidebar_state="expanded",
        page_icon="🎙️",
    )

    # Data source configuration
    BASE_DIR = "http://rclone:8081/data/"  # Remote data source
    site_csv_url = f"{BASE_DIR}site_info.csv"
    parquet_file_url = f"{BASE_DIR}index.parquet"

    # Navigation sidebar
    st.sidebar.title("🎙️ TABMON Dashboard")
    st.sidebar.markdown("---")

    option = st.sidebar.selectbox(
        "📊 Choose Dashboard",
        ["Map Visualization", "Audio Analysis", "Site Metadata"],
        index=0,
        help="Select which dashboard view to display",
    )

    st.sidebar.markdown("---")

    # Add dashboard info
    st.sidebar.markdown("""
    ### 📋 Dashboard Overview

    **🗺️ Map Visualization**: Real-time device monitoring with interactive maps
    and status tracking

    **🎵 Audio Analysis**: In-depth audio recording analysis and visualization

    **📊 Site Metadata**: Site information and metadata management
    """)

    # Route to appropriate dashboard
    if option == "Map Visualization":
        map_app(site_csv_url, parquet_file_url)
    elif option == "Audio Analysis":
        show_audio_dashboard(site_csv_url, parquet_file_url)
    elif option == "Site Metadata":
        show_site_dashboard(site_csv_url, parquet_file_url, BASE_DIR)


if __name__ == "__main__":
    main()
