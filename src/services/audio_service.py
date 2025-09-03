"""
Audio Service
Handles audio file operations and data processing for the TABMON dashboard.
"""

from datetime import datetime

import duckdb
import pandas as pd
import streamlit as st

from utils.data_loader import parse_file_datetime


class AudioService:
    """Service for handling audio file operations and data processing."""

    def __init__(self, parquet_file: str):
        self.parquet_file = parquet_file

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_audio_files_by_device(_self, short_device_id: str) -> pd.DataFrame:
        """Get all audio files for a specific device."""
        try:
            # Check if we're dealing with a URL or local file
            if _self.parquet_file.startswith(("http://", "https://")):
                # For URLs, load all data then filter
                data = pd.read_parquet(_self.parquet_file)
                # Filter for audio files and specific device
                audio_data = data[
                    (data["MimeType"] == "audio/mpeg")
                    & (data["device"].str.endswith(short_device_id))
                ]
            else:
                # For local files, use DuckDB for efficient filtering
                query = """
                SELECT *
                FROM read_parquet(?)
                WHERE MimeType = 'audio/mpeg'
                AND RIGHT(device, 8) = ?
                """
                audio_data = duckdb.execute(
                    query, (_self.parquet_file, short_device_id)
                ).df()

            if audio_data.empty:
                return pd.DataFrame()

            # Parse recording timestamps from filenames
            audio_data = audio_data.copy()  # Prevent SettingWithCopyWarning
            audio_data["recorded_at"] = audio_data["Name"].apply(parse_file_datetime)
            audio_data = audio_data.dropna(subset=["recorded_at"])

            # Sort by recording time (newest first)
            audio_data = audio_data.sort_values(by="recorded_at", ascending=False)

            return audio_data
        except Exception as e:
            st.error(f"Failed to load audio files: {e}")
            return pd.DataFrame()

    def find_closest_recordings(
        self, audio_data: pd.DataFrame, target_datetime: datetime, limit: int = 10
    ) -> pd.DataFrame:
        """Find recordings closest to a target datetime."""
        if audio_data.empty:
            return pd.DataFrame()

        # Calculate absolute time difference
        audio_data = audio_data.copy()
        audio_data["time_diff"] = (audio_data["recorded_at"] - target_datetime).abs()

        # Sort by time difference and limit results
        closest_recordings = audio_data.sort_values(by="time_diff").head(limit)

        return closest_recordings

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

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_total_dataset_stats(_self) -> dict:
        """Get statistics for the entire audio dataset."""
        try:
            # Check if we're dealing with a URL or local file
            if _self.parquet_file.startswith(("http://", "https://")):
                # For URLs, load all data then filter
                data = pd.read_parquet(_self.parquet_file)
                # Filter for audio files only
                audio_data = data[data["MimeType"] == "audio/mpeg"]
            else:
                # For local files, use DuckDB for efficient filtering
                query = """
                SELECT COUNT(*) as total_recordings, SUM(Size) as total_size_bytes
                FROM read_parquet(?)
                WHERE MimeType = 'audio/mpeg'
                """
                result = duckdb.execute(query, (_self.parquet_file,)).df()
                return {
                    "total_recordings": int(result["total_recordings"].iloc[0])
                    if not result.empty
                    else 0,
                    "total_size_gb": float(result["total_size_bytes"].iloc[0])
                    / (1024 * 1024 * 1024)
                    if not result.empty and pd.notna(result["total_size_bytes"].iloc[0])
                    else 0,
                }

            if audio_data.empty:
                return {"total_recordings": 0, "total_size_gb": 0}

            return {
                "total_recordings": len(audio_data),
                "total_size_gb": audio_data["Size"].sum() / (1024 * 1024 * 1024)
                if "Size" in audio_data.columns
                else 0,
            }
        except Exception as e:
            st.error(f"Failed to load total dataset stats: {e}")
            return {"total_recordings": 0, "total_size_gb": 0}

    def extract_device_id(self, record: pd.Series) -> str:
        """Extract short device ID from a site record."""
        full_device_id = record.get("DeviceID", "")
        if "_" in full_device_id:
            return full_device_id.split("_")[-1].strip()
        else:
            return full_device_id[-8:] if len(full_device_id) >= 8 else full_device_id
