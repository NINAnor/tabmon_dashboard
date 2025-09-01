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
