"""
Authentication component for detailed map access.
"""

import os
import streamlit as st
from config.settings import DETAILED_MAP_PASSWORD


def get_detailed_map_password() -> str:
    """Get the detailed map password from environment variable or config."""
    return os.environ.get("AUTH_PASSWORD", DETAILED_MAP_PASSWORD)


def check_detailed_map_access() -> bool:
    """
    Check if the user has access to the detailed map.
    Returns True if authorized, False otherwise.
    """
    # Initialize session state for detailed map access
    if "detailed_map_authorized" not in st.session_state:
        st.session_state.detailed_map_authorized = False
    
    return st.session_state.detailed_map_authorized


def render_detailed_map_auth() -> bool:
    """
    Render the detailed map authentication interface.
    Returns True if user is authorized for detailed map access.
    """
    # Check if already authorized
    if check_detailed_map_access():
        return True
    
    # Show authentication interface
    with st.expander("🔐 Detailed Map Access", expanded=False):
        st.markdown("""
        **Project Team Access**: Enter your dashboard password to access detailed device locations.
        
        ⚠️ **Note**: This will show exact device coordinates for project management purposes.
        """)
        
        password = st.text_input(
            "Password",
            type="password",
            help="Enter your dashboard password to unlock detailed map view",
            key="detailed_map_password"
        )
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if st.button("🔓 Unlock Detailed Map", type="primary"):
                if password == get_detailed_map_password():
                    st.session_state.detailed_map_authorized = True
                    st.success("✅ Access granted! Detailed map is now available.")
                    st.rerun()
                else:
                    st.error("❌ Invalid password")
        
        with col2:
            if st.session_state.detailed_map_authorized:
                if st.button("🔒 Lock Detailed Map"):
                    st.session_state.detailed_map_authorized = False
                    st.info("🔒 Detailed map access revoked")
                    st.rerun()
    
    return check_detailed_map_access()


def get_map_zoom_level() -> int:
    """
    Get the appropriate zoom level based on user authorization.
    Returns detailed zoom level if authorized, otherwise privacy-protected level.
    """
    from config.settings import MAX_ZOOM_LEVEL, DETAILED_MAP_MAX_ZOOM
    
    if check_detailed_map_access():
        return DETAILED_MAP_MAX_ZOOM
    else:
        return MAX_ZOOM_LEVEL


def get_map_access_status() -> dict:
    """
    Get the current map access status and settings.
    Returns a dictionary with access information.
    """
    from config.settings import MAX_ZOOM_LEVEL, DETAILED_MAP_MAX_ZOOM
    
    is_authorized = check_detailed_map_access()
    
    return {
        "is_authorized": is_authorized,
        "current_max_zoom": DETAILED_MAP_MAX_ZOOM if is_authorized else MAX_ZOOM_LEVEL,
        "access_level": "Detailed (Project Team)" if is_authorized else "Privacy Protected (Public)",
        "zoom_description": f"Up to level {DETAILED_MAP_MAX_ZOOM}" if is_authorized else f"Limited to level {MAX_ZOOM_LEVEL}"
    }
