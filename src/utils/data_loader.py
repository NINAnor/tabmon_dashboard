import pandas as pd
import datetime
import re
from datetime import datetime, timezone
import json
import subprocess


def load_index_parquet(parquet_file):
    """Load the index Parquet file and return a DataFrame."""
    df = pd.read_parquet(parquet_file, engine="pyarrow")
    return df


def process_audio_df(df):
    """Extract hierarchy columns and add default values if missing."""
    df[["country", "device", "file"]] = df["Path"].apply(
        lambda x: pd.Series(extract_hierarchy(x))
    )
    if "Size" not in df.columns:
        df["Size"] = 0
    if "ModTime" not in df.columns:
        df["ModTime"] = "N/A"
    return df


def extract_hierarchy(path):
    parts = path.split("/")
    if len(parts) < 2:
        return None, None, None
    country = parts[0]
    device = parts[1]
    file_name = parts[-1]
    return country, device, file_name


def load_site_info(csv_file, delimiter=","):
    site_info = pd.read_csv(csv_file, delimiter=delimiter)
    # Rename columns 
    site_info = site_info.rename(
        columns={
            "4. Latitude: decimal degree, WGS84 (ex: 64.65746)": "latitude",
            "5. Longitude: decimal degree, WGS84 (ex: 5.37463)": "longitude",
            (
                "8. DeviceID: last digits of the serial number "
                "(ex: RPiID-100000007ft35sm --> 7ft35sm)"
            ): "deviceID",
            "1. Country": "country",
            "Site": "site",
        }
    )
    # Convert coordinates to numeric values
    site_info["latitude"] = pd.to_numeric(site_info["latitude"], errors="coerce")
    site_info["longitude"] = pd.to_numeric(site_info["longitude"], errors="coerce")
    return site_info


def aggregate_file_counts(audio_df):
    device_counts = (
        audio_df.groupby("device").agg(file_count=("file", "count")).reset_index()
    )
    device_counts["short_device"] = device_counts["device"].str[-8:]
    return device_counts

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

