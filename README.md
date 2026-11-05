# TABMON Dashboard

Dashboard for the [TABMON project](https://www.nina.no/english/TABMON): a public
**sound map** that follows bird phenology from Spain to Arctic Norway, plus a
login-protected **team area** for device monitoring.

## What's inside

| Path | What | Stack |
|---|---|---|
| `web/` | Public site + team area | Next.js, React, Tailwind, MapLibre, d3, wavesurfer.js |
| `api/` | Data API, auth, clip extraction | FastAPI, DuckDB, ffmpeg |
| `preprocessing/` | Builds the aggregated tables the API serves | DuckDB (reads S3 directly) |
| `src/` | Legacy Streamlit dashboard (kept during the transition) | Streamlit |

```
            ┌────────── Traefik ──────────┐
   /  ───►  web (Next.js)                 │
   /api ─►  api (FastAPI + DuckDB) ──► rclone ──► S3 bucket
                                          ▲
   preprocessing (scheduled job) ─────────┘ writes data/preprocessed/dashboard/*.parquet
```

### Public site (`/`)
- **When does it arrive where?** Ridgeline of weekly detection rate for a species, one
  row per landscape (cluster), ordered by latitude. Arrival (10% of peak) and
  mid-season (50% of activity) markers, and a dashed line tracing the wave north.
  The map recolours by mid-season date.
- **What does this place sound like?** Species x week calendar and an "acoustic clock"
  (hour of day x month) for any landscape, with playable example clips.
- **Species cards**: share of recorded hours with the species (with the spread
  across sites), a year-on-year trend, validation status and Macaulay Library media.

### Team area (`/ops`, login required)
Device health map and table (exact coordinates), daily recording activity heatmap,
dataset statistics, site pages with deployment history, field photos and the
site-level soundscape, and validation progress.

## Method notes

- **Effort correction.** Every rate is `detections / recorded hours`. Recording effort
  comes from `index.parquet` (5-minute files) and only counts deployment-days that
  BirdNET has processed, so gaps in recording or analysis never look like absences.
  Weeks with less than 2 h of recording are hatched.
- **Thresholds.** Per-species BirdNET confidence thresholds are calibrated on the
  expert and citizen validations: the lowest threshold reaching 90% precision, or the
  most precise threshold above 70%. Species whose validations never reach 70% are
  excluded. Species without validations use a conservative 0.7.
- **Sparse rows.** Landscapes with very few detections of a species (mostly isolated
  false positives) are drawn faded and left out of the arrival line.
- **Trends** compare the two most recent years using only site-weeks recorded in both.
- **Privacy.** Public endpoints only return cluster centroids snapped to a 0.1° grid,
  never site coordinates, photos or bucket paths. Site-level data needs a login.

## Running locally

Requirements: Docker, an rclone remote `nirds3` in `~/.config/rclone/rclone.conf`.

```bash
cp .env.example .env            # set DASHBOARD_PASSWORD and SESSION_SECRET
docker compose run --rm preprocessing   # once, then on a schedule (e.g. nightly cron)
docker compose up -d --build
```

Open http://localhost:8050. The legacy Streamlit app can still be started with
`docker compose --profile legacy up streamlit` (http://localhost:8501).

### Development without Docker

```bash
# Build the tables into a local folder that mirrors the bucket layout
cd preprocessing
S3_ACCESS_KEY_ID=... S3_SECRET_ACCESS_KEY=... uv run build_tables.py \
  --source s3://bencretois-ns8129k-proj-tabmon \
  --out ../.mirror/data/preprocessed/dashboard --names birdnet_multilingual.csv
# (also copy data/preprocessed/*.csv from the bucket into ../.mirror/data/preprocessed/)

cd ../api
DATA_URL=../.mirror SESSION_SECRET=dev DASHBOARD_PASSWORD=dev uv run uvicorn tabmon_api.main:app --reload
uv run pytest

cd ../web
npm install
npm run dev                      # proxies /api to http://localhost:8000
```

## Adding species media

`api/data/species_media.csv` maps species to Macaulay Library asset IDs:

```csv
species,ml_photo_asset,ml_audio_asset,photo_credit,audio_credit
Cuculus canorus,123456789,,Photographer Name,
```

Photos are embedded from Macaulay Library (not re-hosted), with credit and a link back.

## Acknowledgment

Developed by [Benjamin Cretois](mailto:benjamin.cretois@nina.no) and
[Francesco Frassinelli](mailto:francesco.frassinelli@nina.no).
