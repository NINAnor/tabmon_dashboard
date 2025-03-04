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

## Running the app

```bash
uv run streamlit run src/app.py
```