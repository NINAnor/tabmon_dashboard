"""
Site Metadata Service
Handles site metadata and image operations for the TABMON dashboard.
"""

import pandas as pd
import streamlit as st

from .base_service import BaseService


class SiteMetadataService(BaseService):
    """Service for handling site metadata and image operations."""

    def __init__(self, parquet_file: str):
        super().__init__(parquet_file)

    @st.cache_data(ttl=3600, show_spinner=False)
    def generate_pictures_mapping(_self) -> pd.DataFrame:
        """Generate mapping of device pictures from parquet data."""
        try:
            data = _self._download_data(_self.data_source)
            if data.empty:
                return pd.DataFrame()

            # Filter for image files
            image_data = data[data["MimeType"].isin(["image/jpeg", "image/png"])]
            if image_data.empty:
                return pd.DataFrame()

            # Extract device ID and picture type from filename
            image_data["deviceID"] = image_data["Name"].str.split("_").str[2]
            image_data["picture_type"] = (
                image_data["Name"].str.split("_").str[3].str.split(".").str[0]
            )
            image_data["url"] = "/data/" + image_data["Path"]

            return image_data

        except Exception as e:
            st.error(f"💥 Error generating pictures mapping: {str(e)}")
            return pd.DataFrame()

    def extract_device_id(self, record: pd.Series) -> str:
        """Extract short device ID from a site record."""
        device_id = record.get("DeviceID", "")
        if "_" in device_id:
            return device_id.split("_")[-1].strip()
        else:
            return device_id[-8:] if len(device_id) >= 8 else device_id
