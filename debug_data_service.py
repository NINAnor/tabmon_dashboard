#!/usr/bin/env python3
"""
Debug data service implementation exactly
"""
import sys
sys.path.append('src')

import pandas as pd
import duckdb
from datetime import datetime, timedelta, timezone
from utils.data_loader import load_site_info

def debug_load_device_status():
    """Copy exact implementation from DataService"""
    site_csv = "http://rclone:8081/data/site_info.csv" 
    parquet_file = "http://rclone:8081/data/index.parquet"
    offline_threshold_days = 7
    
    print("🔍 Debugging DataService.load_device_status() exactly")
    print("=" * 60)
    
    # First get device status from recordings
    query = """
    SELECT 
        device,
        RIGHT(device, 8) AS short_device,
        MAX(COALESCE(
            TRY_STRPTIME(Name, '%Y-%m-%dT%H_%M_%S.%fZ.mp3'),
            TRY_STRPTIME(Name, '%Y-%m-%dT%H_%M_%SZ.mp3'),
            STRPTIME(Name, '%Y-%m-%dT%H_%MZ.mp3')
        )) AS last_file,
        COUNT(*) as total_recordings
    FROM read_parquet(?)
    WHERE MimeType = 'audio/mpeg'
    GROUP BY device, short_device
    """
    
    print("1. Executing parquet query...")
    df_status = duckdb.execute(query, (parquet_file,)).df()
    print(f"   Records from parquet: {len(df_status)}")
    
    if df_status.empty:
        return pd.DataFrame()
    
    # Calculate status
    now = datetime.now(timezone.utc)
    threshold = timedelta(days=offline_threshold_days)
    
    def calculate_status(t):
        if pd.isna(t):
            return "Offline"
        # Ensure datetime is timezone-aware
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        return "Offline" if now - t > threshold else "Online"
    
    print("2. Calculating status...")
    df_status["status"] = df_status["last_file"].apply(calculate_status)
    
    # Load site information first
    print("3. Loading site info...")
    site_info = load_site_info(site_csv)
    print(f"   Total sites: {len(site_info)}")
    
    site_info = site_info[site_info["Active"] == True].copy()
    print(f"   Active sites: {len(site_info)}")
    
    # Create mapping between device IDs - use consistent 8-character suffix
    site_info["short_device"] = site_info["DeviceID"].str.strip().str[-8:]
    df_status["short_device"] = df_status["short_device"].str.strip()
    
    print("4. Device ID processing...")
    print(f"   Site short_device count: {len(site_info['short_device'].unique())}")
    print(f"   Recording short_device count: {len(df_status['short_device'].unique())}")
    
    # Start with all active sites and merge recording data into them
    # This ensures we get exactly 100 devices (all active sites)
    print("5. Performing merge (site_info LEFT JOIN recordings)...")
    merged = pd.merge(site_info, df_status, on="short_device", how="left")
    print(f"   Merged result count: {len(merged)}")
    
    # Fill missing values for sites with no recordings
    print("6. Filling missing values...")
    merged["device_name"] = merged["device"].fillna("RPiID-" + merged["DeviceID"])
    merged["last_file"] = merged["last_file"].fillna(pd.NaT)
    merged["total_recordings"] = merged["total_recordings"].fillna(0)
    merged["status"] = merged["status"].fillna("Offline")  # Sites with no recordings are offline
    
    # Add country mapping - Country column should already exist from site_info
    # If not, create it from device country codes if available
    if 'Country' not in merged.columns:
        merged['Country'] = 'Unknown'
    
    # Fill missing Country values
    merged['Country'] = merged['Country'].fillna('Unknown')
    
    # Rename columns to match expected interface
    merged = merged.rename(columns={
        'Site': 'site_name',
        'Cluster': 'cluster'
    })
    
    # Ensure device_name is properly set
    if 'device_name' not in merged.columns:
        merged['device_name'] = merged['device'].fillna("RPiID-" + merged["DeviceID"])
    
    print("7. Final processing...")
    # Calculate days since last recording
    # Ensure timezone consistency
    def make_timezone_aware(dt):
        if pd.isna(dt):
            return dt
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    
    merged["last_file"] = merged["last_file"].apply(make_timezone_aware)
    
    # Calculate days since last recording, handling NaT values
    def calculate_days_since(last_file_dt):
        if pd.isna(last_file_dt):
            return float('inf')  # Infinite days for devices with no recordings
        return (now - last_file_dt).total_seconds() / 86400
    
    merged["days_since_last"] = merged["last_file"].apply(calculate_days_since).round(1)
    
    print(f"8. Final result count: {len(merged)}")
    print(f"   With coordinates: {len(merged[(merged['Latitude'].notna()) & (merged['Longitude'].notna())])}")
    print(f"   Unknown countries: {len(merged[merged['Country'] == 'Unknown'])}")
    
    # We should now have exactly 100 devices (all active sites)
    return merged

def main():
    try:
        result = debug_load_device_status()
        print(f"\n✅ Final result: {len(result)} devices")
        
        if len(result) > 0:
            print("\nSample data:")
            print(result[['device_name', 'status', 'Country', 'site_name', 'total_recordings', 'Latitude', 'Longitude']].head())
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
