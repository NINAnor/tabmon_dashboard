import pandas as pd

def extract_device_id(record: pd.Series) -> str:
    """Extract short device ID from a site record."""
    full_device_id = record.get("DeviceID", "")
    if "_" in full_device_id:
        return full_device_id.split("_")[-1].strip()
    else:
        return full_device_id[-8:] if len(full_device_id) >= 8 else full_device_id