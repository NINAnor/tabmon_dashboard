"""
Site Metadata Service
Handles site metadata and image operations for the TABMON dashboard.
"""

import duckdb
import pandas as pd
import streamlit as st


class SiteMetadataService:
    """Service for handling site metadata and image operations."""
    
    def __init__(self, parquet_file: str):
        self.parquet_file = parquet_file
    
    @st.cache_data(ttl=3600, show_spinner=False)
    def generate_pictures_mapping(_self) -> pd.DataFrame:
        """Generate mapping of device pictures from parquet data."""
        try:
            # Check if we're dealing with a URL or local file
            if _self.parquet_file.startswith(('http://', 'https://')):
                # For URLs, we need to load the data first then filter
                data = pd.read_parquet(_self.parquet_file)
                # Filter for image files
                data = data[data["MimeType"].isin(['image/jpeg', 'image/png'])]
            else:
                # For local files, use DuckDB for efficient filtering
                query = """
                SELECT * FROM read_parquet(?)
                WHERE MimeType IN ('image/jpeg', 'image/png')
                """
                data = duckdb.execute(query, (_self.parquet_file,)).df()
            
            if data.empty:
                return pd.DataFrame()
            
            # Extract device ID and picture type from filename
            data["deviceID"] = data["Name"].str.split("_").str[2]
            data["picture_type"] = data["Name"].str.split("_").str[3].str.split(".").str[0]
            data["url"] = "/data/" + data["Path"]
            
            return data
        except Exception as e:
            st.error(f"Failed to generate pictures mapping: {e}")
            return pd.DataFrame()
    
    def extract_device_id(self, record: pd.Series) -> str:
        """Extract short device ID from a site record."""
        device_id = record.get("DeviceID", "")
        if "_" in device_id:
            return device_id.split("_")[-1].strip()
        else:
            return device_id[-8:] if len(device_id) >= 8 else device_id
