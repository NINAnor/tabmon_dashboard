"""
Data service for TABMON dashboard.
Handles all data loading, processing, and caching operations.
"""

import pandas as pd
import streamlit as st

from config.settings import BASE_DATA_URL, CACHE_TTL, PARQUET_FILE_URL, SITE_CSV_URL
from utils.data_loader import load_site_info


class DataService:
    """Service class for handling all data operations."""

    def __init__(self):
        """Initialize DataService with centralized configuration."""
        self.site_csv = SITE_CSV_URL
        self.parquet_file = PARQUET_FILE_URL
        self._temp_files = {}
        self.base_dir = BASE_DATA_URL

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
        return pd.read_csv(
            f"{_self.base_dir}/data/preprocessed/recording_matrix.csv", index_col=[0, 1]
        )

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
