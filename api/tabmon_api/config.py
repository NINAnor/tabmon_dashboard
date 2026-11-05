from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Root of the bucket as served by rclone (or a local mirror for development).
    data_url: str = "http://rclone:8081/data"
    # Where build_tables.py writes its output, relative to data_url.
    tables_prefix: str = "data/preprocessed/dashboard"
    # Existing preprocessed CSVs (device status, recording matrix, ...).
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

    clip_cache_dir: Path = Path("/tmp/tabmon-clips")  # noqa: S108
    clip_pre_roll_s: float = 1.0
    clip_length_s: float = 5.0

    species_media_csv: Path = Path(__file__).parent.parent / "data/species_media.csv"


@lru_cache
def get_settings() -> Settings:
    return Settings()
