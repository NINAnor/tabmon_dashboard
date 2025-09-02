"""
Audio Dashboard for TABMON - Modernized Version
Provides audio file browsing, filtering, and playback functionality.
"""

import os
import requests
from datetime import datetime, timezone
from urllib.parse import unquote

import duckdb
import pandas as pd
import streamlit as st

from config.settings import COUNTRY_MAP, ASSETS_SITE_CSV, ASSETS_PARQUET_FILE
from services.data_service import DataService
from components.ui_styles import load_custom_css
from components.sidebar import render_complete_sidebar
from utils.data_loader import load_site_info, parse_file_datetime


class AudioService:
    """Service for handling audio file operations and data processing."""
    
    def __init__(self, parquet_file: str):
        self.parquet_file = parquet_file
    
    @st.cache_data(ttl=3600, show_spinner=False)
    def get_audio_files_by_device(_self, short_device_id: str) -> pd.DataFrame:
        """Get all audio files for a specific device."""
        try:
            # Check if we're dealing with a URL or local file
            if _self.parquet_file.startswith(('http://', 'https://')):
                # For URLs, load all data then filter
                data = pd.read_parquet(_self.parquet_file)
                # Filter for audio files and specific device
                audio_data = data[
                    (data["MimeType"] == 'audio/mpeg') &
                    (data["device"].str.endswith(short_device_id))
                ]
            else:
                # For local files, use DuckDB for efficient filtering
                query = """
                SELECT *
                FROM read_parquet(?)
                WHERE MimeType = 'audio/mpeg'
                AND RIGHT(device, 8) = ?
                """
                audio_data = duckdb.execute(query, (_self.parquet_file, short_device_id)).df()
            
            if audio_data.empty:
                return pd.DataFrame()
            
            # Parse recording timestamps from filenames
            audio_data = audio_data.copy()  # Prevent SettingWithCopyWarning
            audio_data["recorded_at"] = audio_data["Name"].apply(parse_file_datetime)
            audio_data = audio_data.dropna(subset=["recorded_at"])
            
            # Sort by recording time (newest first)
            audio_data = audio_data.sort_values(by="recorded_at", ascending=False)
            
            return audio_data
        except Exception as e:
            st.error(f"Failed to load audio files: {e}")
            return pd.DataFrame()
    
    def find_closest_recordings(self, audio_data: pd.DataFrame, target_datetime: datetime, limit: int = 10) -> pd.DataFrame:
        """Find recordings closest to a target datetime."""
        if audio_data.empty:
            return pd.DataFrame()
        
        # Calculate absolute time difference
        audio_data = audio_data.copy()
        audio_data["time_diff"] = (audio_data["recorded_at"] - target_datetime).abs()
        
        # Sort by time difference and limit results
        closest_recordings = audio_data.sort_values(by="time_diff").head(limit)
        
        return closest_recordings
    
    def get_audio_stats(self, audio_data: pd.DataFrame) -> dict:
        """Calculate statistics for audio data."""
        if audio_data.empty:
            return {}
        
        return {
            'total_recordings': len(audio_data),
            'date_range': {
                'earliest': audio_data['recorded_at'].min(),
                'latest': audio_data['recorded_at'].max()
            },
            'total_size_gb': audio_data['Size'].sum() / (1024 * 1024 * 1024) if 'Size' in audio_data.columns else 0
        }
    
    @st.cache_data(ttl=3600, show_spinner=False)
    def get_total_dataset_stats(_self) -> dict:
        """Get statistics for the entire audio dataset."""
        try:
            # Check if we're dealing with a URL or local file
            if _self.parquet_file.startswith(('http://', 'https://')):
                # For URLs, load all data then filter
                data = pd.read_parquet(_self.parquet_file)
                # Filter for audio files only
                audio_data = data[data["MimeType"] == 'audio/mpeg']
            else:
                # For local files, use DuckDB for efficient filtering
                query = """
                SELECT COUNT(*) as total_recordings, SUM(Size) as total_size_bytes
                FROM read_parquet(?)
                WHERE MimeType = 'audio/mpeg'
                """
                result = duckdb.execute(query, (_self.parquet_file,)).df()
                return {
                    'total_recordings': int(result['total_recordings'].iloc[0]) if not result.empty else 0,
                    'total_size_gb': float(result['total_size_bytes'].iloc[0]) / (1024 * 1024 * 1024) if not result.empty and pd.notna(result['total_size_bytes'].iloc[0]) else 0
                }
            
            if audio_data.empty:
                return {'total_recordings': 0, 'total_size_gb': 0}
            
            return {
                'total_recordings': len(audio_data),
                'total_size_gb': audio_data['Size'].sum() / (1024 * 1024 * 1024) if 'Size' in audio_data.columns else 0
            }
        except Exception as e:
            st.error(f"Failed to load total dataset stats: {e}")
            return {'total_recordings': 0, 'total_size_gb': 0}


