"""
Base Service Class
Provides common functionality for all TABMON dashboard services.
"""

import os
import tempfile
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
from requests.auth import HTTPBasicAuth


class BaseService:
    """Base service class with common data handling functionality."""

    def __init__(self, data_source: str):
        self.data_source = data_source
        self._temp_files = {}

    def _get_auth(self):
        """Get authentication for HTTP requests."""
        username = os.getenv("AUTH_USERNAME")
        password = os.getenv("AUTH_PASSWORD")
        if not username or not password:
            raise ValueError("AUTH_USERNAME and AUTH_PASSWORD required")
        return HTTPBasicAuth(username, password)

    def _is_healthy(self, url: str) -> bool:
        """Check if data source is accessible."""
        if not url.startswith(("http://", "https://")):
            return Path(url).exists()
        
        try:
            response = requests.head(url, auth=self._get_auth(), timeout=120)
            return response.status_code == 200
        except Exception:
            return False

    def _download_data(self, url: str) -> pd.DataFrame:
        """Download and return DataFrame from URL or local file."""
        if not url.startswith(("http://", "https://")):
            return pd.read_parquet(url)

        # Check health first
        if not self._is_healthy(url):
            st.error("🔥 Data source unavailable")
            return pd.DataFrame()

        try:
            response = requests.get(url, auth=self._get_auth(), timeout=120, stream=True)
            
            if response.status_code != 200:
                st.error(f"❌ Download failed: HTTP {response.status_code}")
                return pd.DataFrame()

            # Stream to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.parquet')
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            temp_file.close()

            # Read and cleanup
            data = pd.read_parquet(temp_file.name)
            os.unlink(temp_file.name)
            return data

        except Exception as e:
            st.error(f"💥 Error: {str(e)}")
            return pd.DataFrame()