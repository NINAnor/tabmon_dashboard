"""
Base Service Class
Provides common functionality for all TABMON dashboard services.
"""

import os
import tempfile
from pathlib import Path

import backoff
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

    @backoff.on_exception(
        backoff.expo,
        (requests.exceptions.ConnectionError, requests.exceptions.Timeout),
        max_tries=3,
        max_time=300,
        on_backoff=lambda details: st.warning(
            f"🔄 Connection retry {details['tries']}/3 - waiting {details['wait']:.1f}s"
        ),
    )
    def _is_healthy(self, url: str) -> bool:
        """Check if data source is accessible with retry logic."""
        if not url.startswith(("http://", "https://")):
            return Path(url).exists()

        try:
            response = requests.head(url, auth=self._get_auth(), timeout=30)
            return response.status_code == 200
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            # Re-raise to trigger backoff retry
            raise
        except Exception:
            # Other exceptions (like auth errors) should not be retried
            return False

    @backoff.on_exception(
        backoff.expo,
        (requests.exceptions.ConnectionError, requests.exceptions.Timeout),
        max_tries=3,
        max_time=300,
        on_backoff=lambda details: st.warning(
            f"🔄 Download retry {details['tries']}/3 - waiting {details['wait']:.1f}s"
        ),
    )
    def _download_data(self, url: str) -> pd.DataFrame:
        """Download and return DataFrame from URL or local file with retry logic."""
        if not url.startswith(("http://", "https://")):
            try:
                if url.endswith(".parquet"):
                    return pd.read_parquet(url)
                elif url.endswith(".csv"):
                    return pd.read_csv(url)
                else:
                    # Try to infer format
                    return pd.read_parquet(url)
            except Exception as e:
                st.error(f"💥 Error reading local file: {str(e)}")
                return pd.DataFrame()

        # Check health first
        if not self._is_healthy(url):
            st.error("🔥 Data source unavailable after retries")
            return pd.DataFrame()

        try:
            response = requests.get(
                url, auth=self._get_auth(), timeout=120, stream=True
            )

            if response.status_code == 429:  # Rate limiting
                st.warning("⏳ Rate limited, retrying...")
                raise requests.exceptions.ConnectionError("Rate limited")

            if response.status_code != 200:
                st.error(f"❌ Download failed: HTTP {response.status_code}")
                return pd.DataFrame()

            # Stream to temporary file
            suffix = ".parquet" if "parquet" in url else ".csv"
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)

            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            temp_file.close()

            # Read and cleanup
            try:
                if suffix == ".parquet":
                    data = pd.read_parquet(temp_file.name)
                else:
                    data = pd.read_csv(temp_file.name)
            finally:
                Path(temp_file.name).unlink()

            return data

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            # Re-raise to trigger backoff retry
            raise
        except Exception as e:
            st.error(f"💥 Error: {str(e)}")
            return pd.DataFrame()

    def _download_csv_data(self, url: str) -> pd.DataFrame:
        """Download CSV data specifically (wrapper for backward compatibility)."""
        return self._download_data(url)
