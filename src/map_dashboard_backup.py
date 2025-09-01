"""
Enhanced TABMON Dashboard with modular architecture.
"""

import streamlit as st
import pandas as pd
from config.settings import (
    APP_TITLE, ASSETS_SITE_CSV, ASSETS_PARQUET_FILE, 
    TAB_ICONS, DEFAULT_MAP_ZOOM
)
from services.data_service import DataService
from components.ui_styles import load_custom_css, render_page_header
from components.metrics import render_status_metrics
from components.map_viz import render_device_map
from components.tables import render_status_table, render_summary_table
from components.charts import render_activity_heatmap, render_status_pie_chart, render_country_bar_chart
from components.sidebar import render_complete_sidebar
from components.filters import render_complete_filters



def app():
    """Main application entry point for the TABMON Dashboard."""
    
    # Initialize styling and page configuration
    load_custom_css()
    render_page_header(APP_TITLE, "🗺️")
    
    # Initialize data service
    data_service = DataService()
    
    # Load all data
    with st.spinner("Loading device data..."):
        device_data = data_service.load_device_status()
        site_info = data_service.load_site_info()
        
    # Calculate metrics
    metrics = data_service.calculate_metrics(device_data)
    
    # Render sidebar with controls and metrics
    with st.sidebar:
        time_granularity = render_complete_sidebar(
            metrics=metrics,
            site_csv=ASSETS_SITE_CSV,
            parquet_file=ASSETS_PARQUET_FILE
        )
    
    # Main dashboard tabs
    tab1, tab2, tab3 = st.tabs([
        f"{TAB_ICONS['map']} Map View", 
        f"{TAB_ICONS['status']} Device Status", 
        f"{TAB_ICONS['activity']} Recording Activity"
    ])
    
    with tab1:
        render_map_tab(device_data, data_service)
    
    with tab2:
        render_status_tab(device_data, metrics, data_service)
    
    with tab3:
        render_activity_tab(time_granularity, data_service)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666; font-size: 0.9em;'>"
        f"{APP_TITLE} | Real-time Audio Device Monitoring | "
        f"Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}"
        "</div>", 
        unsafe_allow_html=True
    )


def render_map_tab(device_data: pd.DataFrame, data_service: DataService):
    """Render the interactive map tab."""
    st.markdown("### 🗺️ Device Locations and Real-time Status")
    
    # Filters for map view
    filtered_data, active_filters = render_complete_filters(device_data)
    
    if not filtered_data.empty:
        # Render the interactive map
        render_device_map(filtered_data)
        
        # Map summary statistics
        st.markdown("#### 📊 Map Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Devices Shown", len(filtered_data))
        with col2:
            online_count = len(filtered_data[filtered_data['status'] == 'Online'])
            st.metric("Online", online_count, delta=f"{online_count/len(filtered_data)*100:.1f}%")
        with col3:
            country_count = filtered_data['Country'].nunique()
            st.metric("Countries", country_count)
        with col4:
            site_count = filtered_data['site_name'].nunique() if 'site_name' in filtered_data.columns else 0
            st.metric("Sites", site_count)
    else:
        st.warning("⚠️ No devices match the current filter criteria. Please adjust your filters.")


def render_status_tab(device_data: pd.DataFrame, metrics: dict, data_service: DataService):
    """Render the device status overview tab."""
    st.markdown("### 📊 Device Status Overview")
    
    # Display status metrics cards
    render_status_metrics(metrics)
    
    # Status visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🥧 Status Distribution")
        render_status_pie_chart(device_data)
    
    with col2:
        st.markdown("#### 🌍 Status by Country")
        render_country_bar_chart(device_data)
    
    # Detailed status table
    st.markdown("#### 📋 Detailed Device Status")
    
    # Filters for status table
    filtered_data, _ = render_complete_filters(device_data)
    
    if not filtered_data.empty:
        # Display options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            show_all_columns = st.checkbox("Show all columns", value=False)
        with col2:
            sort_by = st.selectbox(
                "Sort by", 
                ["device_name", "Country", "status", "last_file", "total_recordings"],
                index=2  # Default to status
            )
        with col3:
            ascending = st.checkbox("Ascending order", value=False)
        
        # Sort and display table
        sorted_data = filtered_data.sort_values(by=sort_by, ascending=ascending)
        render_status_table(sorted_data, show_all_columns=show_all_columns)
        
        # Summary statistics
        st.markdown("#### 📈 Summary Statistics")
        render_summary_table(filtered_data)
    else:
        st.warning("⚠️ No devices match the current filter criteria.")


