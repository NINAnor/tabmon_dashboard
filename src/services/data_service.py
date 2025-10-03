"""
Data service for TABMON dashboard.
Handles all data loading, processing, and caching operations.
"""

from datetime import datetime, timedelta, timezone

import duckdb
import pandas as pd
import streamlit as st

from config.settings import (
    ASSETS_PARQUET_FILE,
    ASSETS_SITE_CSV,
    CACHE_TTL,
    OFFLINE_THRESHOLD_DAYS,
)
from utils.data_loader import load_site_info

from .base_service import BaseService


class DataService(BaseService):
    """Service class for handling all data operations."""

    def __init__(
        self,
        site_csv: str = ASSETS_SITE_CSV,
        parquet_file: str = ASSETS_PARQUET_FILE,
    ):
        super().__init__(parquet_file)
        self.site_csv = site_csv
        self.parquet_file = parquet_file

    @st.cache_data(ttl=CACHE_TTL, show_spinner=False)
    def load_device_status(
        _self, offline_threshold_days: int = OFFLINE_THRESHOLD_DAYS
    ) -> pd.DataFrame:
        """Load and calculate comprehensive device status."""
        try:
            # Download data
            parquet_data = _self._download_data(_self.parquet_file)
            if parquet_data.empty:
                return pd.DataFrame()

            # Get device status using DuckDB
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
            FROM parquet_data
            WHERE MimeType = 'audio/mpeg'
            GROUP BY device, short_device
            """
            df_status = duckdb.execute(query).df()

            if df_status.empty:
                return pd.DataFrame()

            # Calculate status
            now = datetime.now(timezone.utc)
            threshold = timedelta(days=offline_threshold_days)

            def calculate_status(t):
                if pd.isna(t):
                    return "Offline"
                if t.tzinfo is None:
                    t = t.replace(tzinfo=timezone.utc)
                return "Offline" if now - t > threshold else "Online"

            df_status["status"] = df_status["last_file"].apply(calculate_status)

            # Load and merge site info
            if _self.site_csv.startswith(("http://", "https://")):
                site_data = _self._download_data(_self.site_csv)
            else:
                site_data = load_site_info(_self.site_csv)

            site_data = site_data[site_data["Active"]].copy()
            site_data["short_device"] = site_data["DeviceID"].str.strip().str[-8:]

            # Merge and process
            merged = pd.merge(site_data, df_status, on="short_device", how="left")
            merged["device_name"] = merged["device"].fillna(
                "RPiID-" + merged["DeviceID"]
            )
            merged["last_file"] = merged["last_file"].fillna(pd.NaT)
            merged["total_recordings"] = merged["total_recordings"].fillna(0)
            merged["status"] = merged["status"].fillna("Offline")
            merged["Country"] = merged.get("Country", "Unknown").fillna("Unknown")
            merged = merged.rename(columns={"Site": "site_name", "Cluster": "cluster"})

            # Calculate days since last recording
            def calculate_days_since(last_file_dt):
                if pd.isna(last_file_dt):
                    return float("inf")
                if last_file_dt.tzinfo is None:
                    last_file_dt = last_file_dt.replace(tzinfo=timezone.utc)
                return (now - last_file_dt).total_seconds() / 86400

            merged["days_since_last"] = (
                merged["last_file"].apply(calculate_days_since).round(1)
            )
            return merged

        except Exception as e:
            st.error(f"💥 Error loading device status: {str(e)}")
            return pd.DataFrame()

    @st.cache_data(ttl=CACHE_TTL, show_spinner=False)
    def load_site_info(_self) -> pd.DataFrame:
        """Load site information."""
        return _self._download_data(_self.site_csv)

    @st.cache_data(ttl=CACHE_TTL, show_spinner=False)
    def load_recording_matrix(_self, time_granularity: str = "day") -> pd.DataFrame:
        """Load and process recording matrix data."""
        try:
            parquet_data = _self._download_data(_self.parquet_file)
            if parquet_data.empty:
                return pd.DataFrame()

            # Use DuckDB for efficient processing
            query = """
            SELECT *,
                COALESCE(
                    TRY_STRPTIME(Name, '%Y-%m-%dT%H_%M_%S.%fZ.mp3'),
                    TRY_STRPTIME(Name, '%Y-%m-%dT%H_%M_%SZ.mp3'),
                    STRPTIME(Name, '%Y-%m-%dT%H_%MZ.mp3')
                ) AS datetime
            FROM parquet_data
            WHERE MimeType = 'audio/mpeg'
            AND datetime >= '2024-01-01'
            """
            return duckdb.execute(query).df()

        except Exception as e:
            st.error(f"💥 Error loading recording matrix: {str(e)}")
            return pd.DataFrame()

    def calculate_metrics(self, device_data: pd.DataFrame) -> dict:
        """Calculate dashboard metrics from device data."""
        if device_data.empty:
            return {
                "total_devices": 0,
                "online_devices": 0,
                "offline_devices": 0,
                "countries": 0,
            }

        total_devices = len(device_data)
        online_devices = len(device_data[device_data["status"] == "Online"])
        offline_devices = total_devices - online_devices
        countries = device_data["Country"].nunique()

        return {
            "total_devices": total_devices,
            "online_devices": online_devices,
            "offline_devices": offline_devices,
            "countries": countries,
        }
