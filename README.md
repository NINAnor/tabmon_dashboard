# TABMON Dashboard

Public dashboard and team area for [TABMON](https://www.nina.no/english/TABMON), a
transnational passive acoustic monitoring network for European birds, from Spain to
Arctic Norway. The network continues from October 2026 within
[BEAGLE](https://cordis.europa.eu/project/id/101288886) (Horizon Europe).

| Path | What | Stack |
|---|---|---|
| `web/` | Public site (Network · Sites · Species · Project) and team area (`/ops`) | Next.js, React, Tailwind, MapLibre, d3, wavesurfer.js |
| `api/` | Data API, team login, and clip serving | FastAPI, DuckDB, ffmpeg |

```
                 ┌──── Traefik ────┐
     /      ──►  web (Next.js)     │
     /api   ──►  api (FastAPI) ────┼──► rclone (internal) ──► S3 bucket
                                   │
     data_transfer (daily 06:00 UTC; steps 05/06) ──► data/preprocessed/dashboard/
```

## Public site

- **Network**: live totals, cluster map, per-country summary, monthly hours analysed,
  and how the pipeline works.
- **Sites**: per-cluster species × week calendar, acoustic clock (hour × month),
  most-heard species and example clips.
- **Species**: photo and description (Wikipedia/Wikimedia Commons), IUCN status,
  migration strategy and diet, a "how to read the chart" text, the latitude-ordered
  phenology ridgeline with a time-lapse map, the spring and autumn waves (onset moving
  north, end of the vocal season), the daily vocal rhythm, validation status and 5-second
  clips (3 s BirdNET window + 1 s each side) with spectrograms.
- **Project**: mission, TABMON → BEAGLE, the Listening Lab, partners, publications.

Every "Help identify birds" link deep-links into the
[Listening Lab](https://tabmon-listening-lab.nina.no) with the country, cluster and
species preselected.

## Method notes

These table-building methods are implemented by `data_transfer` in `05_dashboard/`.

- **Effort correction.** Rates are detections per recorded hour. Effort comes from
  `index.parquet` (5-minute files) and only counts deployment-days BirdNET has processed,
  so gaps in recording or analysis never look like absences.
- **Thresholds.** Per-species BirdNET thresholds are calibrated on expert and citizen
  validations (lowest threshold reaching 90% precision, else the best above 70%).
  Species never reaching 70% are excluded; species with fewer than 20 validations use 0.7
  and are flagged "not yet validated" on the site.
- **Seasons and waves.** Per cluster, onset / end are the weeks reaching 10% / 90% of
  the season's activity (weeks below 10% of the peak and isolated bursts are ignored; the
  year starts at the species' quietest week). Spring and autumn waves are fitted against
  latitude for migrants only, using onsets in Feb–Jun and ends in May–Nov.
- **Sparse rows.** Clusters with very few detections of a species are drawn faded and
  left out of the waves.
- **Trends** compare the two latest years on site-weeks recorded in both.
- **Privacy.** Public endpoints only return cluster centroids snapped to a 0.1° grid,
  never site coordinates, photos or bucket paths. Site-level data needs a login.

Trait data: Storchová & Hořák (2018) and AVONET (Tobias et al. 2022); see
the references used by `05_dashboard/` in
[WP1-data-transfer](https://github.com/NINAnor/WP1-data-transfer).

Dashboard data is produced by the
[data_transfer pipeline](https://github.com/NINAnor/WP1-data-transfer), which runs daily
at 06:00 UTC (step 05 builds dashboard tables; step 06 pre-cuts clips). See the
[data contract](docs/data-contract.md) for the API input schemas and compatibility
requirements.

## Running

Requirements: Docker (rootless socket path is set in `docker-compose.yml`), an rclone
remote `nirds3` in `~/.config/rclone/rclone.conf`.

```bash
cp .env.example .env  # set dashboard password and session secret
docker compose up -d --build
```

Open http://localhost:8058 (Traefik dashboard on :8088).

### Development

```bash
cd api && DATA_URL=/path/to/bucket-mirror SESSION_SECRET=dev DASHBOARD_PASSWORD=dev \
  uv run uvicorn tabmon_api.main:app --reload       # tests: uv run pytest
cd web && npm install && npm run dev                # proxies /api to localhost:8000
```

`DATA_URL` can be a local folder that mirrors the bucket layout
(`data/preprocessed/dashboard/*.parquet`, `data/preprocessed/*.csv`).

## Species media

Photos and descriptions come from Wikipedia/Wikimedia Commons with attribution. To use a
Macaulay Library photo instead, add its asset ID to `api/data/species_media.csv`.

## Acknowledgment

Developed by [Benjamin Cretois](mailto:benjamin.cretois@nina.no) and
[Francesco Frassinelli](mailto:francesco.frassinelli@nina.no).
