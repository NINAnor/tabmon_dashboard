#!/usr/bin/env python3
"""
Debug script to check device count issues
"""
import sys
sys.path.append('src')

from utils.data_loader import load_site_info
from services.data_service import DataService

def main():
    print("🔍 Debug: Device Count Analysis")
    print("=" * 50)
    
    # URLs that work inside Docker network
    site_csv_url = "http://rclone:8081/data/site_info.csv"
    parquet_url = "http://rclone:8081/data/index.parquet"
    
    try:
        # Load site info directly
        print("1. Loading site info...")
        site_info = load_site_info(site_csv_url)
        print(f"   Total sites in CSV: {len(site_info)}")
        
        active_sites = site_info[site_info['Active'] == True]
        print(f"   Active sites: {len(active_sites)}")
        print(f"   Sample DeviceIDs: {active_sites['DeviceID'].head(3).tolist()}")
        print()
        
        # Load device data through service
        print("2. Loading device data through DataService...")
        data_service = DataService(site_csv_url, parquet_url)
        
        # Clear any cached data by creating a new instance with slightly different params
        import importlib
        import services.data_service
        importlib.reload(services.data_service)
        from services.data_service import DataService
        
        data_service = DataService(site_csv_url, parquet_url)
        device_data = data_service.load_device_status()
        
        print(f"   Devices loaded: {len(device_data)}")
        print(f"   Online devices: {len(device_data[device_data['status'] == 'Online'])}")
        print(f"   Offline devices: {len(device_data[device_data['status'] == 'Offline'])}")
        print()
        
        # Check columns
        print("3. Column analysis...")
        print(f"   Columns: {device_data.columns.tolist()}")
        print()
        
        # Check sample data
        print("4. Sample data...")
        print(device_data[['device_name', 'status', 'Country', 'site_name', 'total_recordings']].head())
        print()
        
        # Check for devices with no recordings
        no_recordings = device_data[device_data['total_recordings'] == 0]
        print(f"5. Devices with no recordings: {len(no_recordings)}")
        
        # Check coordinate data
        coord_data = device_data[['device_name', 'Latitude', 'Longitude']].dropna()
        print(f"6. Devices with coordinates: {len(coord_data)}")
        
        # Check merge quality
        print("7. Merge quality check...")
        unknown_country = device_data[device_data['Country'] == 'Unknown']
        print(f"   Devices with unknown country: {len(unknown_country)}")
        
        missing_site = device_data[device_data['site_name'].isna()]
        print(f"   Devices with missing site name: {len(missing_site)}")
        
        # Show some examples of devices not matching
        if len(unknown_country) > 0:
            print("   Sample unknown country devices:")
            print(unknown_country[['device_name', 'short_device', 'Country', 'site_name']].head(3))
        
        print(f"8. Total active vs loaded comparison:")
        print(f"   Active sites in CSV: {len(active_sites)}")
        print(f"   Loaded devices: {len(device_data)}")
        print(f"   Expected: All 100 active devices should be loaded")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
