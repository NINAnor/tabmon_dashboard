"""
UI styling and custom CSS for the TABMON dashboard.
"""

import streamlit as st


def load_custom_css():
    """Load custom CSS styles for the dashboard."""
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
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #2E86AB;
        color: white;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }
    
    .stAlert > div {
        border-radius: 10px;
    }
    
    .status-online {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    }
    
    .status-offline {
        background: linear-gradient(135deg, #ff6b6b 0%, #feca57 100%);
    }
    
    .status-total {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .sidebar-header {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        color: white;
        margin-bottom: 1rem;
    }
    
    .info-box {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #2E86AB;
    }
    
    .legend-box {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
    }
    
    /* Subtle section headers for information display */
    .section-info {
        background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 0.8rem 1.2rem;
        border-radius: 8px;
        border-left: 4px solid #6c757d;
        margin: 0.5rem 0;
    }
    
    .section-info h3 {
        color: #495057;
        margin: 0;
        font-weight: 600;
    }
    
    .section-info h4 {
        color: #6c757d;
        margin: 0;
        font-weight: 500;
    }
    
    .audio-stats-header {
        background: linear-gradient(90deg, #e3f2fd 0%, #f3e5f5 100%);
        border-left: 4px solid #2196f3;
    }
    
    .audio-stats-header h3 {
        color: #1976d2;
    }
    
    .dataset-contribution-header {
        background: linear-gradient(90deg, #f3e5f5 0%, #fce4ec 100%);
        border-left: 4px solid #9c27b0;
    }
    
    .dataset-contribution-header h4 {
        color: #7b1fa2;
    }
    
    .map-summary-header {
        background: linear-gradient(90deg, #e8f5e8 0%, #f1f8e9 100%);
        border-left: 4px solid #4caf50;
    }
    
    .map-summary-header h4 {
        color: #388e3c;
    }
    
    .site-details-header {
        background: linear-gradient(90deg, #fff3e0 0%, #fce4ec 100%);
        border-left: 4px solid #ff9800;
    }
    
    .site-details-header h3 {
        color: #f57c00;
    }
    
    .site-images-header {
        background: linear-gradient(90deg, #f3e5f5 0%, #e1f5fe 100%);
        border-left: 4px solid #00bcd4;
    }
    
    .site-images-header h3 {
        color: #0097a7;
    }
    
    .recording-header {
        background: linear-gradient(90deg, #e8f5e8 0%, #e3f2fd 100%);
        border-left: 4px solid #4caf50;
    }
    
    .recording-header h3 {
        color: #388e3c;
    }
    
    .player-header {
        background: linear-gradient(90deg, #fff3e0 0%, #fce4ec 100%);
        border-left: 4px solid #ff5722;
    }
    
    .player-header h3 {
        color: #d84315;
    }
    
    .quick-filters-header {
        background: linear-gradient(90deg, #e8f5e8 0%, #e3f2fd 100%);
        border-left: 4px solid #2196f3;
    }
    
    .quick-filters-header h3 {
        color: #1565c0;
    }
    
    .site-name-header {
        background: linear-gradient(90deg, #f3e5f5 0%, #e8f5e8 100%);
        border-left: 4px solid #9c27b0;
    }
    
    .site-name-header h2 {
        color: #7b1fa2;
        margin: 0;
        font-weight: 600;
    }
    
    .export-tools-header {
        background: linear-gradient(90deg, #e3f2fd 0%, #f3e5f5 100%);
        border-left: 4px solid #2196f3;
    }
    
    .export-tools-header h4 {
        color: #1976d2;
    }
    </style>
    """, unsafe_allow_html=True)


def render_page_header(title: str, subtitle: str = None):
    """Render the main page header with styling."""
    header_html = f"""
    <h1 style='text-align: center; color: #2E86AB; margin-bottom: 30px;'>
        {title}
    </h1>
    """
    
    if subtitle:
        header_html += f"""
        <p style='text-align: center; color: #666; font-size: 1.2em; margin-bottom: 30px;'>
            {subtitle}
        </p>
        """
    
    header_html += "<hr style='margin-bottom: 30px;'>"
    
    st.markdown(header_html, unsafe_allow_html=True)


def render_info_section_header(title: str, level: str = "h3", style_class: str = "section-info"):
    """Render a subtle styled section header for information display."""
    st.markdown(f"""
    <div class='section-info {style_class}'>
        <{level} style='margin: 0; font-weight: 600;'>{title}</{level}>
    </div>
    """, unsafe_allow_html=True)