def render_activity_tab(time_granularity: str, data_service: DataService):
    """Render the recording activity analysis tab."""
    st.markdown("### 📈 Recording Activity Analysis")
    
    # Load recording matrix data based on time granularity
    with st.spinner(f"Loading {time_granularity.lower()} activity data..."):
        recording_data = data_service.load_recording_matrix(time_granularity.lower())
    
    if not recording_data.empty:
        # Activity heatmap
        st.markdown(f"#### 🔥 Recording Activity Heatmap ({time_granularity})")
        render_activity_heatmap(recording_data, time_granularity)
        
        # Activity insights
        st.markdown("#### 💡 Activity Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Most active devices
            device_totals = recording_data.groupby('device_name')['recording_count'].sum().sort_values(ascending=False)
            
            st.markdown("**🏆 Most Active Devices**")
            top_devices = device_totals.head(10)
            for device, count in top_devices.items():
                st.write(f"• **{device}**: {count:,} recordings")
        
        with col2:
            # Activity statistics
            total_recordings = recording_data['recording_count'].sum()
            avg_per_device = recording_data.groupby('device_name')['recording_count'].sum().mean()
            active_periods = recording_data[recording_data['recording_count'] > 0].shape[0]
            
            st.markdown("**📊 Activity Statistics**")
            st.write(f"• **Total recordings**: {total_recordings:,}")
            st.write(f"• **Average per device**: {avg_per_device:.1f}")
            st.write(f"• **Active periods**: {active_periods:,}")
            st.write(f"• **Coverage**: {len(recording_data['device_name'].unique())} devices")
        
        # Downloadable data
        st.markdown("#### 💾 Export Data")
        
        csv_data = recording_data.to_csv(index=False)
        st.download_button(
            label="📥 Download activity data as CSV",
            data=csv_data,
            file_name=f"tabmon_activity_{time_granularity.lower()}_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            help="Download the current activity data for further analysis"
        )
    else:
        st.warning("⚠️ No recording activity data available for the selected time granularity.")
        st.info("💡 This might be due to missing data or no recordings in the specified time period.")


# Legacy function for backward compatibility
def show_map_dashboard(site_csv: str, parquet_file: str) -> None:
    """Legacy function for backward compatibility."""
    app()


if __name__ == "__main__":
    app()


@st.cache_data(ttl=3600, show_spinner=False)
def load_and_process_data(parquet_file: str, site_csv: str, time_granularity: str = "Day") -> Tuple[pd.DataFrame, str]:
    """Load and process data for visualization."""
    
    # Load parquet data with optimized query
    query = """
    SELECT *,
        COALESCE(
            TRY_STRPTIME(Name, '%Y-%m-%dT%H_%M_%S.%fZ.mp3'),
            TRY_STRPTIME(Name, '%Y-%m-%dT%H_%M_%SZ.mp3'),
            STRPTIME(Name, '%Y-%m-%dT%H_%MZ.mp3')
        ) AS datetime
    FROM read_parquet(?)
    WHERE MimeType = 'audio/mpeg'
    AND datetime >= ?
    """
    
    data = duckdb.execute(query, (parquet_file, DATA_START_DATE)).df()
    
    if data.empty:
        return pd.DataFrame(), time_granularity
    
    # Extract device ID from path
    data["short_device_id"] = (
        data["Path"]
        .str.split("/").str[-3]
        .str.split("-").str[-1]
        .str[-8:].str.strip()
    )
    
    # Load site info
    site_info = load_site_info(site_csv)
    site_info = site_info[site_info["Active"] == True].copy()
    site_info["clean_id"] = site_info["DeploymentID"].str.strip()
    data["clean_id"] = data["short_device_id"].str.strip()
    
    # Merge data
    df_merged = pd.merge(data, site_info, on="clean_id", how="left")
    
    # Map countries using the constant
    for code, country_name in COUNTRY_MAP.items():
        df_merged.loc[df_merged['country'] == code, 'Country'] = country_name
    
    # Create time periods based on granularity
    if time_granularity == "Day":
        df_merged["time_period"] = df_merged["datetime"].dt.to_period("D").astype(str)
    elif time_granularity == "Week":
        df_merged["time_period"] = df_merged["datetime"].dt.to_period("W").astype(str)
    else:  # Month
        df_merged["time_period"] = df_merged["datetime"].dt.to_period("M").astype(str)
    
    # Create matrix
    matrix_data = pd.crosstab(
        index=[df_merged["Country"], df_merged["device"]],
        columns=df_merged["time_period"],
        values=df_merged["datetime"],
        aggfunc="count"
    ).fillna(0)
    
    return matrix_data.sort_index(), time_granularity


@st.cache_data(ttl=3600, show_spinner=False)
def get_status_table(parquet_file: str, site_info: pd.DataFrame, offline_threshold_days: int = 3) -> pd.DataFrame:
    """Get device status table with site information."""
    df_status = get_device_status_by_recorded_at(parquet_file, offline_threshold_days)
    if df_status.empty:
        return pd.DataFrame()

    site_info["short_device"] = site_info["DeploymentID"].apply(
        lambda x: x.split("_")[-1].strip().lower()
    )

    merged = pd.merge(site_info, df_status, on="short_device", how="left")
    merged["status"] = merged["status"].fillna("Offline")
    merged["last_recorded"] = merged["recorded_at"]

    now = datetime.now(timezone.utc)
    merged["days_since_last"] = (
        (now - merged["last_recorded"]).dt.total_seconds() / 86400
    ).round(1)

    return merged


def render_status_metrics(status_df: pd.DataFrame) -> None:
    """Render status metrics with improved styling."""
    if status_df.empty:
        return
        
    total_devices = len(status_df)
    online_devices = len(status_df[status_df["status"] == "Online"])
    offline_devices = total_devices - online_devices
    online_pct = (online_devices/total_devices*100) if total_devices > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 1.5rem; border-radius: 15px; color: white; text-align: center;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);'>
            <h2 style='margin: 0; font-size: 2.5em;'>📡</h2>
            <h3 style='margin: 0.5rem 0; font-size: 2em;'>{total_devices}</h3>
            <p style='margin: 0; font-size: 1.1em;'>Total Devices</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); 
                    padding: 1.5rem; border-radius: 15px; color: white; text-align: center;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);'>
            <h2 style='margin: 0; font-size: 2.5em;'>✅</h2>
            <h3 style='margin: 0.5rem 0; font-size: 2em;'>{online_devices}</h3>
            <p style='margin: 0; font-size: 1.1em;'>Online ({online_pct:.1f}%)</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #ff6b6b 0%, #feca57 100%); 
                    padding: 1.5rem; border-radius: 15px; color: white; text-align: center;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);'>
            <h2 style='margin: 0; font-size: 2.5em;'>❌</h2>
            <h3 style='margin: 0.5rem 0; font-size: 2em;'>{offline_devices}</h3>
            <p style='margin: 0; font-size: 1.1em;'>Offline ({100-online_pct:.1f}%)</p>
        </div>
        """, unsafe_allow_html=True)


def render_map(site_info: pd.DataFrame, status_df: pd.DataFrame) -> None:
    """Render the interactive map with improved styling."""
    if site_info.empty:
        st.warning("⚠️ No site information available")
        return
    
    # Create map centered on device locations
    center_lat = site_info["Latitude"].mean()
    center_lon = site_info["Longitude"].mean()
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=6,
        tiles="OpenStreetMap"
    )
    
    marker_cluster = MarkerCluster().add_to(m)
    
    # Add markers with improved styling
    for _, row in status_df.iterrows():
        location_text = f"{row['Cluster']}: {row['Site']}"
        popup_html = f"""
        <div style="font-family: Arial, sans-serif;">
            <h4 style="margin: 0; color: #2E86AB;">🎙️ {row['DeploymentID']}</h4>
            <hr style="margin: 5px 0;">
            <p><b>📍 Site:</b> {location_text}</p>
            <p><b>🌍 Country:</b> {row['Country']}</p>
            <p><b>📶 Status:</b> 
                <span style="color: {'green' if row['status'] == 'Online' else 'red'};">
                    {row['status']}
                </span>
            </p>
        </div>
        """
        
        # Status-based styling
        icon_color = "green" if row["status"] == "Online" else "red"
        icon_symbol = "play" if row["status"] == "Online" else "pause"
        
        folium.Marker(
            location=[row["Latitude"], row["Longitude"]],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"🎙️ {row['Site']} ({row['status']})",
            icon=folium.Icon(
                color=icon_color, 
                icon=icon_symbol, 
                prefix="fa"
            ),
        ).add_to(marker_cluster)
    
    return st_folium(m, width=1200, height=600)


def render_status_table(status_df: pd.DataFrame) -> None:
    """Render improved status table."""
    if status_df.empty:
        st.info("ℹ️ No device status data available")
        return
    
    # Prepare display data
    display_cols = ["Cluster", "Site", "DeploymentID", "Country", "status", "last_recorded", "days_since_last"]
    table_data = status_df[display_cols].copy()
    
    # Format dates and handle NaN values
    table_data["last_recorded"] = table_data["last_recorded"].dt.strftime("%Y-%m-%d %H:%M")
    table_data["days_since_last"] = table_data["days_since_last"].fillna("N/A")
    
    # Style function for better visual appeal
    def style_status(row):
        if row["status"] == "Online":
            return ["background-color: #d4edda; color: #155724"] * len(row)
        else:
            return ["background-color: #f8d7da; color: #721c24"] * len(row)
    
    st.dataframe(
        table_data.style.apply(style_status, axis=1),
        use_container_width=True,
        height=400
    )


def render_activity_heatmap(matrix_data: pd.DataFrame, period_title: str) -> None:
    """Render improved activity heatmap."""
    if matrix_data.empty:
        st.info("ℹ️ No recording data available")
        return
    
    # Prepare data for visualization
    ytick_labels = []
    prev_country = None
    
    for country, device in matrix_data.index:
        if country != prev_country:
            ytick_labels.append(f"<b>{country}</b> - {device}")
            prev_country = country
        else:
            ytick_labels.append(f"     {device}")
    
    # Reverse for top-down display
    ytick_labels = ytick_labels[::-1]
    z_data = matrix_data.values[::-1]
    x_labels = matrix_data.columns.tolist()
    
    # Create improved heatmap
    fig = go.Figure(
        data=go.Heatmap(
            z=z_data,
            x=x_labels,
            y=ytick_labels,
            colorscale="Viridis",
            colorbar=dict(
                title="📊 Recordings",
                titleside="right"
            ),
            hoverongaps=False,
            hovertemplate=f"<b>{period_title}:</b> %{{x}}<br><b>Device:</b> %{{y}}<br><b>Recordings:</b> %{{z}}<extra></extra>",
        )
    )
    
    fig.update_layout(
        title=f"🎵 Recording Activity by {period_title}",
        xaxis_title=f"📅 {period_title}",
        yaxis_title="🎙️ Device (by Country)",
        height=max(500, len(matrix_data) * 25),
        margin=dict(l=200, r=50, t=80, b=50),
        font=dict(size=12),
        title_font_size=16
    )
    
    st.plotly_chart(fig, use_container_width=True)


def show_map_dashboard(site_csv: str, parquet_file: str) -> None:
    """Main dashboard function with improved UI/UX."""
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main > div {
        padding-top: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
        border-radius: 10px;
        background-color: #f0f2f6;
        border: 1px solid #ddd;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2E86AB;
        color: white;
    }
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .stAlert > div {
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main title with styling
    st.markdown("""
    <h1 style='text-align: center; color: #2E86AB; margin-bottom: 30px;'>
        🎙️ TABMON Device Monitoring Dashboard
    </h1>
    <hr style='margin-bottom: 30px;'>
    """, unsafe_allow_html=True)
    
    # Load data with spinner
    with st.spinner("🔄 Loading data..."):
        site_info = load_site_info(site_csv)
        site_info = site_info[site_info["Active"] == True]
        status_df = get_status_table(parquet_file, site_info, OFFLINE_THRESHOLD_DAYS)
    
    if status_df.empty:
        st.error("❌ No data available. Please check your data files.")
        return
    
    # Sidebar controls with improved styling
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; padding: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    border-radius: 10px; color: white; margin-bottom: 1rem;'>
            <h2 style='margin: 0;'>🎛️ Dashboard Controls</h2>
        </div>
        """, unsafe_allow_html=True)
        
        time_granularity = st.radio(
            "📊 **Time Granularity**",
            ["Day", "Week", "Month"],
            index=0,
            help="Choose how to aggregate recording data over time"
        )
        
        st.markdown("---")
        
        # Add some useful info
        st.markdown("""
        <div style='background: #f0f2f6; padding: 1rem; border-radius: 10px; border-left: 4px solid #2E86AB;'>
            <h4 style='color: #2E86AB; margin-top: 0;'>� Dashboard Info</h4>
            <p style='margin-bottom: 0; font-size: 0.9em;'>
                This dashboard provides real-time monitoring of TABMON audio recording devices 
                across multiple countries. Use the tabs above to explore different views of your data.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Add status legend
        st.markdown("""
        <div style='background: #f8f9fa; padding: 1rem; border-radius: 10px;'>
            <h4 style='color: #2E86AB; margin-top: 0;'>🏷️ Status Legend</h4>
            <p style='margin: 0.5rem 0;'><span style='color: green;'>🟢 Online:</span> Active within 3 days</p>
            <p style='margin: 0.5rem 0;'><span style='color: red;'>🔴 Offline:</span> No activity > 3 days</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Main content in tabs with improved styling
    tab1, tab2, tab3 = st.tabs(["🗺️ **Map View**", "📊 **Device Status**", "📈 **Recording Activity**"])
    
    with tab1:
        st.markdown("""
        <div style='background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                    padding: 1rem; border-radius: 10px; margin-bottom: 1rem;'>
            <h3 style='color: white; margin: 0; text-align: center;'>🌍 Interactive Device Locations</h3>
        </div>
        """, unsafe_allow_html=True)
        render_map(site_info, status_df)
    
    with tab2:
        st.markdown("""
        <div style='background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%); 
                    padding: 1rem; border-radius: 10px; margin-bottom: 1rem;'>
            <h3 style='color: white; margin: 0; text-align: center;'>📊 Device Status Overview</h3>
        </div>
        """, unsafe_allow_html=True)
        render_status_metrics(status_df)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("""
        <div style='background: #f8f9fa; padding: 1rem; border-radius: 10px; border-left: 4px solid #11998e; margin: 1rem 0;'>
            <h4 style='color: #11998e; margin-top: 0;'>📋 Detailed Status Information</h4>
        </div>
        """, unsafe_allow_html=True)
        render_status_table(status_df)
    
    with tab3:
        st.markdown("""
        <div style='background: linear-gradient(90deg, #ff6b6b 0%, #feca57 100%); 
                    padding: 1rem; border-radius: 10px; margin-bottom: 1rem;'>
            <h3 style='color: white; margin: 0; text-align: center;'>📈 Recording Activity Analysis</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Load activity data
        with st.spinner("🔄 Processing activity data..."):
            matrix_data, period_title = load_and_process_data(
                parquet_file, site_csv, time_granularity
            )
        
        render_activity_heatmap(matrix_data, period_title)


