#!/usr/bin/env python3
"""
Debug merge issues step by step
"""
import sys
sys.path.append('src')

import pandas as pd
import duckdb
from utils.data_loader import load_site_info

def main():
    print("🔍 Step-by-step Merge Debug")
    print("=" * 50)
    
    # URLs that work inside Docker network
    site_csv_url = "http://rclone:8081/data/site_info.csv"
    parquet_url = "http://rclone:8081/data/index.parquet"
    
    try:
        print("1. Loading site info...")
        site_info = load_site_info(site_csv_url)
        active_sites = site_info[site_info["Active"] == True].copy()
        print(f"   Active sites: {len(active_sites)}")
        
        # Process device IDs
        active_sites["short_device"] = active_sites["DeviceID"].str.strip().str[-8:]
        print(f"   Sample short_device IDs: {active_sites['short_device'].head(3).tolist()}")
        print()
        
        print("2. Loading parquet data...")
        query = """
        SELECT 
            device,
            RIGHT(device, 8) AS short_device,
            COUNT(*) as total_recordings
        FROM read_parquet(?)
        WHERE MimeType = 'audio/mpeg'
        GROUP BY device, short_device
        """
        
        df_status = duckdb.execute(query, (parquet_url,)).df()
        print(f"   Devices with recordings: {len(df_status)}")
        print(f"   Sample recording short_device: {df_status['short_device'].head(3).tolist()}")
        print()
        
        print("3. Checking device ID overlap...")
        site_device_ids = set(active_sites['short_device'])
        recording_device_ids = set(df_status['short_device'])
        
        print(f"   Site device IDs: {len(site_device_ids)}")
        print(f"   Recording device IDs: {len(recording_device_ids)}")
        print(f"   Intersection: {len(site_device_ids.intersection(recording_device_ids))}")
        print(f"   Site devices with no recordings: {len(site_device_ids - recording_device_ids)}")
        print(f"   Recording devices not in sites: {len(recording_device_ids - site_device_ids)}")
        print()
        
        print("4. Testing LEFT JOIN (site_info first)...")
        left_merge = pd.merge(active_sites, df_status, on="short_device", how="left")
        print(f"   Result count: {len(left_merge)}")
        print(f"   Expected: 100 (should match active sites)")
        
        no_recordings = left_merge[left_merge['device'].isna()]
        print(f"   Sites with no recordings: {len(no_recordings)}")
        
        if len(no_recordings) > 0:
            print("   Sample sites with no recordings:")
            print(no_recordings[['DeviceID', 'short_device', 'Country', 'Site']].head(3))
        print()
        
        print("5. Testing coordinate availability...")
        with_coords = left_merge[(left_merge['Latitude'].notna()) & (left_merge['Longitude'].notna())]
        print(f"   Devices with coordinates: {len(with_coords)}")
        
        if len(with_coords) < len(left_merge):
            without_coords = left_merge[(left_merge['Latitude'].isna()) | (left_merge['Longitude'].isna())]
            print(f"   Devices without coordinates: {len(without_coords)}")
            print("   Sample devices without coordinates:")
            print(without_coords[['DeviceID', 'Country', 'Site', 'Latitude', 'Longitude']].head(3))
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
