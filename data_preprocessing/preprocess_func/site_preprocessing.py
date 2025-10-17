import duckdb
import pandas as pd
import requests
import tempfile
import os


def preprocess_sites(parquet_file, username=None, password=None, base_dir = None):

    response = requests.get(parquet_file, auth=(username, password))
    response.raise_for_status()

    with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as tmp:
        tmp.write(response.content)
        tmp_path = tmp.name

    query = """
    SELECT * FROM read_parquet(?)
    WHERE MimeType IN ('image/jpeg', 'image/png')
    """

    result = duckdb.execute(query, (tmp_path,)).df()
    result["deviceID"] = result["Name"].str.split("_").str[2]
    result["picture_type"] = (
        result["Name"].str.split("_").str[3].str.split(".").str[0]
    )

    result["url"] = base_dir + "/" + result["Path"]

    result.to_csv("./image_mapping.csv", index=False)
    os.unlink(tmp_path)