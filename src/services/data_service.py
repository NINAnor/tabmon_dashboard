"""
Data service for TABMON dashboard.
Handles all data loading, processing, and caching operations.
"""

import os
import tempfile
from datetime import datetime, timedelta, timezone

import duckdb
import pandas as pd
import requests
import streamlit as st
from requests.auth import HTTPBasicAuth

from config.settings import (
    ASSETS_PARQUET_FILE,
    ASSETS_SITE_CSV,
    CACHE_TTL,
    COUNTRY_MAP,
    DATA_START_DATE,
    OFFLINE_THRESHOLD_DAYS,
)
from utils.data_loader import load_site_info


class DataService:
    """Service class for handling all data operations."""

    def __init__(
        self, site_csv: str = ASSETS_SITE_CSV, parquet_file: str = ASSETS_PARQUET_FILE
    ):
        """Initialize DataService with data source paths or URLs."""
        self.site_csv = site_csv
        self.parquet_file = parquet_file
        self._temp_files = {}  # Track temporary files for cleanup

    def _get_auth(self):
        """Get authentication for HTTP requests from environment."""
        username = os.getenv("AUTH_USERNAME", "guest")
        password = os.getenv("AUTH_PASSWORD", "ninaguest")
        return HTTPBasicAuth(username, password)

    def _get_file_path(self, url_or_path: str, file_type: str = "csv") -> str:
        """Get local file path from URL or return existing path."""
        if url_or_path.startswith(("http://", "https://")):
            # It's a URL, download to temporary file
            cache_key = f"{file_type}_{hash(url_or_path)}"

            if cache_key not in self._temp_files:
                auth = self._get_auth()
                response = requests.get(url_or_path, auth=auth)

                if response.status_code != 200:
                    raise Exception(
                        f"Failed to download {url_or_path}: HTTP {response.status_code}"
                    )

                # Create temporary file
                suffix = f".{file_type}"
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                temp_file.write(response.content)
                temp_file.close()

                self._temp_files[cache_key] = temp_file.name

            return self._temp_files[cache_key]
        else:
            # It's already a local path
            return url_or_path

    @st.cache_data(ttl=CACHE_TTL, show_spinner=False)
    def load_device_status(
        _self, offline_threshold_days: int = OFFLINE_THRESHOLD_DAYS
    ) -> pd.DataFrame:
        """Load and calculate comprehensive device status from parquet file with site info."""
        # Get local file paths (download if URLs)
        parquet_path = _self._get_file_path(_self.parquet_file, "parquet")
        site_csv_path = _self._get_file_path(_self.site_csv, "csv")

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

        df_status = duckdb.execute(query, (parquet_path,)).df()

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

        # Load site information first
        site_info = load_site_info(site_csv_path)

        site_info = site_info[site_info["Active"] == True].copy()

        # Create mapping between device IDs - use consistent 8-character suffix
        site_info["short_device"] = site_info["DeviceID"].str.strip().str[-8:]
        df_status["short_device"] = df_status["short_device"].str.strip()

        # Start with all active sites and merge recording data into them
        # This ensures we get exactly 100 devices (all active sites)
        merged = pd.merge(site_info, df_status, on="short_device", how="left")

        # Fill missing values for sites with no recordings
        merged["device_name"] = merged["device"].fillna("RPiID-" + merged["DeviceID"])
        merged["last_file"] = merged["last_file"].fillna(pd.NaT)
        merged["total_recordings"] = merged["total_recordings"].fillna(0)
        merged["status"] = merged["status"].fillna(
            "Offline"
        )  # Sites with no recordings are offline

        # Add country mapping - Country column should already exist from site_info
        # If not, create it from device country codes if available
        if "Country" not in merged.columns:
            merged["Country"] = "Unknown"

        # Fill missing Country values
        merged["Country"] = merged["Country"].fillna("Unknown")

        # Rename columns to match expected interface
        merged = merged.rename(
            columns={"device": "device_name", "Site": "site_name", "Cluster": "cluster"}
        )

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
                return float("inf")  # Infinite days for devices with no recordings
            return (now - last_file_dt).total_seconds() / 86400

        merged["days_since_last"] = (
            merged["last_file"].apply(calculate_days_since).round(1)
        )

        # We should now have exactly 100 devices (all active sites)
        return merged

    @st.cache_data(ttl=CACHE_TTL, show_spinner=False)
    def load_site_info(_self) -> pd.DataFrame:
        """Load site information from CSV file."""
        site_csv_path = _self._get_file_path(_self.site_csv, "csv")
        return load_site_info(site_csv_path)

    @st.cache_data(ttl=CACHE_TTL, show_spinner=False)
    def load_recording_matrix(_self, time_granularity: str = "day") -> pd.DataFrame:
        """Load and process recording matrix data."""
        # Get local file paths (download if URLs)
        parquet_path = _self._get_file_path(_self.parquet_file, "parquet")
        site_csv_path = _self._get_file_path(_self.site_csv, "csv")

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

        data = duckdb.execute(query, (parquet_path, DATA_START_DATE)).df()

        if data.empty:
            return pd.DataFrame()

        # Extract device ID from path
        data["short_device_id"] = (
            data["Path"]
            .str.split("/")
            .str[-3]
            .str.split("-")
            .str[-1]
            .str[-8:]
            .str.strip()
        )

        # Load site info
        site_info = load_site_info(site_csv_path)
        site_info = site_info[site_info["Active"] == True].copy()
        site_info["clean_id"] = site_info["DeploymentID"].str.strip()
        data["clean_id"] = data["short_device_id"].str.strip()

        # Merge data
        df_merged = pd.merge(data, site_info, on="clean_id", how="left")

        # Map countries
        for code, country_name in COUNTRY_MAP.items():
            df_merged.loc[df_merged["country"] == code, "Country"] = country_name

        # Create time periods based on granularity
        if time_granularity == "Day":
            df_merged["time_period"] = (
                df_merged["datetime"].dt.to_period("D").astype(str)
            )
        elif time_granularity == "Week":
            df_merged["time_period"] = (
                df_merged["datetime"].dt.to_period("W").astype(str)
            )
        else:  # Month
            df_merged["time_period"] = (
                df_merged["datetime"].dt.to_period("M").astype(str)
            )

        # Create matrix
        matrix_data = pd.crosstab(
            index=[df_merged["Country"], df_merged["device"]],
            columns=df_merged["time_period"],
            values=df_merged["datetime"],
            aggfunc="count",
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
        online_percentage = (
            (online_devices / total_devices * 100) if total_devices > 0 else 0
        )

        return {
            "total_devices": total_devices,
            "online_devices": online_devices,
            "offline_devices": offline_devices,
            "online_percentage": online_percentage,
            "offline_percentage": 100 - online_percentage,
        }

    def cleanup_temp_files(self):
        """Clean up temporary files."""
        for temp_file in self._temp_files.values():
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception:
                pass  # Ignore errors during cleanup
        self._temp_files.clear()
