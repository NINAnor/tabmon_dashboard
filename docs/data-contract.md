# Dashboard data contract

The API is a reader; the
[WP1-data-transfer pipeline](https://github.com/NINAnor/WP1-data-transfer) produces
its inputs in steps 03–06. Step 05 writes the dashboard tables and step 06 writes
pre-cut clips. The pipeline runs daily at 06:00 UTC.

## Locations and requiredness

With the default `DATA_URL`/`data_url` root (`http://rclone:8081/data`), the API reads:

| Input | Location relative to `data_url` | Requiredness |
|---|---|---|
| Dashboard Parquet tables | `data/preprocessed/dashboard/{deployments,effort,phenology,species,clips,photos,validations}.parquet` | All seven required; a missing file prevents loading. |
| Species enrichment | `data/preprocessed/dashboard/species_info.parquet`, `species_ecology.parquet` | Optional; empty typed tables are created when absent. |
| Legacy CSVs | `data/preprocessed/device_status.csv`, `all_device_stats.csv`, `dataset_stats.csv`, `recording_matrix.csv` | Loader attempts each and creates a placeholder table if absent. Team endpoints that query their columns need usable CSVs; some public summaries degrade gracefully. |
| Pre-cut audio | `data/preprocessed/dashboard/clips/v3/{clip_id}.mp3` | Optional per clip; if missing, the API cuts on demand from the original recording. |
| Species media override | `api/data/species_media.csv` (local to the API image, not the bucket) | Optional; an empty table is created if absent. |
| Site photos and original audio | Object paths referenced by `photos.path` and `clips.path`, under bucket `data/` | Needed when those media are requested. |

`tables_prefix` defaults to `data/preprocessed/dashboard`; `legacy_prefix` defaults
to `data/preprocessed`. Both are configurable in `api/tabmon_api/config.py`.

## Dashboard Parquet schemas

Types below are the DuckDB output types created by step 05. Nullable values are
possible where input metadata is absent or a calculation has no result.

### Required tables

| Table | Column | Type | Meaning |
|---|---|---|---|
| `deployments` | `deployment_id` | VARCHAR | Recorder deployment identifier. |
| | `device_id` | VARCHAR | Normalized recorder ID. |
| | `country`, `cluster`, `site` | VARCHAR | Human-readable deployment geography. |
| | `site_id` | VARCHAR | Stable normalized site key. |
| | `cluster_id` | VARCHAR | Stable normalized cluster key. |
| | `lat`, `lon` | DOUBLE | Site coordinates. |
| | `active` | BOOLEAN | Whether the deployment is marked active. |
| | `habitat` | VARCHAR | Recorded habitat description. |
| | `mic_height_cm` | DOUBLE | Microphone height in centimetres. |
| | `mic_direction` | VARCHAR | Microphone direction. |
| | `coord_uncertainty_m` | DOUBLE | Coordinate uncertainty in metres. |
| | `begin_ts`, `end_ts` | TIMESTAMP | Deployment start and end. |
| | `comments` | VARCHAR | Deployment comments. |
| `effort` | `site_id` | VARCHAR | Site key. |
| | `date` | DATE | Local recording date. |
| | `hour` | TINYINT | Local hour (0–23). |
| | `recorded_minutes` | FLOAT | Analysed recording effort, in minutes. |
| `phenology` | `species`, `site_id` | VARCHAR | Scientific species name and site key. |
| | `date` | DATE | Local detection date. |
| | `hour` | TINYINT | Local detection hour (0–23). |
| | `n_detections` | INTEGER | Number of retained detections in the species/site/date/hour group. |
| `species` | `species` | VARCHAR | Scientific species name (join key). |
| | `common_en`, `common_fr`, `common_es`, `common_nl`, `common_no` | VARCHAR | Common names in English, French, Spanish, Dutch and Norwegian. |
| | `n_detections` | BIGINT | Total retained detections. |
| | `n_sites`, `n_countries` | BIGINT | Distinct sites and countries with detections. |
| | `threshold` | DOUBLE | Applied BirdNET confidence threshold. |
| | `threshold_source` | VARCHAR | Calibration status (`calibrated`, `calibrated_low`, `default`, or `unreliable`). |
| | `n_validated`, `n_correct` | BIGINT | Validation count and correct validations. |
| | `precision_at_threshold` | DOUBLE | Validation precision at the selected threshold. |
| `clips` | `clip_id` | VARCHAR | Stable ID used in the pre-cut clip filename. |
| | `species`, `site_id`, `cluster_id`, `country` | VARCHAR | Species and location keys/label. |
| | `path` | VARCHAR | Bucket-relative path to the original recording. |
| | `start_s` | INTEGER | Start of the BirdNET detection window in the recording, seconds. |
| | `confidence` | DOUBLE | BirdNET confidence. |
| | `validated` | BOOLEAN | Whether validation supports the detection. |
| | `recorded_at` | TIMESTAMP | Local recording timestamp. |
| `photos` | `path` | VARCHAR | Bucket-relative photo path. |
| | `name` | VARCHAR | Photo filename. |
| | `device_id` | VARCHAR | Recorder ID associated with the photo. |
| | `picture_type` | VARCHAR | Parsed photo type (defaults to `site`). |
| `validations` | `country`, `species`, `source` | VARCHAR | Country, scientific species name, and validation source (`citizen` or `expert`). |
| | `n_validated`, `n_correct` | BIGINT | Number of valid checks and checks marked correct. |

### Optional enrichment tables

| Table | Column | Type | Meaning |
|---|---|---|---|
| `species_info` | `species` | VARCHAR | Scientific species name (join key). |
| | `wiki_title` | VARCHAR | Wikipedia page title. |
| | `wiki_url` | VARCHAR | Wikipedia page URL. |
| | `extract` | VARCHAR | Short Wikipedia description. |
| | `image_url` | VARCHAR | Attributed Wikimedia thumbnail URL. |
| | `image_page` | VARCHAR | Wikimedia file description page. |
| | `image_artist` | VARCHAR | Image creator/attribution. |
| | `image_license` | VARCHAR | Short licence name. |
| | `image_license_url` | VARCHAR | Licence URL. |
| `species_ecology` | `species` | VARCHAR | Scientific species name (join key). |
| | `iucn` | VARCHAR | IUCN category code. |
| | `migration` | VARCHAR | Migration strategy. |
| | `habitats`, `diet` | VARCHAR[] | Habitat and diet labels. |
| | `lifestyle` | VARCHAR | Primary lifestyle trait. |
| | `trait_source` | VARCHAR | Source for migration/habitat/diet traits. |
| | `peak_hour` | INTEGER | Hour of peak vocal activity. |
| | `night_share` | DOUBLE | Share of vocal activity during 23:00–03:59. |
| | `active_months` | VARCHAR | JSON object of active months by country. |
| `species_media` | `species`, `ml_photo_asset`, `ml_audio_asset`, `photo_credit`, `audio_credit` | VARCHAR | Scientific name key, optional Macaulay Library asset IDs, and media credits. |

`species_info` and `species_ecology` are written by step 05; `species_media` is the
API's local override CSV. The API also creates empty tables with these columns if any
of these optional inputs is missing.

## Legacy CSV schemas

The legacy files are read with DuckDB CSV type inference (`sample_size=-1`), not a
fixed cast. The columns below are those consumed by API queries; keep the listed names
and logical types compatible (especially capitalization). Other input columns can be
present and are passed through where the API returns the full row.

| CSV | Consumed columns (logical type; meaning) |
|---|---|
| `device_status.csv` | `device_name` (text; display name), `short_device` (text; recorder ID), `DeploymentID` (text; deployment join key), `Country` (text; country), `cluster` (text; cluster label), `site_name` (text; site label), `Latitude`, `Longitude` (numbers; coordinates), `status` (text; recorder status), `last_file` (date/time or text; latest upload), `days_since_last` (number; upload age), `total_recordings` (number; recorder count), `Habitat` (text; habitat), `device` (text; full recorder name used to join device statistics). |
| `all_device_stats.csv` | `device_id` (text; recorder ID), `full_device_name` (text; join/display name), `total_recordings` (number; file count), `total_size_gb` (number; data size), `avg_file_size_mb` (number; average file size), `earliest_recording`, `latest_recording` (date/time; recording bounds). |
| `dataset_stats.csv` | `total_recordings` (number; dataset file count), `total_size_bytes` (number; dataset size), plus any additional columns returned by the team dataset endpoint. |
| `recording_matrix.csv` | `Country`, `device` (text; row identifiers), plus date-named columns (counts, converted to integers by the API). |

## Clip format and compatibility

The `clips` row identifies the original MP3 and detection start. A pre-cut clip is
stored as `data/preprocessed/dashboard/clips/v3/{clip_id}.mp3`. It is 5 seconds:
1 second before + the 3-second BirdNET detection window + 1 second after (clipped at
the recording boundary). If that object is missing, the API uses `clips.path` and
`clips.start_s` to cut it on demand; `api/tabmon_api/mp3.py` implements that fallback.

Treat these schemas as a cross-repository contract: changing a column name, type, or
meaning requires coordinated changes in both this API and
[`WP1-data-transfer`](https://github.com/NINAnor/WP1-data-transfer), followed by an
update to this document.
