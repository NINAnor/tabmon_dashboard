"""Public endpoints. Never return exact coordinates, site photos or bucket paths."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from .. import media, phenology
from ..auth import current_user
from ..config import Settings, get_settings
from ..data import DataStore
from ..deps import get_store

router = APIRouter(prefix="/api/public", tags=["public"])
clips_router = APIRouter(prefix="/api/clips", tags=["public"])


def _snap(value: float | None, grid: float) -> float | None:
    if value is None:
        return None
    return round(round(value / grid) * grid, 4)


@router.get("/overview")
def overview(store: DataStore = Depends(get_store)):
    def compute():
        devices = (
            store.one(
                "SELECT count(*) AS n, count(*) FILTER (WHERE status = 'Online') AS online "
                "FROM device_status"
            )
            if _has_column(store, "device_status", "status")
            else {"n": 0, "online": 0}
        )
        effort = store.one(
            "SELECT sum(recorded_minutes) / 60 AS hours, min(date) AS since FROM effort"
        )
        species = store.one(
            "SELECT count(*) AS n_species, sum(n_detections)::BIGINT AS n_detections "
            "FROM species"
        )
        geo = store.one(
            "SELECT count(DISTINCT country) AS countries, "
            "count(DISTINCT cluster_id) AS clusters, count(*) AS sites FROM sites"
        )
        return {
            "devices": devices["n"],
            "devices_online": devices["online"],
            "hours_recorded": float(effort["hours"] or 0),
            "recording_since": effort["since"],
            **species,
            **geo,
            "updated_at": store.loaded_at,
        }

    return store.cached(("overview",), compute)


def _has_column(store: DataStore, table: str, column: str) -> bool:
    return bool(
        store.query(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = ? AND column_name = ?",
            [table, column],
        )
    )


@router.get("/network")
def network(store: DataStore = Depends(get_store)):
    """Per-country summary, monthly analysed hours and pipeline numbers."""

    def compute():
        countries = store.query(
            """
            WITH ef AS (
                SELECT s.country, sum(e.recorded_minutes) / 60 AS hours
                FROM effort e JOIN sites s USING (site_id) GROUP BY ALL
            ),
            sp AS (
                SELECT s.country, p.species, sum(p.n_detections) AS n
                FROM phenology p JOIN sites s USING (site_id) GROUP BY ALL
            ),
            top AS (
                SELECT sp.country, count(*) AS n_species,
                       arg_max(COALESCE(x.common_en, sp.species), sp.n) AS top_species
                FROM sp LEFT JOIN species x USING (species) GROUP BY ALL
            ),
            geo AS (
                SELECT country, count(DISTINCT cluster_id) AS n_clusters,
                       count(*) AS n_sites
                FROM sites GROUP BY ALL
            )
            SELECT geo.country, geo.n_clusters, geo.n_sites,
                   COALESCE(ef.hours, 0) AS hours, COALESCE(top.n_species, 0) AS n_species,
                   top.top_species
            FROM geo LEFT JOIN ef USING (country) LEFT JOIN top USING (country)
            ORDER BY hours DESC
            """
        )
        monthly = store.query(
            """
            SELECT s.country, strftime(date_trunc('month', e.date), '%Y-%m') AS month,
                   sum(e.recorded_minutes) / 60 AS hours
            FROM effort e JOIN sites s USING (site_id)
            GROUP BY ALL ORDER BY month
            """
        )
        pipeline = store.one(
            """
            SELECT (SELECT sum(n_detections) FROM species)::BIGINT AS detections,
                   (SELECT sum(n_validated) FROM validations)::BIGINT AS validated,
                   (SELECT count(*) FROM species
                    WHERE threshold_source IN ('calibrated', 'calibrated_low')) AS calibrated,
                   (SELECT count(*) FROM species) AS species
            """
        )
        files = (
            store.one("SELECT total_recordings FROM dataset_stats")
            if _has_column(store, "dataset_stats", "total_recordings")
            else None
        )
        pipeline["files"] = files["total_recordings"] if files else None
        return {"countries": countries, "monthly": monthly, "pipeline": pipeline}

    return store.cached(("network",), compute)


@router.get("/clusters")
def clusters(
    store: DataStore = Depends(get_store), settings: Settings = Depends(get_settings)
):
    def compute():
        rows = store.query(
            """
            WITH ef AS (
                SELECT s.cluster_id, sum(e.recorded_minutes) / 60 AS hours,
                       max(e.date) AS last_recording
                FROM effort e JOIN sites s USING (site_id) GROUP BY ALL
            ),
            ph AS (
                SELECT s.cluster_id, sum(p.n_detections)::BIGINT AS detections,
                       count(DISTINCT p.species) AS n_species
                FROM phenology p JOIN sites s USING (site_id) GROUP BY ALL
            ),
            hab AS (
                SELECT cluster_id, list(DISTINCT habitat) FILTER (WHERE habitat IS NOT NULL)
                    AS habitats
                FROM sites GROUP BY ALL
            )
            SELECT c.cluster_id AS id, c.cluster AS label, c.country, c.lat, c.lon,
                   c.n_sites, COALESCE(ef.hours, 0) AS hours, ef.last_recording,
                   COALESCE(ph.detections, 0) AS detections,
                   COALESCE(ph.n_species, 0) AS n_species, hab.habitats
            FROM clusters c
            LEFT JOIN ef USING (cluster_id)
            LEFT JOIN ph USING (cluster_id)
            LEFT JOIN hab USING (cluster_id)
            ORDER BY c.country, c.cluster
            """
        )
        for r in rows:
            r["lat"] = _snap(r["lat"], settings.public_coord_grid)
            r["lon"] = _snap(r["lon"], settings.public_coord_grid)
        return rows

    return store.cached(("clusters",), compute)


@router.get("/clusters/{cluster_id}/species")
def cluster_species(
    cluster_id: str,
    limit: int = Query(15, le=60),
    store: DataStore = Depends(get_store),
):
    """Most detected species in a landscape, with detection rate and Red List status."""
    return store.cached(
        ("cluster_species", cluster_id, limit),
        lambda: store.query(
            f"""
            WITH g AS (SELECT site_id FROM sites WHERE cluster_id = ?),
            ef AS (
                SELECT sum(recorded_minutes) / 60 AS hours FROM effort
                WHERE site_id IN (SELECT site_id FROM g)
            ),
            ph AS (
                SELECT species, sum(n_detections)::BIGINT AS n FROM phenology
                WHERE site_id IN (SELECT site_id FROM g) GROUP BY ALL
            )
            SELECT ph.species, sp.common_en, ph.n, ph.n / NULLIF(ef.hours, 0) AS rate,
                   eco.iucn, eco.migration,
                   sp.threshold_source IN ('calibrated', 'calibrated_low') AS calibrated
            FROM ph CROSS JOIN ef
            LEFT JOIN species sp USING (species)
            LEFT JOIN species_ecology eco USING (species)
            ORDER BY ph.n DESC LIMIT {int(limit)}
            """,
            [cluster_id],
        ),
    )


@router.get("/species")
def species_list(
    q: str | None = None,
    limit: int = Query(60, le=500),
    store: DataStore = Depends(get_store),
):
    params: list = []
    where = ""
    if q:
        where = "WHERE species ILIKE ? OR common_en ILIKE ?"
        params = [f"%{q}%", f"%{q}%"]
    return store.query(
        f"""
        SELECT species, common_en, common_fr, common_es, common_nl, common_no,
               n_detections, n_sites, n_countries, threshold, threshold_source,
               n_validated, n_correct, precision_at_threshold,
               threshold_source IN ('calibrated', 'calibrated_low') AS calibrated
        FROM species {where}
        ORDER BY calibrated DESC, n_detections DESC LIMIT {int(limit)}
        """,
        params,
    )


@router.get("/species/{species}")
def species_detail(
    species: str,
    store: DataStore = Depends(get_store),
    settings: Settings = Depends(get_settings),
):
    result = store.cached(
        ("species", species),
        lambda: phenology.species_summary(store, settings, species),
    )
    if result is None:
        raise HTTPException(404, "Unknown species")
    return result


@router.get("/phenology/species")
def phenology_species(
    species: str,
    level: Literal["cluster", "country", "site"] = "cluster",
    year: int | None = None,
    user: str | None = Depends(current_user),
    store: DataStore = Depends(get_store),
    settings: Settings = Depends(get_settings),
):
    if level == "site" and user is None:
        raise HTTPException(401, "Site-level phenology requires login")
    return store.cached(
        ("phen", species, level, year),
        lambda: phenology.species_phenology(store, settings, species, level, year),
    )


@router.get("/phenology/place")
def phenology_place(
    id: str,  # noqa: A002
    level: Literal["cluster", "country", "site"] = "cluster",
    year: int | None = None,
    top: int = Query(25, le=80),
    species: str | None = None,
    user: str | None = Depends(current_user),
    store: DataStore = Depends(get_store),
    settings: Settings = Depends(get_settings),
):
    if level == "site" and user is None:
        raise HTTPException(401, "Site-level phenology requires login")
    return store.cached(
        ("place", level, id, year, top, species),
        lambda: phenology.place_profile(store, settings, level, id, year, top, species),
    )


@router.get("/clips")
def clips(
    species: str | None = None,
    cluster_id: str | None = None,
    month: int | None = Query(None, ge=1, le=12),
    limit: int = Query(12, le=50),
    store: DataStore = Depends(get_store),
    settings: Settings = Depends(get_settings),
):
    where, params = ["true"], []
    if species:
        where.append("c.species = ?")
        params.append(species)
    if cluster_id:
        where.append("c.cluster_id = ?")
        params.append(cluster_id)
    if month:
        where.append("month(c.recorded_at) = ?")
        params.append(month)
    return store.query(
        f"""
        SELECT c.clip_id, c.species, sp.common_en, c.cluster_id, cl.cluster,
               c.country, c.recorded_at::DATE AS recorded_on, c.confidence, c.validated,
               least(c.start_s, ?) AS window_start,
               least(c.start_s, ?) + ? AS window_end
        FROM clips c
        LEFT JOIN clusters cl USING (cluster_id)
        LEFT JOIN species sp USING (species)
        WHERE {" AND ".join(where)}
        ORDER BY c.validated DESC, c.confidence DESC
        LIMIT {int(limit)}
        """,
        [
            settings.clip_context_s,
            settings.clip_context_s,
            settings.clip_detection_s,
            *params,
        ],
    )


@clips_router.get("/{clip_id}.mp3")
async def clip_audio(
    clip_id: str,
    store: DataStore = Depends(get_store),
    settings: Settings = Depends(get_settings),
):
    row = store.one("SELECT path, start_s FROM clips WHERE clip_id = ?", [clip_id])
    if row is None:
        raise HTTPException(404, "Unknown clip")
    path = await media.clip_file(settings, clip_id, row["path"], float(row["start_s"]))
    return FileResponse(
        path,
        media_type="audio/mpeg",
        headers={"Cache-Control": "public, max-age=604800, immutable"},
    )
