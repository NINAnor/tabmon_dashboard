"""
Audio Dashboard Components
Provides reusable components for audio file browsing and playbook functionality.
"""

import pandas as pd
import streamlit as st

from components.ui_styles import render_info_section_header


def render_site_selection(site_info: pd.DataFrame) -> tuple:
    """Render country and site selection interface."""
    st.markdown("### 🌍 Site Selection")

    # Country filter
    countries = site_info["Country"].dropna().unique().tolist()
    selected_country = st.selectbox(
        "📍 Select Country", sorted(countries), key="audio_country_filter"
    )

    # Filter by country
    filtered_site_info = site_info[site_info["Country"] == selected_country]

    # Site filter
    sites = filtered_site_info["Site"].dropna().unique().tolist()
    selected_site = st.selectbox(
        "🏞️ Select Site", sorted(sites), key="audio_site_filter"
    )

    return selected_country, selected_site, filtered_site_info


def render_site_details(record: pd.Series) -> None:
    """Render site information details."""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🏞️ Site Information")
        st.markdown(f"**Country:** {record.get('Country', 'N/A')}")
        st.markdown(f"**Site:** {record.get('Site', 'N/A')}")
        st.markdown(f"**Cluster:** {record.get('Cluster', 'N/A')}")

    with col2:
        st.markdown("#### 🎙️ Device Information")
        st.markdown(f"**Device ID:** {record.get('DeviceID', 'N/A')}")
        st.markdown(f"**Deployment ID:** {record.get('DeploymentID', 'N/A')}")


def render_audio_stats(stats: dict, total_stats: dict = None) -> None:
    """Render audio statistics with dataset contribution information."""
    if not stats:
        return

    render_info_section_header("📊 Audio Statistics", style_class="audio-stats-header")

    # First row - site-specific stats
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("📼 Site Recordings", stats.get("total_recordings", 0))

    with col2:
        size_gb = stats.get("total_size_gb", 0)
        st.metric("💾 Site Size", f"{size_gb:.2f} GB")

    with col3:
        date_range = stats.get("date_range", {})
        if date_range.get("earliest") and date_range.get("latest"):
            days = (date_range["latest"] - date_range["earliest"]).days
            st.metric("📅 Date Range", f"{days} days")

    # Second row - dataset contribution stats (if total stats available)
    if total_stats:
        render_info_section_header(
            "🌐 Dataset Contribution",
            level="h4",
            style_class="dataset-contribution-header",
        )
        col4, col5, col6 = st.columns(3)

        with col4:
            total_recordings = total_stats.get("total_recordings", 0)
            site_recordings = stats.get("total_recordings", 0)

            if total_recordings > 0:
                percentage = (site_recordings / total_recordings) * 100
                st.metric(
                    "📊 Recordings Share",
                    f"{percentage:.2f}%",
                    delta=f"{site_recordings:,} of {total_recordings:,}",
                )
            else:
                st.metric("📊 Recordings Share", "N/A")

        with col5:
            total_size = total_stats.get("total_size_gb", 0)
            site_size = stats.get("total_size_gb", 0)

            if total_size > 0:
                size_percentage = (site_size / total_size) * 100
                st.metric(
                    "💾 Size Share",
                    f"{size_percentage:.2f}%",
                    delta=f"{site_size:.2f} GB of {total_size:.2f} GB",
                )
            else:
                st.metric("💾 Size Share", "N/A")

        with col6:
            st.metric("🗂️ Total Dataset", f"{total_recordings:,} recordings")
            st.caption(f"Total size: {total_size:.2f} GB")
