import requests
import pandas as pd
import pyarrow as pa
from io import BytesIO
import re
from datetime import datetime
import seaborn
import matplotlib

def extract_datetime(filename):
    match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}_\d{2}_\d{2}\.\d{3}Z)', filename)
    if match:
        dt_string = match.group(1)
        dt_string = dt_string.replace('_', ':').replace('Z', '')
        return pd.to_datetime(dt_string)
    return None


def show_stats(parquet_file, BASE_DIR):

    # Open .parquet file and r
    file_obj = BytesIO(parquet_file.content)
    df = pd.read_parquet(file_obj)
    df_audio = df[df['MimeType'] == 'audio/mpeg']