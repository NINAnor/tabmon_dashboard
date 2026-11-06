"""In-memory DuckDB store, loaded from the bucket and refreshed periodically."""

import asyncio
import logging
import threading
import time
from contextlib import contextmanager

import duckdb

from .config import Settings

log = logging.getLogger("tabmon.data")

PARQUET_TABLES = (
    "deployments",
    "effort",
    "phenology",
    "species",
    "clips",
    "photos",
    "validations",
)
LEGACY_CSV = {
    "device_status": "device_status.csv",
    "device_stats": "all_device_stats.csv",
    "dataset_stats": "dataset_stats.csv",
    "recording_matrix": "recording_matrix.csv",
}


class DataStore:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._con: duckdb.DuckDBPyConnection | None = None
        self._lock = threading.Lock()
        self.loaded_at: float | None = None
        self._cache: dict = {}

    def _url(self, prefix: str, name: str) -> str:
        return f"{self.settings.data_url.rstrip('/')}/{prefix.strip('/')}/{name}"

    def _load(self) -> duckdb.DuckDBPyConnection:
        con = duckdb.connect()
        con.execute("SET TimeZone = 'UTC'")
        if self.settings.data_url.startswith("http"):
            con.execute("INSTALL httpfs; LOAD httpfs;")

        for table in PARQUET_TABLES:
            url = self._url(self.settings.tables_prefix, f"{table}.parquet")
            con.execute(f"CREATE TABLE {table} AS SELECT * FROM read_parquet('{url}')")

        # Optional enrichment produced by the data-transfer pipeline.
        url = self._url(self.settings.tables_prefix, "species_info.parquet")
        try:
            con.execute(
                f"CREATE TABLE species_info AS SELECT * FROM read_parquet('{url}')"
            )
        except duckdb.Error:
            log.warning("species_info.parquet not available")
            con.execute(
                "CREATE TABLE species_info (species VARCHAR, wiki_title VARCHAR, "
                "wiki_url VARCHAR, extract VARCHAR, image_url VARCHAR, "
                "image_page VARCHAR, image_artist VARCHAR, image_license VARCHAR, "
                "image_license_url VARCHAR)"
            )

        url = self._url(self.settings.tables_prefix, "species_ecology.parquet")
        try:
            con.execute(
                f"CREATE TABLE species_ecology AS SELECT * FROM read_parquet('{url}')"
            )
        except duckdb.Error:
            log.warning("species_ecology.parquet not available")
            con.execute(
                "CREATE TABLE species_ecology (species VARCHAR, iucn VARCHAR, "
                "migration VARCHAR, habitats VARCHAR[], diet VARCHAR[], "
                "lifestyle VARCHAR, trait_source VARCHAR, peak_hour INTEGER, "
                "night_share DOUBLE, active_months VARCHAR)"
            )

        for table, name in LEGACY_CSV.items():
            url = self._url(self.settings.legacy_prefix, name)
            try:
                con.execute(
                    f"CREATE TABLE {table} AS SELECT * FROM "
                    f"read_csv('{url}', header = true, sample_size = -1)"
                )
            except duckdb.Error as exc:
                log.warning("could not load %s: %s", url, exc)
                con.execute(f"CREATE TABLE {table} (missing BOOLEAN)")

        media = self.settings.species_media_csv
        if media.exists():
            con.execute(
                f"CREATE TABLE species_media AS SELECT * FROM "
                f"read_csv('{media}', header = true, all_varchar = true)"
            )
        else:
            con.execute(
                "CREATE TABLE species_media (species VARCHAR, ml_photo_asset VARCHAR, "
                "ml_audio_asset VARCHAR, photo_credit VARCHAR, audio_credit VARCHAR)"
            )

        # One row per site (a site can have several deployments over time).
        con.execute(
            """
            CREATE TABLE sites AS
            SELECT site_id, any_value(site) AS site, any_value(cluster) AS cluster,
                   any_value(cluster_id) AS cluster_id, any_value(country) AS country,
                   avg(lat) AS lat, avg(lon) AS lon,
                   bool_or(active) AS active, any_value(habitat) AS habitat,
                   list(DISTINCT deployment_id) AS deployment_ids,
                   list(DISTINCT device_id) AS device_ids
            FROM deployments
            WHERE site_id IS NOT NULL
            GROUP BY site_id
            """
        )
        con.execute(
            """
            CREATE TABLE clusters AS
            SELECT cluster_id, any_value(cluster) AS cluster,
                   any_value(country) AS country, avg(lat) AS lat, avg(lon) AS lon,
                   count(*) AS n_sites
            FROM sites GROUP BY cluster_id
            """
        )
        return con

    def refresh(self) -> None:
        started = time.monotonic()
        con = self._load()
        with self._lock:
            old, self._con = self._con, con
            self.loaded_at = time.time()
            self._cache = {}
        if old is not None:
            old.close()
        log.info("data loaded in %.1fs", time.monotonic() - started)

    async def refresh_forever(self) -> None:
        """Load now, then reload periodically. Retry quickly until the first load works."""
        while True:
            try:
                await asyncio.to_thread(self.refresh)
                delay = self.settings.refresh_seconds
            except Exception:
                log.exception("data refresh failed, keeping previous data")
                delay = self.settings.refresh_seconds if self.loaded_at else 60
            await asyncio.sleep(delay)

    @contextmanager
    def cursor(self):
        with self._lock:
            if self._con is None:
                raise RuntimeError("data not loaded")
            cur = self._con.cursor()
        try:
            yield cur
        finally:
            cur.close()

    def cached(self, key: tuple, compute):
        """Memoise a result until the next data refresh."""
        if key in self._cache:
            return self._cache[key]
        value = compute()
        if len(self._cache) > 2000:
            self._cache.clear()
        self._cache[key] = value
        return value

    def query(self, sql: str, params: list | None = None) -> list[dict]:
        with self.cursor() as cur:
            rel = cur.execute(sql, params or [])
            cols = [d[0] for d in rel.description]
            return [dict(zip(cols, row, strict=True)) for row in rel.fetchall()]

    def one(self, sql: str, params: list | None = None) -> dict | None:
        rows = self.query(sql, params)
        return rows[0] if rows else None
