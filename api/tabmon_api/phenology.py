"""Effort-corrected phenology queries.

All rates are detections per recorded hour, computed as
sum(detections) / (sum(recorded_minutes) / 60) over the sites in a group.
"""

from datetime import date

from .config import Settings
from .data import DataStore

LEVELS = {
    "cluster": ("cluster_id", "clusters", "cluster_id", "cluster"),
    "country": ("country", None, None, "country"),
    "site": ("site_id", "sites", "site_id", "site"),
}


def _year_clause(alias: str, year: int | None) -> str:
    return f"AND year({alias}.date) = {int(year)}" if year else ""


def week_start(week: int, year: int | None) -> str:
    """Monday of an ISO week, using a reference year when none is given."""
    return date.fromisocalendar(year or 2025, min(week, 52), 1).isoformat()


def available_years(store: DataStore) -> list[int]:
    rows = store.query("SELECT DISTINCT year(date) AS y FROM effort ORDER BY y")
    return [r["y"] for r in rows]


def _group_meta(store: DataStore, level: str) -> dict[str, dict]:
    if level == "country":
        rows = store.query(
            "SELECT country AS id, country AS label, country, avg(lat) AS lat "
            "FROM sites GROUP BY country"
        )
    elif level == "cluster":
        rows = store.query(
            "SELECT cluster_id AS id, cluster AS label, country, lat FROM clusters"
        )
    else:
        rows = store.query(
            "SELECT site_id AS id, site AS label, country, lat, cluster FROM sites"
        )
    return {r["id"]: r for r in rows}


def _milestones(weeks: list[dict]) -> tuple[int | None, int | None]:
    """Arrival = first week reaching 10% of the peak rate; median = 50% of activity."""
    usable = [w for w in weeks if not w["low_effort"] and w["rate"] is not None]
    peak = max((w["rate"] for w in usable), default=0.0)
    first = next(
        (w["week"] for w in usable if peak > 0 and w["rate"] >= 0.1 * peak), None
    )
    total = sum(w["rate"] for w in usable)
    median = None
    if total > 0:
        acc = 0.0
        for w in usable:
            acc += w["rate"]
            if acc >= total / 2:
                median = w["week"]
                break
    return first, median


def species_phenology(
    store: DataStore, settings: Settings, species: str, level: str, year: int | None
) -> dict:
    col = LEVELS[level][0]
    rows = store.query(
        f"""
        WITH ef AS (
            SELECT e.site_id, weekofyear(e.date) AS week,
                   sum(e.recorded_minutes) AS minutes
            FROM effort e WHERE true {_year_clause("e", year)}
            GROUP BY ALL
        ),
        ph AS (
            SELECT p.site_id, weekofyear(p.date) AS week, sum(p.n_detections) AS n
            FROM phenology p WHERE p.species = ? {_year_clause("p", year)}
            GROUP BY ALL
        )
        SELECT s.{col} AS gid, ef.week, sum(COALESCE(ph.n, 0))::BIGINT AS n,
               sum(ef.minutes) AS minutes
        FROM ef
        JOIN sites s USING (site_id)
        LEFT JOIN ph USING (site_id, week)
        GROUP BY ALL
        """,
        [species],
    )
    meta = _group_meta(store, level)
    by_group: dict[str, dict[int, dict]] = {}
    for r in rows:
        by_group.setdefault(r["gid"], {})[r["week"]] = r

    groups = []
    for gid, weeks_map in by_group.items():
        weeks = []
        for week in range(1, 54):
            r = weeks_map.get(week)
            minutes = float(r["minutes"]) if r else 0.0
            n = int(r["n"]) if r else 0
            weeks.append(
                {
                    "week": week,
                    "n": n,
                    "minutes": minutes,
                    "rate": n / (minutes / 60) if minutes > 0 else None,
                    "low_effort": minutes < settings.min_week_effort_minutes,
                }
            )
        first, median = _milestones(weeks)
        m = meta.get(gid, {})
        groups.append(
            {
                "id": gid,
                "label": m.get("label", gid),
                "country": m.get("country"),
                "lat": m.get("lat"),
                "total": sum(w["n"] for w in weeks),
                "peak_rate": max((w["rate"] or 0) for w in weeks),
                "first_week": first,
                "median_week": median,
                "weeks": weeks,
            }
        )
    groups.sort(key=lambda g: -(g["lat"] or 0))
    # Groups with very few detections are mostly isolated false positives:
    # flag them so the chart can de-emphasise them.
    max_total = max((g["total"] for g in groups), default=0)
    for g in groups:
        g["sparse"] = g["total"] < max(100, 0.01 * max_total)
    return {
        "species": species,
        "level": level,
        "year": year,
        "years": available_years(store),
        "week_starts": [week_start(w, year) for w in range(1, 54)],
        "groups": groups,
    }


