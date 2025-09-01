"""
Filter components for the T  def render_statu    selected_statuses = st.multiselect(
        "📊 **Select Status**",
        options=status_options,
        default=status_options,
        key="status_filter_main",
        help="Filter devices by online/offline status"
    )r() -> List[str]:
    """Render a filter for device status."""
    status_options = ["Online", "Offline"]
    
    selected_statuses = st.multiselect(
        "📊 **Select Status**",
        options=status_options,
        default=status_options,
        key="status_filter_main",
        help="Filter devices by online/offline status"
    )
    
    return selected_statusesatuses = st.multiselect(
        "📊 **Select Status**",
        options=status_options,
        default=status_options,
        key="status_filter_main",
        help="Filter devices by online/offline status"
    )ashboard.
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Tuple, Optional


def render_country_filter(data: pd.DataFrame, column_name: str = "Country") -> List[str]:
    """Render a multi-select filter for countries."""
    if column_name not in data.columns:
        return []
    
    countries = sorted(data[column_name].dropna().unique())
    
    selected_countries = st.multiselect(
        "🌍 **Select Countries**",
        options=countries,
        default=countries,
        key="country_filter_main",
        help="Filter devices by country"
    )
    
    return selected_countries


def render_status_filter() -> List[str]:
    """Render a filter for device status."""
    status_options = ["Online", "Offline"]
    
    selected_statuses = st.multiselect(
        "� **Select Status**",
        options=statuses,
        default=statuses,
        key="status_filter_main",
        help="Filter devices by online/offline status"
    )
    
    return selected_statuses


def render_date_range_filter(data: pd.DataFrame, date_column: str = "last_file") -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Render a date range filter."""
    if date_column not in data.columns:
        return None, None
    
    # Convert to datetime if not already
    dates = pd.to_datetime(data[date_column], errors='coerce').dropna()
    
    if dates.empty:
        return None, None
    
    min_date = dates.min().date()
    max_date = dates.max().date()
    
    st.markdown("📅 **Date Range Filter**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "From",
            value=min_date,
            min_value=min_date,
            max_value=max_date,
            help="Start date for filtering"
        )
    
    with col2:
        end_date = st.date_input(
            "To",
            value=max_date,
            min_value=min_date,
            max_value=max_date,
            help="End date for filtering"
        )
    
    return pd.Timestamp(start_date, tz='UTC'), pd.Timestamp(end_date, tz='UTC')


def render_site_filter(data: pd.DataFrame, column_name: str = "site_name") -> List[str]:
    """Render a filter for research sites."""
    if column_name not in data.columns:
        return []
    
    sites = sorted(data[column_name].dropna().unique())
    
    if len(sites) > 10:
        # For many sites, use a searchable selectbox
        selected_site = st.selectbox(
            "🏞️ **Select Site** (All sites selected by default)",
            options=["All Sites"] + sites,
            index=0,
            help="Filter by specific research site"
        )
        
        if selected_site == "All Sites":
            return sites
        else:
            return [selected_site]
    else:
        # For fewer sites, use multiselect
        selected_sites = st.multiselect(
            "🏞️ **Select Sites**",
            options=sites,
            default=sites,
            help="Filter devices by research site"
        )
        
        return selected_sites


def render_device_type_filter(data: pd.DataFrame, column_name: str = "device_type") -> List[str]:
    """Render a filter for device types."""
    if column_name not in data.columns:
        return []
    
    device_types = sorted(data[column_name].dropna().unique())
    
    selected_types = st.multiselect(
        "🎙️ **Device Types**",
        options=device_types,
        default=device_types,
        help="Filter by device/recorder type"
    )
    
    return selected_types


