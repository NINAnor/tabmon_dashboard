import duckdb
import pandas as pd
import requests
import tempfile
from io import BytesIO
import os

def preprocess_all_device_stats(parquet_file, username=None, password=None):
    """Get statistics for all devices in the audio dataset."""

    # Download the parquet file with authentication
    response = requests.get(parquet_file, auth=(username, password))
    response.raise_for_status()

    with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as tmp:
        tmp.write(response.content)
        tmp_path = tmp.name

    query = """
    SELECT 
        RIGHT(device, 8) AS device_id,
        device AS full_device_name,
        COUNT(*) AS total_recordings,
        SUM(Size) AS total_size_bytes,
        MIN(ModTime) AS earliest_recording,
        MAX(ModTime) AS latest_recording
    FROM read_parquet(?)
    WHERE MimeType = 'audio/mpeg'
    AND device IS NOT NULL
    AND device != ''
    GROUP BY device
    ORDER BY total_recordings DESC
    """

    result = duckdb.execute(query, (tmp_path,)).df()

    # Add calculated columns
    result['total_size_gb'] = result['total_size_bytes'] / (1024**3)
    result['avg_file_size_mb'] = (result['total_size_bytes'] / result['total_recordings']) / (1024**2)

    # Save to CSV
    result.to_csv("./all_device_stats.csv", index=False)

    os.unlink(tmp_path)

def preprocess_dataset_stats(parquet_file, username=None, password=None):
    """Get statistics for the entire audio dataset."""

    response = requests.get(parquet_file, auth=(username, password))

    query = """
    SELECT COUNT(*) as total_recordings, SUM(Size) as total_size_bytes
    FROM read_parquet(?)
    WHERE MimeType = 'audio/mpeg'
    """

    with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as tmp:
        tmp.write(response.content)
        tmp_path = tmp.name
    
    result = duckdb.execute(query, (tmp_path,)).df()
      
    result.to_csv("./dataset_stats.csv", index=False)

    os.unlink(tmp_path)