def get_auth_credentials():
    """Read authentication credentials from environment variables."""
    username = os.getenv('AUTH_USERNAME')
    password = os.getenv('AUTH_PASSWORD')
    
    if username and password:
        return (username, password)
    
    # No fallback - require explicit configuration
    raise ValueError("Authentication credentials not found. Please set AUTH_USERNAME and AUTH_PASSWORD environment variables.")


def render_site_selection(site_info: pd.DataFrame) -> tuple:
    """Render country and site selection interface."""
    st.markdown("### 🌍 Site Selection")
    
    # Country filter
    countries = site_info["Country"].dropna().unique().tolist()
    selected_country = st.selectbox(
        "📍 Select Country", 
        sorted(countries),
        key="audio_country_filter"
    )
    
    # Filter by country
    filtered_site_info = site_info[site_info["Country"] == selected_country]
    
    # Site filter
    sites = filtered_site_info["Site"].dropna().unique().tolist()
    selected_site = st.selectbox(
        "🏞️ Select Site", 
        sorted(sites),
        key="audio_site_filter"
    )
    
    return selected_country, selected_site, filtered_site_info


def render_datetime_selector() -> datetime:
    """Render date and time selection interface."""
    st.markdown("### ⏰ Recording Time")
    
    # Date and time inputs
    selected_date = st.date_input(
        "📅 Select Date", 
        value=datetime.now().date(),
        key="audio_date_filter"
    )
    
    selected_time = st.time_input(
        "🕐 Select Time", 
        value=datetime.now().time(),
        key="audio_time_filter"
    )
    
    # Combine date and time
    selected_datetime = datetime.combine(selected_date, selected_time).replace(
        tzinfo=timezone.utc
    )
    
    return selected_datetime


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
    
    st.markdown("### 📊 Audio Statistics")
    
    # First row - site-specific stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📼 Site Recordings", stats.get('total_recordings', 0))
    
    with col2:
        size_gb = stats.get('total_size_gb', 0)
        st.metric("💾 Site Size", f"{size_gb:.2f} GB")
    
    with col3:
        date_range = stats.get('date_range', {})
        if date_range.get('earliest') and date_range.get('latest'):
            days = (date_range['latest'] - date_range['earliest']).days
            st.metric("📅 Date Range", f"{days} days")
    
    # Second row - dataset contribution stats (if total stats available)
    if total_stats:
        st.markdown("#### 🌐 Dataset Contribution")
        col4, col5, col6 = st.columns(3)
        
        with col4:
            total_recordings = total_stats.get('total_recordings', 0)
            site_recordings = stats.get('total_recordings', 0)
            
            if total_recordings > 0:
                percentage = (site_recordings / total_recordings) * 100
                st.metric(
                    "📊 Recordings Share", 
                    f"{percentage:.2f}%",
                    delta=f"{site_recordings:,} of {total_recordings:,}"
                )
            else:
                st.metric("📊 Recordings Share", "N/A")
        
        with col5:
            total_size = total_stats.get('total_size_gb', 0)
            site_size = stats.get('total_size_gb', 0)
            
            if total_size > 0:
                size_percentage = (site_size / total_size) * 100
                st.metric(
                    "💾 Size Share", 
                    f"{size_percentage:.2f}%",
                    delta=f"{site_size:.2f} GB of {total_size:.2f} GB"
                )
            else:
                st.metric("💾 Size Share", "N/A")
        
        with col6:
            st.metric("🗂️ Total Dataset", f"{total_recordings:,} recordings")
            st.caption(f"Total size: {total_size:.2f} GB")


