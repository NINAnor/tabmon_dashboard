"""
Sidebar components for the TABMON dashboard.
"""

import streamlit as st
from components.metrics import render_sidebar_metrics


def render_dashboard_sidebar(metrics: dict = None):
    """Render the enhanced dashboard sidebar."""
    
    # Sidebar header
    st.markdown("""
    <div class='sidebar-header'>
        <h2 style='margin: 0;'>🎛️ Dashboard Controls</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Time granularity control
    time_granularity = st.radio(
        "📊 **Time Granularity**",
        ["Day", "Week", "Month"],
        index=0,
        help="Choose how to aggregate recording data over time"
    )
    
    st.markdown("---")
    
    # Show metrics if provided
    if metrics:
        render_sidebar_metrics(metrics)
        st.markdown("---")
    
    # Dashboard info
    st.markdown("""
    <div class='info-box'>
        <h4 style='color: #2E86AB; margin-top: 0;'>📋 Dashboard Info</h4>
        <p style='margin-bottom: 0; font-size: 0.9em;'>
            This dashboard provides real-time monitoring of TABMON audio recording devices 
            across multiple countries. Use the tabs above to explore different views of your data.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Status legend
    st.markdown("""
    <div class='legend-box'>
        <h4 style='color: #2E86AB; margin-top: 0;'>🏷️ Status Legend</h4>
        <p style='margin: 0.5rem 0;'><span style='color: green; font-weight: bold;'>🟢 Online:</span> Active within 3 days</p>
        <p style='margin: 0.5rem 0;'><span style='color: red; font-weight: bold;'>🔴 Offline:</span> No activity > 3 days</p>
        <p style='margin: 0.5rem 0; font-size: 0.8em; color: #666;'>
            <em>Status is determined by the last recorded audio file timestamp.</em>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    return time_granularity


def render_dashboard_sidebar_without_granularity(metrics: dict = None):
    """Render the enhanced dashboard sidebar without time granularity control."""
    
    # Dashboard info
    st.markdown("""
    <div class='info-box'>
        <h4 style='color: #2E86AB; margin-top: 0;'>📋 Dashboard Info</h4>
        <p style='margin-bottom: 0; font-size: 0.9em;'>
            This dashboard provides real-time monitoring of TABMON audio recording devices 
            across multiple countries. Use the tabs above to explore different views of your data.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Status legend
    st.markdown("""
    <div class='legend-box'>
        <h4 style='color: #2E86AB; margin-top: 0;'>🏷️ Status Legend</h4>
        <p style='margin: 0.5rem 0;'><span style='color: green; font-weight: bold;'>🟢 Online:</span> Active within 3 days</p>
        <p style='margin: 0.5rem 0;'><span style='color: red; font-weight: bold;'>🔴 Offline:</span> No activity > 3 days</p>
        <p style='margin: 0.5rem 0; font-size: 0.8em; color: #666;'>
            <em>Status is determined by the last recorded audio file timestamp.</em>
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_data_source_info(site_csv: str, parquet_file: str):
    """Render information about data sources in the sidebar."""
    with st.expander("📁 Data Sources", expanded=False):
        st.markdown(f"""
        **Site Information:**  
        `{site_csv.split('/')[-1]}`
        
        **Recording Data:**  
        `{parquet_file.split('/')[-1]}`
        
        **Last Updated:**  
        {st.session_state.get('last_data_refresh', 'Unknown')}
        """)


def render_help_section():
    """Render help and documentation in the sidebar."""
    with st.expander("❓ Help & Tips", expanded=False):
        st.markdown("""
        **Navigation Tips:**
        - 🗺️ **Map View**: See device locations and real-time status
        - 📊 **Device Status**: View detailed metrics and tables  
        - 📈 **Recording Activity**: Analyze activity patterns over time
        
        **Understanding Status:**
        - Devices are marked **Online** if they recorded audio within 3 days
        - **Offline** devices haven't recorded for more than 3 days
        - Click map markers for detailed device information
        
        **Time Granularity:**
        - **Day**: Shows daily recording patterns (detailed view)
        - **Week**: Shows weekly aggregation (medium view)  
        - **Month**: Shows monthly trends (overview)
        """)


def render_about_section():
    """Render about information in the sidebar."""
    with st.expander("ℹ️ About TABMON", expanded=False):
        st.markdown("""
        **TABMON** is a passive acoustic monitoring system for biodiversity research.
        
        This dashboard monitors the operational status of audio recording devices 
        deployed across multiple countries and research sites.
        
        **Key Features:**
        - Real-time device status monitoring
        - Interactive geographic visualization
        - Recording activity analysis
        - Multi-country deployment tracking
        
        For technical support or questions, contact the TABMON team.
        """)


def render_complete_sidebar(metrics: dict = None, site_csv: str = None, parquet_file: str = None):
    """Render the complete sidebar with all components."""
    render_dashboard_sidebar_without_granularity(metrics)
    
    if site_csv and parquet_file:
        render_data_source_info(site_csv, parquet_file)
    
    render_help_section()
    render_about_section()
