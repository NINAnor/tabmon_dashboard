"""
Configuration settings for the TABMON dashboard.
"""

# Application settings
APP_TITLE = "TABMON Device Monitoring Dashboard"
APP_ICON = "🎙️"
LAYOUT = "wide"

# Data settings
OFFLINE_THRESHOLD_DAYS = 3
DATA_START_DATE = "2025-01-01"

# Country mapping
COUNTRY_MAP = {
    "proj_tabmon_NINA": "Norway",
    "proj_tabmon_NINA_ES": "Spain",
    "proj_tabmon_NINA_NL": "Netherlands",
    "proj_tabmon_NINA_FR": "France",
}

# Map settings
DEFAULT_ZOOM = 6
MAP_HEIGHT = 600
MAP_WIDTH = 1200

# Privacy protection settings
MAX_ZOOM_LEVEL = 7              # Maximum zoom level for public access (prevents very detailed viewing)
MIN_ZOOM_LEVEL = 3              # Minimum zoom level
DETAILED_MAP_MAX_ZOOM = 18      # Maximum zoom level for authorized users (full detail)

# Detailed map access configuration
# Password can be set via AUTH_PASSWORD environment variable (recommended for production)
# This same variable is used for basic authentication in the reverse proxy
DETAILED_MAP_PASSWORD = "tabmon2025"  # Fallback password for detailed map access

# Chart settings
HEATMAP_COLORSCALE = "Viridis"
MIN_HEATMAP_HEIGHT = 400
HEATMAP_ROW_HEIGHT = 25

# Cache settings
CACHE_TTL = 3600  # 1 hour

# UI Colors
COLORS = {
    "primary": "#2E86AB",
    "secondary": "#667eea",
    "success": "#11998e",
    "warning": "#feca57",
    "danger": "#ff6b6b",
    "info": "#764ba2",
    "light": "#f8f9fa",
    "dark": "#343a40",
}

# Data source URLs
BASE_DATA_URL = "http://rclone:8081/data/"
ASSETS_SITE_CSV = "assets/site_info.csv"
ASSETS_PARQUET_FILE = "assets/index.parquet"

# Tab icons
TAB_ICONS = {"map": "🗺️", "status": "📊", "activity": "📈"}

# Map settings
DEFAULT_MAP_ZOOM = 6
