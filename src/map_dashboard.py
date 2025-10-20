"""
Enhanced TABMON Dashboard with modular architecture.
"""

import pandas as pd
import streamlit as st

from components.auth import get_map_access_status, render_detailed_map_auth
from components.charts import (
    render_activity_heatmap,
    render_country_bar_chart,
)
from components.filters import render_complete_filters
from components.map_viz import render_device_map
from components.metrics import render_status_metrics
from components.sidebar import render_complete_sidebar
from components.tables import render_status_table, render_summary_table
from components.ui_styles import (
    load_custom_css,
    render_info_section_header,
)
from config.settings import (
    APP_TITLE,
    TAB_ICONS,
)
from services.data_service import DataService


def app():
    """Main map dashboard application."""
    load_custom_css()

    # Initialize data service
    data_service = DataService()

    # Load all data
    with st.spinner("Loading device data..."):
        device_data = data_service.load_device_status()

    # Calculate metrics
    metrics = data_service.calculate_metrics(device_data)

    # Render sidebar with controls and metrics
    with st.sidebar:
        render_complete_sidebar(metrics=metrics)

    # Main dashboard tabs
    tab1, tab2, tab3 = st.tabs(
        [
            f"{TAB_ICONS['map']} Map View",
            f"{TAB_ICONS['status']} Device Status",
            f"{TAB_ICONS['activity']} Recording Activity",
        ]
    )

    with tab1:
        render_map_tab(device_data, data_service)

    with tab2:
        render_status_tab(device_data, metrics, data_service)

    with tab3:
        render_activity_tab(data_service)

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666; font-size: 0.9em;'>"
        f"{APP_TITLE} | Real-time Audio Device Monitoring | "
        f"Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}"
        "</div>",
        unsafe_allow_html=True,
    )


def render_map_tab(device_data: pd.DataFrame, data_service: DataService):
    """Render the interactive map tab."""
    st.markdown("### Device Locations and Status")

    # Authentication interface for detailed map access
    is_authorized = render_detailed_map_auth()

    # Show current access status
    access_status = get_map_access_status()

    if is_authorized:
        st.success(
            f"🔓 **{access_status['access_level']}** - "
            f"Zoom {access_status['zoom_description']} available"
        )
    else:
        st.info(
            f"🔒 **{access_status['access_level']}** - "
            f"Zoom {access_status['zoom_description']} for privacy protection"
        )

    # Filters for map view
    filtered_data, active_filters = render_complete_filters(
        device_data, key_prefix="map"
    )

    if not filtered_data.empty:
        # Get site info for the map
        site_info = data_service.load_site_info()

        # Render the interactive map with hardcoded zoom limits for privacy
        render_device_map(site_info, filtered_data)

        # Map summary statistics
        render_info_section_header(
            "🗺️ Map Summary", level="h4", style_class="map-summary-header"
        )

        # Show filtering info if devices are being filtered out
        total_devices = len(device_data)
        shown_devices = len(filtered_data)
        if shown_devices < total_devices:
            hidden_devices = total_devices - shown_devices
            st.info(
                f"Showing {shown_devices} of {total_devices} total devices. "
                f"{hidden_devices} devices are hidden by current filters."
            )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Devices Shown", len(filtered_data))
        with col2:
            online_count = len(filtered_data[filtered_data["status"] == "Online"])
            st.metric(
                "Online",
                online_count,
                delta=f"{online_count / len(filtered_data) * 100:.1f}%",
            )
        with col3:
            country_count = filtered_data["Country"].nunique()
            st.metric("Countries", country_count)
        with col4:
            site_count = (
                filtered_data["site_name"].nunique()
                if "site_name" in filtered_data.columns
                else 0
            )
            st.metric("Sites", site_count)
    else:
        st.warning(
            "⚠️ No devices match the current filter criteria. "
            "Please adjust your filters."
        )


def render_status_tab(
    device_data: pd.DataFrame, metrics: dict, data_service: DataService
):
    """Render the device status overview tab."""
    st.markdown("### Device Status Overview")

    # Display status metrics cards
    render_status_metrics(metrics)

    # Status visualizations
    st.markdown("#### Status by Country")
    render_country_bar_chart(device_data)

    # Detailed status table
    st.markdown("#### Detailed Device Status")

    # Filters for status table
    filtered_data, _ = render_complete_filters(device_data, key_prefix="status")

    if not filtered_data.empty:
        # Display options
        col1, col2, col3 = st.columns(3)

        with col2:
            sort_by = st.selectbox(
                "Sort by",
                ["device_name", "Country", "status", "last_file", "total_recordings"],
                index=2,  # Default to status
            )
        with col3:
            ascending = st.checkbox("Ascending order", value=False)

        # Sort and display table
        sorted_data = filtered_data.sort_values(by=sort_by, ascending=ascending)
        render_status_table(sorted_data)

        # Summary statistics
        render_info_section_header(
            "📊 Summary Statistics", level="h4", style_class="map-summary-header"
        )
        render_summary_table(filtered_data)
    else:
        st.warning("⚠️ No devices match the current filter criteria.")


def render_activity_tab(data_service: DataService):
    """Render the recording activity analysis tab."""
    st.markdown("### Recording Activity Analysis")

    # Load recording matrix data with day granularity
    with st.spinner("Loading daily activity data..."):
        recording_data = data_service.load_recording_matrix()

    if not recording_data.empty:
        # Activity heatmap
        st.markdown("#### Recording Activity Heatmap")
        render_activity_heatmap(recording_data)


if __name__ == "__main__":
    app()
