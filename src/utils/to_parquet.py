import pandas as pd
import json

if __name__ == "__main__":

    with open('./assets/index.json', 'r') as f:
        data = json.load(f)

    df = pd.DataFrame(data)

    def extract_hierarchy(path):
        parts = path.split('/')
        if len(parts) < 2:
            return None, None, None
        country = parts[0]
        device = parts[1]
        file_name = parts[-1]
        return country, device, file_name

    df[['country', 'device', 'file']] = df['Path'].apply(lambda x: pd.Series(extract_hierarchy(x)))

    if 'Size' not in df.columns:
        df['Size'] = 0
    if 'ModTime' not in df.columns:
        df['ModTime'] = "N/A"

    df.to_parquet('parquet_dataset', engine='pyarrow', partition_cols=['country', 'device'])
