"""
Data service for TABMON dashboard.
Handles all data loading, processing, and c        data = duckdb.execute(query, (_self.parquet_file, DATA_START_DATE)).df()
        
        if data.empty:
            return pd.DataFrame()
        
        # Extract device ID from path
        data["short_device_id"] = (
            data["Path"]
            .str.split("/").str[-3]
            .str.split("-").str[-1]
            .str[-8:].str.strip()
        )
        
        # Load site info
        site_info = load_site_info(_self.site_csv)ns.
"""

from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional

import duckdb
import pandas as pd
import streamlit as st

from config.settings import (
    OFFLINE_THRESHOLD_DAYS, 
    DATA_START_DATE, 
    COUNTRY_MAP, 
    CACHE_TTL,
    ASSETS_SITE_CSV,
    ASSETS_PARQUET_FILE
)
from utils.data_loader import load_site_info


class DataService:
    """Service class for handling all data operations."""
    
    def __init__(self, site_csv: str = ASSETS_SITE_CSV, parquet_file: str = ASSETS_PARQUET_FILE):
        """Initialize DataService with data source paths."""
        self.site_csv = site_csv
        self.parquet_file = parquet_file
    
    @st.cache_data(ttl=CACHE_TTL, show_spinner=False)
    def load_device_status(_self, offline_threshold_days: int = OFFLINE_THRESHOLD_DAYS) -> pd.DataFrame:
        """Load and calculate comprehensive device status from parquet file with site info."""
        # First get device status from recordings
        query = """
        SELECT 
            device,
            REGEXP_EXTRACT(device, '10000000(.+)$', 1) AS short_device,
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
        
        df_status = duckdb.execute(query, (_self.parquet_file,)).df()
        
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
        
        df_status["status"] = df_status["last_file"].apply(calculate_status)
        
        # Load site information
        site_info = load_site_info(_self.site_csv)
        site_info = site_info[site_info["Active"] == True].copy()
        
        # Create mapping between device IDs
        site_info["short_device"] = site_info["DeviceID"].str.strip()
        df_status["short_device"] = df_status["short_device"].str.strip()
        
        # Merge with site information
        merged = pd.merge(df_status, site_info, on="short_device", how="left")
        
        # Add country mapping - Country column should already exist from site_info
        # If not, create it from device country codes if available
        if 'Country' not in merged.columns:
            merged['Country'] = 'Unknown'
        
        # Fill missing Country values
        merged['Country'] = merged['Country'].fillna('Unknown')
        
        # Rename columns to match expected interface
        merged = merged.rename(columns={
            'device': 'device_name',
            'Site': 'site_name',
            'Cluster': 'cluster'
        })
        
        # Calculate days since last recording
        # Ensure timezone consistency
        def make_timezone_aware(dt):
            if pd.isna(dt):
                return dt
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt
        
        merged["last_file"] = merged["last_file"].apply(make_timezone_aware)
        merged["days_since_last"] = (
            (now - merged["last_file"]).dt.total_seconds() / 86400
        ).round(1)
        
        return merged

    @st.cache_data(ttl=CACHE_TTL, show_spinner=False)
    def load_site_info(_self) -> pd.DataFrame:
        """Load site information from CSV file."""
        return load_site_info(_self.site_csv)
    
    @st.cache_data(ttl=CACHE_TTL, show_spinner=False)
    def load_recording_matrix(_self, time_granularity: str = "day") -> pd.DataFrame:
        """Load and process recording matrix data."""
        # Load parquet data with optimized query
        query = """
        SELECT *,
            COALESCE(
                TRY_STRPTIME(Name, '%Y-%m-%dT%H_%M_%S.%fZ.mp3'),
                TRY_STRPTIME(Name, '%Y-%m-%dT%H_%M_%SZ.mp3'),
                STRPTIME(Name, '%Y-%m-%dT%H_%MZ.mp3')
            ) AS datetime
        FROM read_parquet(?)
        WHERE MimeType = 'audio/mpeg'
        AND datetime >= ?
        """
        
        data = duckdb.execute(query, (_self.parquet_file, DATA_START_DATE)).df()
        
        if data.empty:
            return pd.DataFrame()
        
        # Extract device ID from path
        data["short_device_id"] = (
            data["Path"]
            .str.split("/").str[-3]
            .str.split("-").str[-1]
            .str[-8:].str.strip()
        )
        
        # Load site info
        site_info = load_site_info(_self.site_csv)
        site_info = site_info[site_info["Active"] == True].copy()
        site_info["clean_id"] = site_info["DeploymentID"].str.strip()
        data["clean_id"] = data["short_device_id"].str.strip()
        
        # Merge data
        df_merged = pd.merge(data, site_info, on="clean_id", how="left")
        
        # Map countries
        for code, country_name in COUNTRY_MAP.items():
            df_merged.loc[df_merged['country'] == code, 'Country'] = country_name
        
        # Create time periods based on granularity
        if time_granularity == "Day":
            df_merged["time_period"] = df_merged["datetime"].dt.to_period("D").astype(str)
        elif time_granularity == "Week":
            df_merged["time_period"] = df_merged["datetime"].dt.to_period("W").astype(str)
        else:  # Month
            df_merged["time_period"] = df_merged["datetime"].dt.to_period("M").astype(str)
        
        # Create matrix
        matrix_data = pd.crosstab(
            index=[df_merged["Country"], df_merged["device"]],
            columns=df_merged["time_period"],
            values=df_merged["datetime"],
            aggfunc="count"
        ).fillna(0)
        
        return matrix_data.sort_index()

    @staticmethod
    def calculate_metrics(status_df: pd.DataFrame) -> dict:
        """Calculate summary metrics from status data."""
        if status_df.empty:
            return {}
        
        total_devices = len(status_df)
        online_devices = len(status_df[status_df["status"] == "Online"])
        offline_devices = total_devices - online_devices
        online_percentage = (online_devices / total_devices * 100) if total_devices > 0 else 0
        
        return {
            'total_devices': total_devices,
            'online_devices': online_devices,
            'offline_devices': offline_devices,
            'online_percentage': online_percentage,
            'offline_percentage': 100 - online_percentage
        }
