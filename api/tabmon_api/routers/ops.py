"""Team-only endpoints: exact locations, device health, site photos."""

import hashlib

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

from .. import auth, media
from ..config import Settings, get_settings
from ..data import DataStore
from ..deps import get_store

router = APIRouter(
    prefix="/api/ops", tags=["ops"], dependencies=[Depends(auth.require_user)]
)
auth_router = APIRouter(prefix="/api/auth", tags=["auth"])


class Login(BaseModel):
    username: str
    password: str


@auth_router.post("/login")
def login(body: Login, response: Response, settings: Settings = Depends(get_settings)):
    if not auth.check_credentials(body.username, body.password, settings):
        raise HTTPException(401, "Invalid credentials")
    auth.issue(response, body.username, settings)
    return {"user": body.username}


@auth_router.post("/logout")
def logout(response: Response):
    auth.clear(response)
    return {"ok": True}


@auth_router.get("/me")
def me(user: str | None = Depends(auth.current_user)):
    return {"user": user}


@router.get("/devices")
def devices(store: DataStore = Depends(get_store)):
    return store.query(
        """
        SELECT ds.device_name AS device, ds.short_device AS device_id,
               ds.DeploymentID AS deployment_id, ds.Country AS country,
               ds.cluster, ds.site_name AS site, d.site_id, d.cluster_id,
               ds.Latitude AS lat, ds.Longitude AS lon, ds.status,
               CAST(ds.last_file AS VARCHAR) AS last_file,
               CASE WHEN isfinite(TRY_CAST(ds.days_since_last AS DOUBLE))
                    THEN TRY_CAST(ds.days_since_last AS DOUBLE) END AS days_since_last,
               TRY_CAST(ds.total_recordings AS BIGINT) AS total_recordings,
               ds.Habitat AS habitat
        FROM device_status ds
        LEFT JOIN deployments d ON d.deployment_id = ds.DeploymentID
        ORDER BY ds.Country, ds.cluster, ds.site_name
        """
    )


@router.get("/activity")
def activity(store: DataStore = Depends(get_store)):
    def compute():
        with store.cursor() as cur:
            rel = cur.execute("SELECT * FROM recording_matrix")
            cols = [d[0] for d in rel.description]
            rows = rel.fetchall()
        if "device" not in cols:
            return {"dates": [], "rows": []}
        dates = [c for c in cols if c not in ("Country", "device")]
        meta = {
            r["device"]: r
            for r in store.query(
                "SELECT device, cluster, site_name AS site FROM device_status"
            )
        }
        out = []
        for row in rows:
            rec = dict(zip(cols, row, strict=True))
            m = meta.get(rec["device"], {})
            out.append(
                {
                    "country": rec.get("Country"),
                    "device": rec["device"],
                    "device_id": rec["device"][-8:],
                    "cluster": m.get("cluster"),
                    "site": m.get("site"),
                    "values": [int(rec[d] or 0) for d in dates],
                }
            )
        out.sort(
            key=lambda r: (r["country"] or "", r["cluster"] or "", r["site"] or "")
        )
        return {"dates": dates, "rows": out}

    return store.cached(("activity",), compute)


@router.get("/dataset")
def dataset(store: DataStore = Depends(get_store)):
    total = store.one("SELECT * FROM dataset_stats") or {}
    per_device = store.query(
        """
        SELECT s.device_id, s.full_device_name AS device,
               s.total_recordings, s.total_size_gb, s.avg_file_size_mb,
               s.earliest_recording, s.latest_recording,
               ds.Country AS country, ds.cluster, ds.site_name AS site
        FROM device_stats s
        LEFT JOIN device_status ds ON ds.device = s.full_device_name
        ORDER BY s.total_recordings DESC
        """
    )
    effort = store.query(
        """
        SELECT s.country, date_trunc('month', e.date) AS month,
               sum(e.recorded_minutes) / 60 AS hours
        FROM effort e JOIN sites s USING (site_id)
        GROUP BY ALL ORDER BY month
        """
    )
    return {"total": total, "devices": per_device, "monthly_hours": effort}


@router.get("/sites")
def sites(store: DataStore = Depends(get_store)):
    return store.query(
        """
        SELECT s.site_id, s.site, s.cluster, s.cluster_id, s.country, s.lat, s.lon,
               s.active, s.habitat, len(s.deployment_ids) AS n_deployments,
               (SELECT count(*) FROM photos p WHERE list_contains(s.device_ids, p.device_id))
                   AS n_photos
        FROM sites s ORDER BY s.country, s.cluster, s.site
        """
    )


@router.get("/sites/{site_id}")
def site_detail(site_id: str, store: DataStore = Depends(get_store)):
    site = store.one("SELECT * FROM sites WHERE site_id = ?", [site_id])
    if site is None:
        raise HTTPException(404, "Unknown site")
    deployments = store.query(
        "SELECT * EXCLUDE (site_id, cluster_id) FROM deployments WHERE site_id = ? "
        "ORDER BY begin_ts",
        [site_id],
    )
    photos = store.query(
        "SELECT path, device_id, picture_type FROM photos "
        "WHERE list_contains(?, device_id) ORDER BY device_id, picture_type",
        [site["device_ids"]],
    )
    for p in photos:
        p["photo_id"] = _photo_id(p.pop("path"))
    effort = store.one(
        "SELECT sum(recorded_minutes) / 60 AS hours, min(date) AS first, "
        "max(date) AS last FROM effort WHERE site_id = ?",
        [site_id],
    )
    return {**site, "deployments": deployments, "photos": photos, "effort": effort}


def _photo_id(path: str) -> str:
    return hashlib.sha256(path.encode()).hexdigest()[:20]


@router.get("/photos/{photo_id}")
async def photo(
    photo_id: str,
    store: DataStore = Depends(get_store),
    settings: Settings = Depends(get_settings),
):
    paths = store.cached(
        ("photo_paths",),
        lambda: {
            _photo_id(r["path"]): r["path"]
            for r in store.query("SELECT path FROM photos")
        },
    )
    path = paths.get(photo_id)
    if path is None:
        raise HTTPException(404, "Unknown photo")
    content, ctype = await media.fetch_bytes(settings, f"data/{path}")
    return Response(
        content, media_type=ctype, headers={"Cache-Control": "private, max-age=86400"}
    )


@router.get("/validations")
def validations(store: DataStore = Depends(get_store)):
    by_country = store.query(
        """
        SELECT country, source, sum(n_validated)::BIGINT AS n_validated,
               sum(n_correct)::BIGINT AS n_correct, count(DISTINCT species) AS n_species
        FROM validations GROUP BY ALL ORDER BY country, source
        """
    )
    by_species = store.query(
        """
        SELECT v.species, sp.common_en, sum(v.n_validated)::BIGINT AS n_validated,
               sum(v.n_correct)::BIGINT AS n_correct,
               sp.threshold, sp.threshold_source
        FROM validations v LEFT JOIN species sp USING (species)
        GROUP BY ALL ORDER BY n_validated DESC LIMIT 100
        """
    )
    return {"by_country": by_country, "by_species": by_species}
