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

    # Initialize session isolation
    if "session_id" not in st.session_state:
        import uuid

        st.session_state.session_id = str(uuid.uuid4())[:8]  # Short unique ID

    # Page configuration
    st.set_page_config(
        page_title=APP_TITLE,
        layout="wide",
        initial_sidebar_state="expanded",
        page_icon="🎙️",
    )

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

    **🎵 Audio Analysis**: Audio recording metadata analysis and visualization
    (playback disabled for privacy protection)

    **📊 Site Metadata**: Site information and metadata management
    """)

    # Route to appropriate dashboard
    if option == "Map Visualization":
        map_app()
    elif option == "Audio Analysis":
        show_audio_dashboard()
    elif option == "Site Metadata":
        show_site_dashboard()


if __name__ == "__main__":
    main()
