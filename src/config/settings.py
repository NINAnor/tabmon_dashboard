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
MAX_ZOOM_LEVEL = 7              # Maximum zoom level (prevents very detailed viewing) - hardcoded for privacy
MIN_ZOOM_LEVEL = 3              # Minimum zoom level

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
