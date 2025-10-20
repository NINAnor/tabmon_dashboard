"""
Main TABMON Dashboard Application
"""

from pathlib import Path

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

    # Add the logo
    logo_path = Path("/app/src/images/tabmon_logo.png")
    st.sidebar.image(logo_path, width=300)

    st.sidebar.title("🎙️ TABMON Dashboard")
    st.sidebar.markdown("---")

    option = st.sidebar.selectbox(
        "📊 Choose panel",
        ["Device status", "Dataset overview", "Site Metadata"],
        index=0,
        help="Select which dashboard view to display",
    )

    st.sidebar.markdown("---")

    # Add dashboard info
    st.sidebar.markdown("""
    ### 📋 Dashboard Overview

    **🗺️ Device status**: Explore the status of our devices
                        
    **🎵 Dataset overview**: Explore the size of our dataset
                        
    **📊 Site Metadata**: Explore our sites
    """)

    # Route to appropriate dashboard
    if option == "Device status":
        map_app()
    elif option == "Dataset overview":
        show_audio_dashboard()
    elif option == "Site Metadata":
        show_site_dashboard()


if __name__ == "__main__":
    main()
