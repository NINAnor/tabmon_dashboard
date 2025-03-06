# TABMON dashboard

Dashboard summarizing the device deployment metadata for the TABMON project.

## Requirements

Install `uv`: https://docs.astral.sh/uv/getting-started/installation/

```bash
uv sync
```

## Listing the device deployment metadata

TABMON data is contained on an S3 bucket. Since it takes a while to access the data through http, we build an `index.json` gathering all the files' metadata. This file is then used by the dashboard

```bash
rclone lsjson nirds3:bencretois-ns8129k-proj-tabmon --recursive > assets/index.json
```

It's also possible to display the pictures per site. For this, copy the TABMON Google Drive folders containing the pictures in the S3 Bucket and map the pictures per device ID using the following script:

```bash
uv run python src/utils/map_pictures.py
```

## Running the app

```bash
uv run streamlit run src/app.py
```

### (Optional) pre-commit
pre-commit is a set of tools that help you ensure code quality. It runs every time you make a commit.
To install pre-commit hooks run:
```bash
uv run pre-commit install
```

#### Visual studio code
If you are using visual studio code install the recommended extensions

### Development with docker
A basic docker image is already provided, run:
```bash
docker compose watch
```

### Tools installed
- uv
- pre-commit (optional)

#### What is an environment variable? and why should I use them?
Environment variables are variables that are not populated in your code but rather in the environment
that you are running your code. This is extremely useful mainly for two reasons:
- security, you can share your code without sharing your passwords/credentials
- portability, you can avoid using hard-coded values like file-system paths or folder names

you can place your environment variables in a file called `.env`, the `main.py` will read from it. Remember to:
- NEVER commit your `.env`
- Keep a `.env.example` file updated with the variables that the software expects