def render_recordings_table(recordings: pd.DataFrame, target_datetime: datetime) -> str:
    """Render recordings table and return selected file path."""
    if recordings.empty:
        st.info("📂 No recordings found for the selected criteria.")
        return None
    
    st.markdown("### 🎵 Closest Recordings")
    
    # Prepare display data
    display_data = recordings.copy()
    display_data["Recording Time"] = display_data["recorded_at"].dt.strftime("%Y-%m-%d %H:%M:%S")
    display_data["Time Difference"] = display_data["time_diff"].apply(
        lambda x: f"{x.total_seconds() / 3600:.1f}h" if x.total_seconds() > 3600 
        else f"{x.total_seconds() / 60:.0f}m"
    )
    display_data["File Size"] = display_data["Size"].apply(
        lambda x: f"{x / (1024*1024):.1f} MB" if pd.notna(x) else "Unknown"
    )
    
    # Show table
    st.dataframe(
        display_data[["Name", "Recording Time", "Time Difference", "File Size"]],
        use_container_width=True,
        hide_index=True
    )
    
    # File selection
    st.markdown("### 🎧 Select Audio File")
    file_options = [(f"{row['Name']} ({row['Recording Time']})", row['Path']) 
                   for _, row in display_data.iterrows()]
    
    selected_option = st.selectbox(
        "Choose a recording to play:",
        options=[option[0] for option in file_options],
        key="audio_file_selector"
    )
    
    if selected_option:
        # Find the corresponding path
        selected_path = next(path for label, path in file_options if label == selected_option)
        return selected_path
    
    return None


def render_audio_player(file_path: str) -> None:
    """Render audio player with authentication."""
    if not file_path:
        return
    
    st.markdown("### 🎵 Audio Player")
    
    try:
        # Construct the full URL
        audio_url = f"/data/{file_path}"
        
        # For Docker environment, we need to use authenticated requests
        if audio_url.startswith('/data/'):
            full_url = f"http://reverseproxy:80{audio_url}"
            
            try:
                # Get authentication credentials
                auth = get_auth_credentials()
                
                # Fetch the audio file with authentication
                response = requests.get(full_url, auth=auth, timeout=30)
                
                if response.status_code == 200:
                    # Display the audio player using Streamlit's native audio component
                    st.audio(response.content, format='audio/mp3')
                    
                    # Show file info
                    file_size = len(response.content) / (1024 * 1024)
                    st.success(f"✅ Audio loaded successfully ({file_size:.1f} MB)")
                else:
                    st.error(f"❌ Failed to load audio file: HTTP {response.status_code}")
            except Exception as e:
                st.error(f"❌ Authentication error: {str(e)}")
                # Fallback to HTML audio tag (may not work without auth)
                st.markdown(
                    f'<audio controls style="width: 100%"><source src="{audio_url}" type="audio/mpeg"></audio>',
                    unsafe_allow_html=True
                )
        else:
            # For local files, use direct URL
            st.audio(audio_url, format='audio/mp3')
            
    except Exception as e:
        st.error(f"❌ Error loading audio: {str(e)}")


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
    st.markdown(f"## 📍 {selected_site}")
    
    # Render site details
    render_site_details(record)
    
    # Extract device ID
    full_device_id = record.get("DeviceID", "")
    if "_" in full_device_id:
        short_device_id = full_device_id.split("_")[-1].strip()
    else:
        short_device_id = full_device_id[-8:] if len(full_device_id) >= 8 else full_device_id
    
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
    st.markdown("### 🔧 Additional Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Export Recording List", key="export_recordings"):
            csv_data = closest_recordings[["Name", "recorded_at", "Path", "Size"]].to_csv(index=False)
            st.download_button(
                label="💾 Download as CSV",
                data=csv_data,
                file_name=f"recordings_{selected_site}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="download_recordings_csv"
            )
    
    with col2:
        # Show recording frequency
        if len(audio_data) > 1:
            time_diffs = audio_data.sort_values('recorded_at')['recorded_at'].diff().dropna()
            avg_interval = time_diffs.mean()
            if pd.notna(avg_interval):
                interval_hours = avg_interval.total_seconds() / 3600
                st.info(f"📊 Average recording interval: {interval_hours:.1f} hours")
