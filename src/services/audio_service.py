"""
Audio Service
Handles audio file operations and data processing for the TABMON dashboard.
"""

from datetime import datetime

import pandas as pd
import streamlit as st

from utils.data_loader import parse_file_datetime

from .base_service import BaseService


class AudioService(BaseService):
    """Service for handling audio file operations and data processing."""

    def __init__(self, parquet_file: str):
        super().__init__(parquet_file)

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_audio_files_by_device(_self, short_device_id: str) -> pd.DataFrame:
        """Get all audio files for a specific device."""
        try:
            data = _self._download_data(_self.data_source)
            if data.empty:
                return pd.DataFrame()

            # Filter for audio files and specific device
            audio_data = data[
                (data["MimeType"] == "audio/mpeg")
                & (data["device"].str.endswith(short_device_id))
            ]

            if audio_data.empty:
                return pd.DataFrame()

            # Parse recording timestamps
            audio_data = audio_data.copy()
            audio_data["recorded_at"] = audio_data["Name"].apply(parse_file_datetime)
            audio_data = audio_data.dropna(subset=["recorded_at"])
            return audio_data.sort_values(by="recorded_at", ascending=False)

        except Exception as e:
            st.error(f"💥 Error loading audio files: {str(e)}")
            return pd.DataFrame()

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_total_dataset_stats(_self) -> dict:
        """Get statistics for the entire audio dataset."""
        try:
            data = _self._download_data(_self.data_source)
            if data.empty:
                return {"total_recordings": 0, "total_size_gb": 0}

            # Filter for audio files
            audio_data = data[data["MimeType"] == "audio/mpeg"]
            if audio_data.empty:
                return {"total_recordings": 0, "total_size_gb": 0}

            return {
                "total_recordings": len(audio_data),
                "total_size_gb": audio_data["Size"].sum() / (1024 * 1024 * 1024)
                if "Size" in audio_data.columns
                else 0,
            }

        except Exception as e:
            st.error(f"� Error loading dataset stats: {str(e)}")
            return {"total_recordings": 0, "total_size_gb": 0}

    def find_closest_recordings(
        self, audio_data: pd.DataFrame, target_datetime: datetime, limit: int = 10
    ) -> pd.DataFrame:
        """Find recordings closest to a target datetime."""
        if audio_data.empty:
            return pd.DataFrame()

        audio_data = audio_data.copy()
        audio_data["time_diff"] = (audio_data["recorded_at"] - target_datetime).abs()
        return audio_data.sort_values(by="time_diff").head(limit)

    def get_audio_stats(self, audio_data: pd.DataFrame) -> dict:
        """Calculate statistics for audio data."""
        if audio_data.empty:
            return {}

        return {
            "total_recordings": len(audio_data),
            "date_range": {
                "earliest": audio_data["recorded_at"].min(),
                "latest": audio_data["recorded_at"].max(),
            },
            "total_size_gb": audio_data["Size"].sum() / (1024 * 1024 * 1024)
            if "Size" in audio_data.columns
            else 0,
        }

    def extract_device_id(self, record: pd.Series) -> str:
        """Extract short device ID from a site record."""
        full_device_id = record.get("DeviceID", "")
        if "_" in full_device_id:
            return full_device_id.split("_")[-1].strip()
        else:
            return full_device_id[-8:] if len(full_device_id) >= 8 else full_device_id
