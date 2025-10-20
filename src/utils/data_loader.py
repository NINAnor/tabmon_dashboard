import pandas as pd


def load_site_info(csv_file, delimiter=","):
    """Load site information from CSV file."""
    site_info = pd.read_csv(csv_file, delimiter=delimiter)

    # Convert coordinates to numeric values
    site_info["Latitude"] = pd.to_numeric(site_info["Latitude"], errors="coerce")
    site_info["Longitude"] = pd.to_numeric(site_info["Longitude"], errors="coerce")
    return site_info
