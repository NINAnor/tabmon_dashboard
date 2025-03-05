# TABMON dashboard

Dashboard summarizing the device deployment metadata for the TABMON project.

## Requirements

```bash
uv add pyproject.toml
```

## Listing the device deployment metadata

TABMON data is contained on an S3 bucket. Since it takes a while to access the data through http, we build an `index.json` gathering all the files' metadata. This file is then used by the dashboard

```bash
rclone lsjson nirds3:bencretois-ns8129k-proj-tabmon --recursive > index.json
```

It's also possible to display the pictures per site. For this, copy the TABMON Google Drive folders containing the pictures in the S3 Bucket and map the pictures per device ID using the following script:

```bash
uv run python src/map_pictures.py
```

## Running the app

```bash
uv run streamlit run src/app.py
```