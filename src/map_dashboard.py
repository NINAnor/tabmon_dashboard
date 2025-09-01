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


def app(site_csv: str = None, parquet_file: str = None):
    """Main map dashboard application."""
    load_custom_css()
    
    # Use provided URLs or fall back to defaults
    site_csv_url = site_csv or ASSETS_SITE_CSV
    parquet_file_url = parquet_file or ASSETS_PARQUET_FILE
    
    # Initialize data service with provided URLs
    data_service = DataService(site_csv_url, parquet_file_url)
    
    # Load all data
    with st.spinner("Loading device data..."):
        device_data = data_service.load_device_status()
        site_info = data_service.load_site_info()
        
    # Calculate metrics
    metrics = data_service.calculate_metrics(device_data)
    
    # Render sidebar with controls and metrics
    with st.sidebar:
        render_complete_sidebar(
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
        render_activity_tab(data_service)
    
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
    filtered_data, active_filters = render_complete_filters(device_data, key_prefix="map")
    
    if not filtered_data.empty:
        # Get site info for the map
        site_info = data_service.load_site_info()
        
        # Render the interactive map
        render_device_map(site_info, filtered_data)
        
        # Map summary statistics
        st.markdown("#### 📊 Map Summary")
        
        # Show filtering info if devices are being filtered out
        total_devices = len(device_data)
        shown_devices = len(filtered_data)
        if shown_devices < total_devices:
            st.info(f"ℹ️ Showing {shown_devices} of {total_devices} total devices. {total_devices - shown_devices} devices are hidden by current filters.")
        
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
    st.markdown("#### 🌍 Status by Country")
    render_country_bar_chart(device_data)
    
    # Detailed status table
    st.markdown("#### 📋 Detailed Device Status")
    
    # Filters for status table
    filtered_data, _ = render_complete_filters(device_data, key_prefix="status")
    
    if not filtered_data.empty:
        # Display options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            per_page = st.selectbox("Devices per page", [10, 25, 50, 100], index=1)
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
        render_status_table(sorted_data)
        
        # Summary statistics
        st.markdown("#### 📈 Summary Statistics")
        render_summary_table(filtered_data)
    else:
        st.warning("⚠️ No devices match the current filter criteria.")


def render_activity_tab(data_service: DataService):
    """Render the recording activity analysis tab."""
    st.markdown("### 📈 Recording Activity Analysis")
    
    # Load recording matrix data with day granularity
    with st.spinner("Loading daily activity data..."):
        recording_data = data_service.load_recording_matrix("Day")
    
    if not recording_data.empty:
        # Activity heatmap
        st.markdown("#### 🔥 Recording Activity Heatmap")
        render_activity_heatmap(recording_data, "Day")
        
        # Activity insights
        st.markdown("#### 💡 Activity Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Most active devices - recording_data is a crosstab with MultiIndex
            # Sum across all time periods for each device
            device_totals = recording_data.sum(axis=1).sort_values(ascending=False)
            
            st.markdown("**🏆 Most Active Devices**")
            top_devices = device_totals.head(10)
            for device_info, count in top_devices.items():
                # device_info is a tuple (Country, device) due to MultiIndex
                if isinstance(device_info, tuple):
                    country, device = device_info
                    st.write(f"• **{device}** ({country}): {count:,} recordings")
                else:
                    st.write(f"• **{device_info}**: {count:,} recordings")
        
        with col2:
            # Activity statistics - recording_data is a crosstab matrix
            total_recordings = recording_data.sum().sum()  # Sum all values in the matrix
            device_totals = recording_data.sum(axis=1)  # Sum across time periods for each device
            avg_per_device = device_totals.mean()
            active_cells = (recording_data > 0).sum().sum()  # Count non-zero cells
            
            st.markdown("**📊 Activity Statistics**")
            st.write(f"• **Total recordings**: {total_recordings:,.0f}")
            st.write(f"• **Average per device**: {avg_per_device:.1f}")
            st.write(f"• **Active data points**: {active_cells:,}")
            st.write(f"• **Coverage**: {len(recording_data.index)} devices")
        
        # Downloadable data
        st.markdown("#### 💾 Export Data")
        
        # Convert crosstab to CSV format
        csv_data = recording_data.to_csv()
        st.download_button(
            label="📥 Download activity data as CSV",
            data=csv_data,
            file_name=f"tabmon_activity_day_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
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
