import configparser
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Set DATA_DIR to use a local folder mirroring the bucket layout.
    data_dir: Path | None = None
    s3_bucket: str = "bencretois-ns8129k-proj-tabmon"
    s3_endpoint: str | None = None
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_region: str = "us-east-1"
    rclone_config: Path | None = None

    # Dashboard tables produced by the data-transfer pipeline, relative to the bucket.
    tables_prefix: str = "data/preprocessed/dashboard"
    # Legacy CSVs, relative to the bucket.
    legacy_prefix: str = "data/preprocessed"
    refresh_seconds: int = 3600

    dashboard_username: str = "tabmon"
    dashboard_password: str = ""
    session_secret: str = ""
    session_hours: int = 12
    cookie_secure: bool = False

    # Public coordinates are snapped to this grid (degrees, ~11 km at 0.1).
    public_coord_grid: float = 0.1
    # Weeks with less recording than this (minutes) are flagged as low effort.
    min_week_effort_minutes: float = 120.0
    min_hour_effort_minutes: float = 30.0

    clip_cache_max_entries: int = 500
    # Seconds of audio kept before and after the 3 s BirdNET detection window.
    clip_context_s: float = 1.0
    clip_detection_s: float = 3.0
    # Some objects on NIRD S3 take >30 s on first read.
    upstream_timeout_s: float = 180.0

    species_media_csv: Path = Path(__file__).parent.parent / "data/species_media.csv"

    def model_post_init(self, __context) -> None:
        parser = configparser.ConfigParser(interpolation=None)
        if self.rclone_config is not None:
            try:
                parser.read(self.rclone_config)
            except (OSError, configparser.Error):
                # Missing or invalid credentials are reported without exposing config contents.
                pass

        remote = parser["nirds3"] if parser.has_section("nirds3") else {}
        if not self.s3_access_key_id:
            self.s3_access_key_id = remote.get("access_key_id") or None
        if not self.s3_secret_access_key:
            self.s3_secret_access_key = remote.get("secret_access_key") or None
        if not self.s3_endpoint:
            self.s3_endpoint = remote.get("endpoint") or "https://s3.nird.sigma2.no"


@lru_cache
def get_settings() -> Settings:
    return Settings()