def _site_filter(level: str, group_id: str) -> tuple[str, list]:
    col = {"cluster": "cluster_id", "site": "site_id", "country": "country"}[level]
    return f"site_id IN (SELECT site_id FROM sites WHERE {col} = ?)", [group_id]


def place_profile(
    store: DataStore,
    settings: Settings,
    level: str,
    group_id: str,
    year: int | None,
    top: int,
    diel_species: str | None,
) -> dict:
    where, params = _site_filter(level, group_id)

    effort_weeks = store.query(
        f"""
        SELECT weekofyear(e.date) AS week, sum(e.recorded_minutes) AS minutes
        FROM effort e WHERE {where} {_year_clause("e", year)} GROUP BY ALL
        """,
        params,
    )
    minutes_by_week = {r["week"]: float(r["minutes"]) for r in effort_weeks}

    grid = store.query(
        f"""
        WITH ph AS (
            SELECT p.species, weekofyear(p.date) AS week, sum(p.n_detections) AS n
            FROM phenology p WHERE {where} {_year_clause("p", year)}
            GROUP BY ALL
        ),
        top AS (
            SELECT species, sum(n) AS total FROM ph
            GROUP BY species ORDER BY total DESC LIMIT {int(top)}
        )
        SELECT ph.species, ph.week, ph.n, top.total,
               sp.common_en
        FROM ph JOIN top USING (species)
        LEFT JOIN species sp USING (species)
        ORDER BY top.total DESC
        """,
        params,
    )
    species_rows: dict[str, dict] = {}
    for r in grid:
        row = species_rows.setdefault(
            r["species"],
            {
                "species": r["species"],
                "common_en": r["common_en"],
                "total": int(r["total"]),
                "cells": [None] * 53,
            },
        )
        minutes = minutes_by_week.get(r["week"], 0.0)
        if minutes >= settings.min_week_effort_minutes:
            row["cells"][r["week"] - 1] = r["n"] / (minutes / 60)

    diel_params = list(params)
    species_clause = ""
    if diel_species:
        species_clause = "AND p.species = ?"
        diel_params.append(diel_species)
    effort_diel = store.query(
        f"""
        SELECT month(e.date) AS month, e.hour, sum(e.recorded_minutes) AS minutes
        FROM effort e WHERE {where} {_year_clause("e", year)} GROUP BY ALL
        """,
        params,
    )
    det_diel = store.query(
        f"""
        SELECT month(p.date) AS month, p.hour, sum(p.n_detections) AS n
        FROM phenology p WHERE {where} {_year_clause("p", year)} {species_clause}
        GROUP BY ALL
        """,
        diel_params,
    )
    det = {(r["month"], r["hour"]): r["n"] for r in det_diel}
    diel = [[None] * 24 for _ in range(12)]
    for r in effort_diel:
        minutes = float(r["minutes"])
        if minutes >= settings.min_hour_effort_minutes:
            n = det.get((r["month"], r["hour"]), 0)
            diel[r["month"] - 1][r["hour"]] = n / (minutes / 60)

    return {
        "level": level,
        "id": group_id,
        "year": year,
        "years": available_years(store),
        "week_starts": [week_start(w, year) for w in range(1, 54)],
        "effort_weeks": [minutes_by_week.get(w, 0.0) for w in range(1, 54)],
        "species": list(species_rows.values()),
        "diel_species": diel_species,
        "diel": diel,
    }


