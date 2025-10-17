"""
Sidebar components for the TABMON dashboard.
"""

import streamlit as st

from components.metrics import render_sidebar_metrics


def render_dashboard_sidebar(metrics: dict = None):
    """Render the enhanced dashboard sidebar."""

    # Sidebar header
    st.markdown(
        """
    <div class='sidebar-header'>
        <h2 style='margin: 0;'>🎛️ Dashboard Controls</h2>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Time granularity control
    time_granularity = st.radio(
        "**Time Granularity**",
        ["Day", "Week", "Month"],
        index=0,
        help="Choose how to aggregate recording data over time",
    )

    st.markdown("---")

    # Show metrics if provided
    if metrics:
        render_sidebar_metrics(metrics)
        st.markdown("---")

    # Dashboard info
    st.markdown(
        """
    <div class='info-box'>
        <h4 style='color: #2E86AB; margin-top: 0;'>📋 Dashboard Info</h4>
        <p style='margin-bottom: 0; font-size: 0.9em;'>
            This dashboard provides real-time monitoring of TABMON audio recording
            devices across multiple countries. Use the tabs above to explore
            different views of your data.
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Status legend
    st.markdown(
        """
    <div class='legend-box'>
        <h4 style='color: #2E86AB; margin-top: 0;'>🏷️ Status Legend</h4>
        <p style='margin: 0.5rem 0;'>
            <span style='color: green; font-weight: bold;'>🟢 Online:</span>
            Active within 3 days
        </p>
        <p style='margin: 0.5rem 0;'>
            <span style='color: red; font-weight: bold;'>🔴 Offline:</span>
            No activity > 3 days
        </p>
        <p style='margin: 0.5rem 0; font-size: 0.8em; color: #666;'>
            <em>Status is determined by the last recorded audio file timestamp.</em>
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    return time_granularity


def render_dashboard_sidebar_without_granularity(metrics: dict = None):
    """Render the enhanced dashboard sidebar without time granularity control."""

    # Dashboard info
    st.markdown(
        """
    <div class='info-box'>
        <h4 style='color: #2E86AB; margin-top: 0;'>📋 Dashboard Info</h4>
        <p style='margin-bottom: 0; font-size: 0.9em;'>
            Real-time monitoring of TABMON audio recording devices
            across multiple countries. Navigate using the tabs above to explore
            different data views.
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Status Summary
    if metrics:
        total_devices = metrics.get("total_devices", 0)
        online_devices = metrics.get("online_devices", 0)
        offline_devices = metrics.get("offline_devices", 0)

        if total_devices > 0:
            online_percentage = (online_devices / total_devices) * 100
            offline_percentage = (offline_devices / total_devices) * 100

            st.markdown(
                """
            <div class='status-summary-box'>
                <h4 style='color: #2E86AB; margin-top: 0;'>📊 Device Status Summary</h4>
            </div>
            """,
                unsafe_allow_html=True,
            )

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    label="🟢 Online",
                    value=f"{online_devices}",
                    delta=f"{online_percentage:.1f}%",
                )

            with col2:
                st.metric(
                    label="🔴 Offline",
                    value=f"{offline_devices}",
                    delta=f"{offline_percentage:.1f}%",
                )

            # Total devices
            st.metric(label="📱 Total Devices", value=f"{total_devices}")

    st.markdown("---")

    # Status legend
    st.markdown(
        """
    <div class='legend-box'>
        <h4 style='color: #2E86AB; margin-top: 0;'>🏷️ Status Legend</h4>
        <p style='margin: 0.5rem 0;'>
            <span style='color: green; font-weight: bold;'>🟢 Online:</span>
            Active within 3 days
        </p>
        <p style='margin: 0.5rem 0;'>
            <span style='color: red; font-weight: bold;'>🔴 Offline:</span>
            No activity > 3 days
        </p>
        <p style='margin: 0.5rem 0; font-size: 0.8em; color: #666;'>
            <em>Status is determined by the last recorded audio file timestamp.</em>
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_help_section():
    """Render help and documentation in the sidebar."""
    with st.expander("❓ Help & Documentation", expanded=False):
        st.markdown("""
        **Navigation Tips:**
        - 🗺️ **Map View**: See device locations and real-time status
        - 📊 **Device Status**: View detailed metrics and tables
        - 📈 **Recording Activity**: Analyze activity patterns over time

        **Status Understanding:**
        - Devices are **Online** if they recorded audio within 3 days
        - **Offline** devices haven't recorded for more than 3 days
        - Click map markers for detailed device information
        """)


def render_about_section():
    """Render about information in the sidebar."""
    with st.expander("ℹ️ About TABMON", expanded=False):
        st.markdown("""
        **TABMON** develops transnational biodiversity monitoring using autonomous
        acoustic sensors across Europe's latitudinal range, demonstrating how acoustic
        sensing complements existing monitoring to address EU directive gaps and
        Biodiversity Strategy targets.

        **Three Work Packages:**
        1. **Transnational Network** - Deploying acoustic monitoring infrastructure
        2. **AI Analytics** - Deriving Essential Biodiversity Variables (EBV) to
           assess ecosystem and species health
        3. **Policy Impact** - Showcasing results to inform decision makers

        This dashboard monitors operational status of deployed audio recording devices
        across multiple countries and research sites.

        For technical support, contact the TABMON team.
        """)


def render_complete_sidebar(metrics: dict = None):
    """Render the complete sidebar with all components."""
    render_dashboard_sidebar_without_granularity(metrics)
    render_help_section()
    render_about_section()
