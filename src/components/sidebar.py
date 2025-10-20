"""
Sidebar components for the TABMON dashboard.
"""

import streamlit as st

def render_dashboard_sidebar(metrics: dict = None):
    """Render the enhanced dashboard sidebar without time granularity control."""
    
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

    st.markdown("---")


def render_about_section():
    """Render about information in the sidebar."""
    with st.expander("ℹ️ About TABMON", expanded=False):
        st.markdown("""
        **TABMON** develops a transnational biodiversity monitoring network using
        acoustic sensors across Europe, demonstrating how acoustic
        monitoring complements existing monitoring to address EU directive gaps and
        Biodiversity Strategy targets.

        You can find more info on [our website](https://tabmon-eu.nina.no/) or
        """)


def render_complete_sidebar(metrics: dict = None):
    """Render the complete sidebar with all components."""
    render_dashboard_sidebar(metrics)
    render_about_section()
