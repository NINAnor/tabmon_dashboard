"""
Metrics components for the TABMON dashboard.
"""

import streamlit as st


def render_status_metrics(metrics: dict):
    """Render status metrics with improved styling."""
    if not metrics:
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
        <div class='metric-card status-total'>
            <h2 style='margin: 0; font-size: 2.5em;'>📡</h2>
            <h3 style='margin: 0.5rem 0; font-size: 2em;'>
                {metrics["total_devices"]}
            </h3>
            <p style='margin: 0; font-size: 1.1em;'>Total Devices</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
        <div class='metric-card status-online'>
            <h2 style='margin: 0; font-size: 2.5em;'>✅</h2>
            <h3 style='margin: 0.5rem 0; font-size: 2em;'>
                {metrics["online_devices"]}
            </h3>
            <p style='margin: 0; font-size: 1.1em;'>
                Online ({metrics["online_percentage"]:.1f}%)
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
        <div class='metric-card status-offline'>
            <h2 style='margin: 0; font-size: 2.5em;'>❌</h2>
            <h3 style='margin: 0.5rem 0; font-size: 2em;'>
                {metrics["offline_devices"]}
            </h3>
            <p style='margin: 0; font-size: 1.1em;'>
                Offline ({metrics["offline_percentage"]:.1f}%)
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )


def render_sidebar_metrics(metrics: dict):
    """Render compact metrics in the sidebar."""
    if not metrics:
        return

    st.markdown(
        f"""
    <div class='info-box'>
        <h4 style='color: #2E86AB; margin-top: 0;'>📊 Quick Stats</h4>
        <p style='margin: 0.5rem 0;'>
            <strong>Total:</strong> {metrics["total_devices"]} devices
        </p>
        <p style='margin: 0.5rem 0;'>
            <strong>Online:</strong> {metrics["online_devices"]}
            ({metrics["online_percentage"]:.1f}%)
        </p>
        <p style='margin: 0.5rem 0;'>
            <strong>Offline:</strong> {metrics["offline_devices"]}
            ({metrics["offline_percentage"]:.1f}%)
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )
