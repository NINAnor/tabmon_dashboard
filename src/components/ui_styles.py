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
    
    .section-header {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    .map-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    .status-header {
        background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%);
    }
    
    .activity-header {
        background: linear-gradient(90deg, #ff6b6b 0%, #feca57 100%);
    }
    
    .detailed-status-header {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #11998e;
        margin: 1rem 0;
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


def render_section_header(title: str, style_class: str):
    """Render a styled section header."""
    st.markdown(f"""
    <div class='section-header {style_class}'>
        <h3 style='color: white; margin: 0;'>{title}</h3>
    </div>
    """, unsafe_allow_html=True)
