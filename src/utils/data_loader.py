import re
from datetime import datetime

import pandas as pd


def load_site_info(csv_file, delimiter=","):
    """Load site information from CSV file."""
    site_info = pd.read_csv(csv_file, delimiter=delimiter)

    # Convert coordinates to numeric values
    site_info["Latitude"] = pd.to_numeric(site_info["Latitude"], errors="coerce")
    site_info["Longitude"] = pd.to_numeric(site_info["Longitude"], errors="coerce")
    return site_info


def parse_file_datetime(file_str):
    """
    Parse the datetime from a file name like:
    "2024-05-24T15_24_05.762Z.mp3"
    and return a tz-aware datetime object in UTC.
    """
    pattern = re.compile(
        r"(?P<date>\d{4}-\d{2}-\d{2}T)"
        r"(?P<hour>\d{2})_(?P<minute>\d{2})_(?P<second>\d{2}\.\d+)"
        r"Z"
    )
    m = pattern.search(file_str)
    if m:
        iso_str = (
            m.group("date")
            + m.group("hour")
            + ":"
            + m.group("minute")
            + ":"
            + m.group("second")
            + "Z"
        )
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt
    return None
