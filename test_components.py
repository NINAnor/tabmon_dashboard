#!/usr/bin/env python3
"""
Test script for the modular TABMON dashboard components
"""
import sys
import os
sys.path.append('src')

print("🧪 Testing TABMON Dashboard Components...")

try:
    print("1. Testing configuration imports...")
    from config.settings import APP_TITLE, ASSETS_SITE_CSV, ASSETS_PARQUET_FILE
    print(f"   ✅ App title: {APP_TITLE}")
    print(f"   ✅ Site CSV: {ASSETS_SITE_CSV}")
    print(f"   ✅ Parquet file: {ASSETS_PARQUET_FILE}")
    
    print("2. Testing DataService initialization...")
    from services.data_service import DataService
    data_service = DataService()
    print(f"   ✅ DataService initialized with paths:")
    print(f"      - Site CSV: {data_service.site_csv}")
    print(f"      - Parquet: {data_service.parquet_file}")
    
    print("3. Testing component imports...")
    from components.ui_styles import load_custom_css, render_page_header
    print("   ✅ UI styles imported")
    
    from components.metrics import render_status_metrics
    print("   ✅ Metrics component imported")
    
    from components.charts import render_activity_heatmap
    print("   ✅ Charts component imported")
    
    from components.tables import render_status_table
    print("   ✅ Tables component imported")
    
    from components.map_viz import render_device_map
    print("   ✅ Map visualization imported")
    
    from components.sidebar import render_complete_sidebar
    print("   ✅ Sidebar component imported")
    
    from components.filters import render_complete_filters
    print("   ✅ Filters component imported")
    
    print("4. Testing main dashboard import...")
    from map_dashboard import app
    print("   ✅ Main dashboard app imported")
    
    print("5. Testing main app import...")
    from app import main
    print("   ✅ Main app imported")
    
    print("\n🎉 All components imported successfully!")
    print("✅ The modular TABMON dashboard is ready to run!")
    
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
