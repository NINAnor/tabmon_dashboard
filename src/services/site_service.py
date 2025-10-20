import pandas as pd
import streamlit as st

from config.settings import BASE_DATA_URL, CACHE_TTL


class SiteService:
    """Service for handling site operations and data processing."""

    def __init__(self):
        self.BASE_DIR = BASE_DATA_URL

    @st.cache_data(ttl=CACHE_TTL, show_spinner=False)
    def get_image_mapping(_self):
        """Get preprocessed statistics for a specific device."""
        device_mapping_url = f"{_self.BASE_DIR}/data/preprocessed/image_mapping.csv"
        return pd.read_csv(device_mapping_url)
