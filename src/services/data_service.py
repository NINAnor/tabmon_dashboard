"""
Data service for TABMON dashboard.
Handles all data loading, processing, and caching operations.
"""

import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import duckdb
import pandas as pd
import requests
import streamlit as st

from config.settings import (
    ASSETS_PARQUET_FILE,
    ASSETS_SITE_CSV,
    CACHE_TTL,
    COUNTRY_MAP,
    DATA_START_DATE,
    OFFLINE_THRESHOLD_DAYS,
    BASE_DATA_URL
)
from utils.data_loader import load_site_info


class DataService:
    """Service class for handling all data operations."""

    def __init__(
        self, site_csv: str = ASSETS_SITE_CSV, parquet_file: str = ASSETS_PARQUET_FILE, base_dir: str = BASE_DATA_URL
    ):
        """Initialize DataService with data source paths or URLs."""
        self.site_csv = site_csv
        self.parquet_file = parquet_file
        self._temp_files = {} 
        self.base_dir = base_dir

    @st.cache_data(ttl=CACHE_TTL, show_spinner=False)
    def load_device_status(_self) -> pd.DataFrame:
        """Load device status from preprocessed CSV file."""
        device_status_url = f"{_self.base_dir}/data/preprocessed/device_status.csv"
        df = pd.read_csv(device_status_url)
        return df   

    @st.cache_data(ttl=CACHE_TTL, show_spinner=False)
    def load_site_info(_self) -> pd.DataFrame:
        return load_site_info(f"{_self.base_dir}/site_info.csv")

    @st.cache_data(ttl=CACHE_TTL, show_spinner=False)
    def load_recording_matrix(_self) -> pd.DataFrame:
        return pd.read_csv(f"{_self.base_dir}/data/preprocessed/recording_matrix.csv", index_col=[0,1])

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
