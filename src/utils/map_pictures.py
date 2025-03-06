import json
import re
import pandas as pd
import subprocess
from urllib.parse import quote, unquote
import yaml

def get_encoded_title(title):
    if " " in title:
        return quote(title, safe="/")
    elif "%25" in title:
        return unquote(title)
    else:
        return title

def generate_pictures_mapping(s3_pictures_path, output_csv, base_url):
    """
    Generates a CSV mapping for pictures stored in the S3 bucket.
    """
    # Build the rclone command
    cmd = f"rclone lsjson {s3_pictures_path} --recursive"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("Error running rclone:", result.stderr)
        return
    
    data = json.loads(result.stdout)
    records = []
    
    # Updated regex: allows optional whitespace and supports .jpg or .jpeg
    pattern = re.compile(r".*_(?P<deviceid>\s*[0-9a-f]{8})\s*_(?P<pic_type>\w+)\.jpe?g", re.IGNORECASE)
    
    for item in data:
        # Get the file path from rclone output
        title = item.get("Path", "")
        m = pattern.match(title)
        if m:
            device_id = m.group("deviceid").strip()
            pic_type = m.group("pic_type")
            # Use the helper to get the properly encoded title.
            encoded_title = get_encoded_title(title)
            url = f"{base_url}/{encoded_title}"
            records.append({
                "deviceID": device_id,
                "picture_type": pic_type,
                "filename": title,
                "url": url
            })
    
    # Save the mapping to a CSV file
    df_mapping = pd.DataFrame(records)
    df_mapping.to_csv(output_csv, index=False)
    print(f"Mapping saved to {output_csv}")

if __name__ == "__main__":

    with open("./config.yaml") as f:
        cfg = yaml.load(f, Loader=yaml.FullLoader)

    s3_pictures_path = cfg["S3_PICTURES_PATH"]
    output_csv = "./assets/pictures_mapping.csv"
    base_url = cfg["PICTURES_URL"]
    generate_pictures_mapping(s3_pictures_path, output_csv, base_url)
