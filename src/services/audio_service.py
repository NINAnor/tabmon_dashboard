"""
Audio Service
Handles audio file operations and data processing for the TABMON dashboard.
"""

import pandas as pd
import streamlit as st

from config.settings import BASE_DATA_URL, CACHE_TTL


class AudioService:
    """Service for handling audio file operations and data processing."""

    def __init__(self):
        self.BASE_DIR = BASE_DATA_URL

    @st.cache_data(ttl=CACHE_TTL, show_spinner=False)
    def get_device_stats(_self, short_device_id: str) -> dict:
        """Get preprocessed statistics for a specific device."""
        device_stats_url = f"{_self.BASE_DIR}/data/preprocessed/all_device_stats.csv"
        device_stats = pd.read_csv(device_stats_url)

        # Filter for the specific device
        device_row = device_stats[device_stats["device_id"] == short_device_id]

        if device_row.empty:
            return {}

        row = device_row.iloc[0]
        earliest = pd.to_datetime(row["earliest_recording"])
        latest = pd.to_datetime(row["latest_recording"])

        return {
            "device_id": row["device_id"],
            "full_device_name": row["full_device_name"],
            "total_recordings": int(row["total_recordings"]),
            "total_size_gb": float(row["total_size_gb"]),
            "avg_file_size_mb": float(row["avg_file_size_mb"]),
            "date_range": {"earliest": earliest, "latest": latest},
        }

    @st.cache_data(ttl=CACHE_TTL, show_spinner=False)
    def get_total_dataset_stats(_self) -> dict:
        """Get statistics for the entire audio dataset."""
        dataset_stats_url = f"{_self.BASE_DIR}/data/preprocessed/dataset_stats.csv"
        result = pd.read_csv(dataset_stats_url)

        return {
            "total_recordings": int(result["total_recordings"].iloc[0])
            if not result.empty
            else 0,
            "total_size_gb": float(result["total_size_bytes"].iloc[0])
            / (1024 * 1024 * 1024)
            if not result.empty and pd.notna(result["total_size_bytes"].iloc[0])
            else 0,
        }
