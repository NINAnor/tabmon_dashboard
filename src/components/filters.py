"""Filter components for the dashboard."""

import streamlit as st
import pandas as pd
from typing import List, Dict, Tuple
from datetime import datetime, timedelta


def render_country_filter(data: pd.DataFrame, column_name: str = "Country", key_prefix: str = "main") -> List[str]:
    """Render a multi-select filter for countries."""
    if column_name not in data.columns:
        return []
    
    countries = sorted(data[column_name].dropna().unique())
    
    selected_countries = st.multiselect(
        "🌍 **Select Countries**",
        options=countries,
        default=countries,
        key=f"country_filter_{key_prefix}",
        help="Filter devices by country"
    )
    
    return selected_countries


def render_status_filter(key_prefix: str = "main") -> List[str]:
    """Render a filter for device status."""
    status_options = ["Online", "Offline"]
    
    selected_statuses = st.multiselect(
        "📊 **Select Status**",
        options=status_options,
        default=status_options,
        key=f"status_filter_{key_prefix}",
        help="Filter devices by online/offline status"
    )
    
    return selected_statuses


def render_date_range_filter(data: pd.DataFrame, key_prefix: str = "main") -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Render date range filters for the dashboard."""
    if "last_file" not in data.columns:
        # Return default range if no date column
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        return pd.Timestamp(start_date, tz='UTC'), pd.Timestamp(end_date, tz='UTC')
    
    # Get date range from data
    dates = pd.to_datetime(data["last_file"], errors='coerce').dropna()
    if dates.empty:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
    else:
        min_date = dates.min().date()
        max_date = dates.max().date()
        start_date = min_date
        end_date = max_date
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "From",
            value=start_date,
            min_value=min_date if not dates.empty else start_date,
            max_value=max_date if not dates.empty else end_date,
            key=f"start_date_filter_{key_prefix}",
            help="Start date for filtering"
        )
    
    with col2:
        end_date = st.date_input(
            "To",
            value=end_date,
            min_value=min_date if not dates.empty else start_date,
            max_value=max_date if not dates.empty else end_date,
            key=f"end_date_filter_{key_prefix}",
            help="End date for filtering"
        )
    
    return pd.Timestamp(start_date, tz='UTC'), pd.Timestamp(end_date, tz='UTC')


def render_site_filter(data: pd.DataFrame, column_name: str = "site_name", key_prefix: str = "main") -> List[str]:
    """Render a filter for research sites."""
    if column_name not in data.columns:
        return []
    
    sites = sorted(data[column_name].dropna().unique())
    
    if len(sites) > 10:
        # For many sites, use a searchable selectbox
        selected_site = st.selectbox(
            "🏞️ **Select Site** (All sites selected by default)",
            options=["All"] + sites,
            index=0,
            key=f"site_filter_single_{key_prefix}",
            help="Select a specific site to focus on"
        )
        
        if selected_site == "All":
            return sites
        else:
            return [selected_site]
    else:
        # For fewer sites, use multiselect
        selected_sites = st.multiselect(
            "🏞️ **Select Sites**",
            options=sites,
            default=sites,
            key=f"site_filter_multi_{key_prefix}",
            help="Filter devices by research site"
        )
        
        return selected_sites


def render_device_type_filter(data: pd.DataFrame, column_name: str = "device_type", key_prefix: str = "main") -> List[str]:
    """Render a filter for device types."""
    if column_name not in data.columns:
        return []
    
    device_types = sorted(data[column_name].dropna().unique())
    
    selected_types = st.multiselect(
        "🔧 **Select Device Types**",
        options=device_types,
        default=device_types,
        key=f"device_type_filter_{key_prefix}",
        help="Filter by device type"
    )
    
    return selected_types


def apply_filters(data: pd.DataFrame,
                 countries: List[str] = None,
                 statuses: List[str] = None,
                 start_date: pd.Timestamp = None,
                 end_date: pd.Timestamp = None,
                 sites: List[str] = None,
                 device_types: List[str] = None) -> pd.DataFrame:
    """Apply multiple filters to the dataset."""
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


def render_advanced_filters(data: pd.DataFrame, key_prefix: str = "main") -> Dict:
    """Render advanced filtering options."""
    with st.expander("🔧 Advanced Filters", expanded=False):
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Days since last recording filter
            if "days_since_last" in data.columns:
                max_days = int(data["days_since_last"].max()) if not data["days_since_last"].isna().all() else 30
                
                days_threshold = st.slider(
                    "📅 Maximum days since last recording",
                    min_value=0,
                    max_value=max_days,
                    value=max_days,
                    key=f"days_threshold_filter_{key_prefix}",
                    help="Filter devices by days since their last recording"
                )
            else:
                days_threshold = None
            
            # Recording count filter
            if "total_recordings" in data.columns:
                min_recordings = st.number_input(
                    "🎵 Minimum recordings",
                    min_value=0,
                    value=0,
                    key=f"min_recordings_filter_{key_prefix}",
                    help="Filter devices with at least this many recordings"
                )
            else:
                min_recordings = None
        
        with col2:
            # Coordinate filters
            if "latitude" in data.columns and "longitude" in data.columns:
                st.markdown("**📍 Geographic Bounds**")
                
                lat_range = st.slider(
                    "Latitude range",
                    min_value=float(data["latitude"].min()) if not data["latitude"].isna().all() else -90.0,
                    max_value=float(data["latitude"].max()) if not data["latitude"].isna().all() else 90.0,
                    value=(
                        float(data["latitude"].min()) if not data["latitude"].isna().all() else -90.0,
                        float(data["latitude"].max()) if not data["latitude"].isna().all() else 90.0
                    ),
                    key=f"lat_range_filter_{key_prefix}",
                    help="Filter by latitude range"
                )
                
                lon_range = st.slider(
                    "Longitude range",
                    min_value=float(data["longitude"].min()) if not data["longitude"].isna().all() else -180.0,
                    max_value=float(data["longitude"].max()) if not data["longitude"].isna().all() else 180.0,
                    value=(
                        float(data["longitude"].min()) if not data["longitude"].isna().all() else -180.0,
                        float(data["longitude"].max()) if not data["longitude"].isna().all() else 180.0
                    ),
                    key=f"lon_range_filter_{key_prefix}",
                    help="Filter by longitude range"
                )
            else:
                lat_range = None
                lon_range = None
    
    return {
        "days_threshold": days_threshold,
        "min_recordings": min_recordings,
        "lat_range": lat_range,
        "lon_range": lon_range
    }


def render_complete_filters(data: pd.DataFrame, key_prefix: str = "main") -> Tuple[pd.DataFrame, Dict]:
    """Render all filters and return filtered data with active filter info."""
    st.markdown("### 🔍 Filters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        countries = render_country_filter(data, key_prefix=key_prefix)
    
    with col2:
        statuses = render_status_filter(key_prefix=key_prefix)
    
    with col3:
        sites = render_site_filter(data, key_prefix=key_prefix)
    
    # Date range filter
    start_date, end_date = render_date_range_filter(data, key_prefix=key_prefix)
    
    # Device type filter (if the column exists)
    device_types = render_device_type_filter(data, key_prefix=key_prefix)
    
    # Apply filters
    filtered_data = apply_filters(
        data, countries, statuses, start_date, end_date, sites, device_types
    )
    
    # Advanced filters
    advanced_filters = render_advanced_filters(filtered_data, key_prefix=key_prefix)
    
    # Apply advanced filters
    if advanced_filters["days_threshold"] is not None and "days_since_last" in filtered_data.columns:
        filtered_data = filtered_data[filtered_data["days_since_last"] <= advanced_filters["days_threshold"]]
    
    if advanced_filters["min_recordings"] is not None and "total_recordings" in filtered_data.columns:
        filtered_data = filtered_data[filtered_data["total_recordings"] >= advanced_filters["min_recordings"]]
    
    if advanced_filters["lat_range"] is not None and "latitude" in filtered_data.columns:
        lat_min, lat_max = advanced_filters["lat_range"]
        filtered_data = filtered_data[
            (filtered_data["latitude"] >= lat_min) & 
            (filtered_data["latitude"] <= lat_max)
        ]
    
    if advanced_filters["lon_range"] is not None and "longitude" in filtered_data.columns:
        lon_min, lon_max = advanced_filters["lon_range"]
        filtered_data = filtered_data[
            (filtered_data["longitude"] >= lon_min) & 
            (filtered_data["longitude"] <= lon_max)
        ]
    
    # Collect active filter information
    active_filters = {
        "countries": countries,
        "statuses": statuses,
        "start_date": start_date,
        "end_date": end_date,
        "sites": sites,
        "device_types": device_types,
        **advanced_filters
    }
    
    # Display filter summary
    st.markdown(f"**📊 Showing {len(filtered_data)} of {len(data)} devices**")
    
    return filtered_data, active_filters