def apply_filters(data: pd.DataFrame, 
                 countries: List[str] = None,
                 statuses: List[str] = None,
                 start_date: pd.Timestamp = None,
                 end_date: pd.Timestamp = None,
                 sites: List[str] = None,
                 device_types: List[str] = None) -> pd.DataFrame:
    """Apply all selected filters to the data."""
    filtered_data = data.copy()
    
    # Country filter
    if countries and "Country" in filtered_data.columns:
        filtered_data = filtered_data[filtered_data["Country"].isin(countries)]
    
    # Status filter
    if statuses and "status" in filtered_data.columns:
        filtered_data = filtered_data[filtered_data["status"].isin(statuses)]
    
    # Date range filter
    if start_date and end_date and "last_file" in filtered_data.columns:
        last_file_dates = pd.to_datetime(filtered_data["last_file"], errors='coerce')
        # Ensure timezone consistency
        if start_date.tzinfo is None:
            start_date = start_date.tz_localize('UTC')
        if end_date.tzinfo is None:
            end_date = end_date.tz_localize('UTC')
        
        filtered_data = filtered_data[
            (last_file_dates >= start_date) & 
            (last_file_dates <= end_date)
        ]
    
    # Site filter
    if sites and "site_name" in filtered_data.columns:
        filtered_data = filtered_data[filtered_data["site_name"].isin(sites)]
    
    # Device type filter
    if device_types and "device_type" in filtered_data.columns:
        filtered_data = filtered_data[filtered_data["device_type"].isin(device_types)]
    
    return filtered_data


def render_advanced_filters(data: pd.DataFrame) -> Dict:
    """Render advanced filtering options."""
    with st.expander("🔧 Advanced Filters", expanded=False):
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Recording count filter
            if "recording_count" in data.columns:
                min_recordings = st.number_input(
                    "Min Recordings",
                    min_value=0,
                    value=0,
                    help="Filter devices with minimum recording count"
                )
            else:
                min_recordings = 0
        
        with col2:
            # Days since last recording
            if "days_since_last" in data.columns:
                max_days_offline = st.number_input(
                    "Max Days Offline",
                    min_value=0,
                    value=365,
                    help="Filter devices offline for maximum days"
                )
            else:
                max_days_offline = 365
        
        # Show empty/null data
        show_missing_data = st.checkbox(
            "Include devices with missing data",
            value=True,
            help="Include devices that may have incomplete information"
        )
        
        return {
            "min_recordings": min_recordings,
            "max_days_offline": max_days_offline,
            "show_missing_data": show_missing_data
        }


def render_filter_summary(original_count: int, filtered_count: int):
    """Render a summary of applied filters."""
    if filtered_count != original_count:
        st.info(
            f"📊 Showing **{filtered_count}** of **{original_count}** devices "
            f"({filtered_count/original_count*100:.1f}%)"
        )
        
        if filtered_count == 0:
            st.warning("⚠️ No devices match the current filter criteria. Try adjusting your filters.")


def render_filter_reset_button():
    """Render a button to reset all filters."""
    if st.button("🔄 Reset All Filters", help="Clear all filters and show all data"):
        # Clear filter-related session state
        for key in list(st.session_state.keys()):
            if key.startswith('filter_') or key.endswith('_filter'):
                del st.session_state[key]
        st.rerun()


def render_complete_filters(data: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    """Render all filter components and return filtered data."""
    st.markdown("### 🎯 Data Filters")
    
    # Basic filters
    col1, col2 = st.columns(2)
    
    with col1:
        countries = render_country_filter(data)
        sites = render_site_filter(data)
    
    with col2:
        statuses = render_status_filter()
        device_types = render_device_type_filter(data)
    
    # Date range filter
    start_date, end_date = render_date_range_filter(data)
    
    # Advanced filters
    advanced_filters = render_advanced_filters(data)
    
    # Apply all filters
    filtered_data = apply_filters(
        data, countries, statuses, start_date, end_date, sites, device_types
    )
    
    # Apply advanced filters
    if advanced_filters["min_recordings"] > 0 and "recording_count" in filtered_data.columns:
        filtered_data = filtered_data[
            filtered_data["recording_count"] >= advanced_filters["min_recordings"]
        ]
    
    if advanced_filters["max_days_offline"] < 365 and "days_since_last" in filtered_data.columns:
        filtered_data = filtered_data[
            (filtered_data["days_since_last"] <= advanced_filters["max_days_offline"]) |
            (filtered_data["days_since_last"].isna() & advanced_filters["show_missing_data"])
        ]
    
    # Show filter summary
    render_filter_summary(len(data), len(filtered_data))
    
    # Reset button
    render_filter_reset_button()
    
    return filtered_data, {
        "countries": countries,
        "statuses": statuses,
        "start_date": start_date,
        "end_date": end_date,
        "sites": sites,
        "device_types": device_types,
        **advanced_filters
    }