def species_summary(store: DataStore, settings: Settings, species: str) -> dict | None:
    """Card numbers: share of recorded hours with the species, and a year trend."""
    base = store.one("SELECT * FROM species WHERE species = ?", [species])
    if base is None:
        return None

    # Share of recorded hours with >= 1 detection, per site where the species
    # occurs. The between-site spread is a more honest range than a binomial CI,
    # since hours are not independent.
    per_site = store.query(
        """
        WITH hits AS (
            SELECT site_id, count(*) AS k FROM phenology WHERE species = ? GROUP BY ALL
        ),
        hours AS (
            SELECT site_id, count(*) AS n FROM effort
            WHERE recorded_minutes > 0 AND site_id IN (SELECT site_id FROM hits)
            GROUP BY ALL
        )
        SELECT site_id, hits.k, hours.n FROM hits JOIN hours USING (site_id)
        """,
        [species],
    )
    n = sum(r["n"] for r in per_site)
    k = sum(r["k"] for r in per_site)
    shares = sorted(r["k"] / r["n"] for r in per_site if r["n"] >= 24)
    lo, hi = (
        (_quantile(shares, 0.25), _quantile(shares, 0.75)) if shares else (0.0, 0.0)
    )

    # Only compare a site's week across years when it was recorded in both,
    # so newly added sites do not masquerade as population change.
    yearly = store.query(
        f"""
        WITH occ_sites AS (SELECT DISTINCT site_id FROM phenology WHERE species = ?),
        ef AS (
            SELECT site_id, year(date) AS y, weekofyear(date) AS w,
                   sum(recorded_minutes) AS m
            FROM effort WHERE site_id IN (SELECT site_id FROM occ_sites) GROUP BY ALL
        ),
        ph AS (
            SELECT site_id, year(date) AS y, weekofyear(date) AS w,
                   sum(n_detections) AS n
            FROM phenology WHERE species = ? GROUP BY ALL
        ),
        last_two AS (SELECT DISTINCT y FROM ef ORDER BY y DESC LIMIT 2),
        paired AS (
            SELECT site_id, w FROM ef WHERE y IN (SELECT y FROM last_two)
              AND m >= {settings.min_week_effort_minutes}
            GROUP BY ALL HAVING count(DISTINCT y) = 2
        )
        SELECT ef.y, ef.w, sum(ef.m) AS m, sum(COALESCE(ph.n, 0)) AS n,
               count(DISTINCT ef.site_id) AS n_sites
        FROM ef
        JOIN paired USING (site_id, w)
        LEFT JOIN ph USING (site_id, y, w)
        WHERE ef.y IN (SELECT y FROM last_two)
        GROUP BY ALL
        """,
        [species, species],
    )
    trend = _trend(yearly, settings)

    by_country = store.query(
        """
        SELECT s.country, sum(p.n_detections)::BIGINT AS n,
               count(DISTINCT s.cluster_id) AS n_clusters
        FROM phenology p JOIN sites s USING (site_id)
        WHERE p.species = ? GROUP BY ALL ORDER BY n DESC
        """,
        [species],
    )
    media = store.one("SELECT * FROM species_media WHERE species = ?", [species])

    return {
        **base,
        "hours_recorded": n,
        "hours_with_species": k,
        "hour_share": k / n if n else 0.0,
        "hour_share_range": [lo, hi],
        "n_sites_occupied": len(per_site),
        "trend": trend,
        "by_country": by_country,
        "media": media,
    }


def _quantile(values: list[float], q: float) -> float:
    pos = (len(values) - 1) * q
    i = int(pos)
    j = min(i + 1, len(values) - 1)
    return values[i] + (values[j] - values[i]) * (pos - i)


def _trend(rows: list[dict], settings: Settings) -> dict:
    years = sorted({r["y"] for r in rows})
    if len(years) < 2:
        return {"label": "uncertain", "reason": "only one season recorded"}
    prev, last = years[-2], years[-1]
    data: dict[int, dict[int, tuple[float, int]]] = {prev: {}, last: {}}
    for r in rows:
        if r["y"] in data:
            data[r["y"]][r["w"]] = (float(r["m"]), int(r["n"]))
    common = [w for w in data[last] if w in data[prev]]
    if len(common) < 6:
        return {"label": "uncertain", "reason": "too few comparable weeks"}

    def rate(y: int) -> float:
        m = sum(data[y][w][0] for w in common)
        n = sum(data[y][w][1] for w in common)
        return n / (m / 60) if m else 0.0

    r_prev, r_last = rate(prev), rate(last)
    if r_prev == 0 and r_last == 0:
        return {"label": "uncertain", "reason": "not detected in comparable weeks"}
    ratio = (r_last + 1e-9) / (r_prev + 1e-9)
    label = "rising" if ratio > 1.25 else "falling" if ratio < 0.8 else "steady"
    return {
        "label": label,
        "ratio": ratio,
        "from_year": prev,
        "to_year": last,
        "weeks_compared": len(common),
        "rate_from": r_prev,
        "rate_to": r_last,
    }
