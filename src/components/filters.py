"""Filter components for the dashboard."""

import streamlit as st
import pandas as pd
from typing import List, Dict, Tuple
from datetime import datetime, timedelta, date


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
        start_date = date(2020, 1, 1)  # Include all historical data
        return pd.Timestamp(start_date, tz='UTC'), pd.Timestamp(end_date, tz='UTC')
    
    # Get date range from data for determining max date only
    dates = pd.to_datetime(data["last_file"], errors='coerce').dropna()
    
    # Start date to include all historical data
    start_date = date(2020, 1, 1)
    
    if dates.empty:
        end_date = datetime.now().date()
    else:
        max_date = dates.max().date()
        # Use current date if data max date is in the future
        end_date = min(max_date, datetime.now().date())
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "From",
            value=start_date,
            min_value=date(2020, 1, 1),  # Allow historical data
            max_value=end_date,
            key=f"start_date_filter_{key_prefix}",
            help="Start date for filtering"
        )
    
    with col2:
        end_date = st.date_input(
            "To",
            value=end_date,
            min_value=date(2020, 1, 1),  # Allow historical data
            max_value=datetime.now().date(),
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


def apply_filters(
    data: pd.DataFrame,
    countries: List[str] = None,
    statuses: List[str] = None,
    start_date: pd.Timestamp = None,
    end_date: pd.Timestamp = None,
    sites: List[str] = None,
    device_types: List[str] = None,
    advanced_filters: Dict = None
) -> pd.DataFrame:
    """Apply all filters to the data."""
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
        
        # Convert start_date and end_date to same timezone as data (or make timezone-naive)
        start_date_naive = start_date.tz_localize(None) if start_date.tzinfo else start_date
        end_date_naive = end_date.tz_localize(None) if end_date.tzinfo else end_date
        
        # Make end_date inclusive by extending to end of day
        end_date_inclusive = end_date_naive + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        
        # Ensure dates are timezone-naive for comparison
        if last_file_dates.dt.tz is not None:
            last_file_dates = last_file_dates.dt.tz_convert(None)
        
        # Include devices with missing dates OR dates within the range
        date_mask = (
            last_file_dates.isna() |  # Include devices with missing dates
            ((last_file_dates >= start_date_naive) & (last_file_dates <= end_date_inclusive))
        )
        filtered_data = filtered_data[date_mask]
    
    # Site filter
    if sites and "site_name" in filtered_data.columns:
        filtered_data = filtered_data[filtered_data["site_name"].isin(sites)]
    
    # Device type filter
    if device_types and "device_type" in filtered_data.columns:
        filtered_data = filtered_data[filtered_data["device_type"].isin(device_types)]
    
    return filtered_data


def render_advanced_filters(data: pd.DataFrame, key_prefix: str = "main") -> Dict:
    """Render advanced filtering options."""
    # Remove the expander to avoid nesting issues
    st.markdown("**⚙️ Advanced Filters**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Days since last recording filter
        if "days_since_last" in data.columns:
            max_days_value = data["days_since_last"].replace([float('inf'), float('-inf')], float('nan')).max()
            max_days = int(max_days_value) if not pd.isna(max_days_value) else 30
            
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


def get_preset_filters(preset: str, data: pd.DataFrame) -> Dict:
    """Get filter parameters for a given preset."""
    from datetime import datetime, timedelta
    
    # Default values
    all_countries = list(data["Country"].dropna().unique()) if "Country" in data.columns else []
    all_sites = list(data["site_name"].dropna().unique()) if "site_name" in data.columns else []
    all_statuses = ["Online", "Offline"]
    
    current_date = datetime.now().date()
    
    presets = {
        "🌟 All Devices": {
            "countries": all_countries,
            "statuses": all_statuses,
            "start_date": pd.Timestamp(date(2020, 1, 1), tz='UTC'),
            "end_date": pd.Timestamp(current_date, tz='UTC'),
            "sites": all_sites,
            "description": "Show all devices without any filters"
        },
        "✅ Online Devices Only": {
            "countries": all_countries,
            "statuses": ["Online"],
            "start_date": pd.Timestamp(date(2020, 1, 1), tz='UTC'),
            "end_date": pd.Timestamp(current_date, tz='UTC'),
            "sites": all_sites,
            "description": "Show only devices that are currently online"
        },
        "❌ Offline Devices Only": {
            "countries": all_countries,
            "statuses": ["Offline"],
            "start_date": pd.Timestamp(date(2020, 1, 1), tz='UTC'),
            "end_date": pd.Timestamp(current_date, tz='UTC'),
            "sites": all_sites,
            "description": "Show only devices that are currently offline"
        },
        "📅 Recent Activity (Last 30 days)": {
            "countries": all_countries,
            "statuses": all_statuses,
            "start_date": pd.Timestamp(current_date - timedelta(days=30), tz='UTC'),
            "end_date": pd.Timestamp(current_date, tz='UTC'),
            "sites": all_sites,
            "description": "Show devices with activity in the last 30 days"
        },
        "🇳🇴 Norway Only": {
            "countries": ["Norway"] if "Norway" in all_countries else all_countries,
            "statuses": all_statuses,
            "start_date": pd.Timestamp(date(2020, 1, 1), tz='UTC'),
            "end_date": pd.Timestamp(current_date, tz='UTC'),
            "sites": all_sites,
            "description": "Show only devices deployed in Norway"
        },
        "🇳🇱 Netherlands Only": {
            "countries": ["Netherlands"] if "Netherlands" in all_countries else all_countries,
            "statuses": all_statuses,
            "start_date": pd.Timestamp(date(2020, 1, 1), tz='UTC'),
            "end_date": pd.Timestamp(current_date, tz='UTC'),
            "sites": all_sites,
            "description": "Show only devices deployed in the Netherlands"
        },
        "🇫🇷 France Only": {
            "countries": ["France"] if "France" in all_countries else all_countries,
            "statuses": all_statuses,
            "start_date": pd.Timestamp(date(2020, 1, 1), tz='UTC'),
            "end_date": pd.Timestamp(current_date, tz='UTC'),
            "sites": all_sites,
            "description": "Show only devices deployed in France"
        },
        "🇪🇸 Spain Only": {
            "countries": ["Spain"] if "Spain" in all_countries else all_countries,
            "statuses": all_statuses,
            "start_date": pd.Timestamp(date(2020, 1, 1), tz='UTC'),
            "end_date": pd.Timestamp(current_date, tz='UTC'),
            "sites": all_sites,
            "description": "Show only devices deployed in Spain"
        }
    }
    
    return presets.get(preset, presets["🌟 All Devices"])


def render_smart_preset_filters(data: pd.DataFrame, key_prefix: str = "main") -> Tuple[pd.DataFrame, Dict]:
    """Render smart preset filters with optional custom filtering."""
    st.markdown("### 🔍 Quick Filters")
    
    # Preset selection
    preset_options = [
        "🌟 All Devices",
        "✅ Online Devices Only", 
        "❌ Offline Devices Only",
        "📅 Recent Activity (Last 30 days)",
        "🇳🇴 Norway Only",
        "🇳🇱 Netherlands Only", 
        "🇫🇷 France Only",
        "🇪🇸 Spain Only",
        "⚙️ Custom Filters"
    ]
    
    preset = st.selectbox(
        "Choose a filter preset:",
        preset_options,
        key=f"preset_filter_{key_prefix}",
        help="Select a predefined filter or choose Custom to set your own filters"
    )
    
    # Show preset description
    if preset != "⚙️ Custom Filters":
        preset_config = get_preset_filters(preset, data)
        st.info(f"ℹ️ {preset_config['description']}")
        
        # Apply preset filters
        filtered_data = apply_filters(
            data,
            countries=preset_config["countries"],
            statuses=preset_config["statuses"],
            start_date=preset_config["start_date"],
            end_date=preset_config["end_date"],
            sites=preset_config["sites"]
        )
        
        active_filters = preset_config
        
    else:
        # Custom filters section
        st.markdown("**🛠️ Custom Filter Options:**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            countries = render_country_filter(data, key_prefix=key_prefix)
        
        with col2:
            statuses = render_status_filter(key_prefix=key_prefix)
        
        with col3:
            sites = render_site_filter(data, key_prefix=key_prefix)
        
        # Date range filter for custom
        start_date, end_date = render_date_range_filter(data, key_prefix=key_prefix)
        
        # Apply custom filters
        filtered_data = apply_filters(
            data, countries, statuses, start_date, end_date, sites
        )
        
        active_filters = {
            "countries": countries,
            "statuses": statuses,
            "start_date": start_date,
            "end_date": end_date,
            "sites": sites,
            "description": "Custom filter configuration"
        }
        
        # Optional advanced filters (not in expandable section to avoid nesting)
        if st.checkbox("Show Advanced Options", key=f"show_advanced_{key_prefix}"):
            advanced_filters = render_advanced_filters(filtered_data, key_prefix=key_prefix)
            
            # Apply advanced filters
            if advanced_filters["days_threshold"] is not None and "days_since_last" in filtered_data.columns:
                days_since_clean = filtered_data["days_since_last"].replace([float('inf'), float('-inf')], float('nan'))
                filtered_data = filtered_data[
                    days_since_clean.isna() | (days_since_clean <= advanced_filters["days_threshold"])
                ]
            
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
            
            # Merge advanced filters into active filters
            active_filters.update(advanced_filters)
        else:
            # No advanced filters applied
            active_filters.update({
                "days_threshold": None,
                "min_recordings": None,
                "lat_range": None,
                "lon_range": None
            })
    
    # Display filter summary
    if len(filtered_data) != len(data):
        st.success(f"📊 Showing **{len(filtered_data)}** of **{len(data)}** devices")
    else:
        st.info(f"📊 Showing all **{len(data)}** devices")
    
    return filtered_data, active_filters


def render_complete_filters(data: pd.DataFrame, key_prefix: str = "main") -> Tuple[pd.DataFrame, Dict]:
    """Render smart preset filters (new default filter interface)."""
    return render_smart_preset_filters(data, key_prefix=key_prefix)
