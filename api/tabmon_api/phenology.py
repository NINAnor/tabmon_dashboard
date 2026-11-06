"""Effort-corrected phenology queries.

All rates are detections per recorded hour, computed as
sum(detections) / (sum(recorded_minutes) / 60) over the sites in a group.
"""

import math
from datetime import date

from . import ecology
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


def season_start(groups: list[dict]) -> int:
    """Find the quietest week in the normalized species-wide vocal profile."""
    profile = [0.0] * 53
    counts = [0] * 53
    for group in groups:
        if group.get("sparse"):
            continue
        usable = [
            w for w in group["weeks"] if not w["low_effort"] and w["rate"] is not None
        ]
        peak = max((w["rate"] for w in usable), default=0.0)
        if peak <= 0:
            continue
        for week in usable:
            idx = week["week"] - 1
            profile[idx] += week["rate"] / peak
            counts[idx] += 1

    averaged = [profile[i] / counts[i] if counts[i] else None for i in range(53)]
    smoothed = []
    for i in range(53):
        neighbors = [
            averaged[(i + offset) % 53]
            for offset in (-1, 0, 1)
            if averaged[(i + offset) % 53] is not None
        ]
        smoothed.append(sum(neighbors) / len(neighbors) if neighbors else None)
    available = [i for i, value in enumerate(smoothed) if value is not None]
    if not available:
        return 1
    return min(available, key=smoothed.__getitem__) + 1


def season_markers(weeks: list[dict], start: int) -> dict:
    """Return activity onset, peak, and end in a year rotated to ``start``.

    The season is the continuous block of activity around the peak week: weeks
    below 10% of the peak are background, and the block may bridge gaps of up to
    ``MAX_SEASON_GAP`` weeks (quiet or unrecorded). Isolated bursts of false
    positives months away from the peak are therefore ignored. Onset and end are
    the weeks reaching 10% and 90% of the block's cumulative activity.
    """
    rotated = [weeks[(start - 1 + offset) % 53] for offset in range(53)]
    usable = [w for w in rotated if not w["low_effort"] and w["rate"] is not None]
    peak_rate = max((w["rate"] for w in usable), default=0.0)
    if peak_rate <= 0:
        return {"onset_week": None, "peak_week": None, "end_week": None}

    def signal(w: dict) -> float:
        if w["low_effort"] or w["rate"] is None:
            return 0.0
        return w["rate"] if w["rate"] >= BACKGROUND_FRACTION * peak_rate else 0.0

    values = [signal(w) for w in rotated]
    peak_idx = max(range(53), key=lambda i: values[i])

    def extend(step: int) -> int:
        edge, gap, i = peak_idx, 0, peak_idx + step
        while 0 <= i < 53:
            if values[i] > 0:
                edge, gap = i, 0
            else:
                gap += 1
                if gap > MAX_SEASON_GAP:
                    break
            i += step
        return edge

    lo, hi = extend(-1), extend(1)
    block = range(lo, hi + 1)
    total = sum(values[i] for i in block)
    accumulated = 0.0
    onset = end = None
    for i in block:
        accumulated += values[i]
        if onset is None and accumulated >= 0.1 * total:
            onset = rotated[i]["week"]
        if end is None and accumulated >= 0.9 * total:
            end = rotated[i]["week"]
    return {
        "onset_week": onset,
        "peak_week": rotated[peak_idx]["week"],
        "end_week": end,
    }


def _relative_day(week: int, start: int) -> float:
    return ((week - start) % 53) * 7 + 3.5


# Calendar windows (ISO weeks) for each wave: onsets in Feb-Jun, ends in May-Nov.
# Clusters whose season starts or ends outside them, typically southern wintering
# populations active Oct-Mar, are left out of the fits.
WAVE_WINDOWS = {"onset_week": (5, 26), "end_week": (18, 48)}


def _wave_points(groups: list[dict], marker: str, start: int) -> list[dict]:
    lo, hi = WAVE_WINDOWS[marker]
    return [
        {
            "id": group["id"],
            "lat": group["lat"],
            "day": _relative_day(group[marker], start),
            "weight": math.sqrt(group["total"]),
        }
        for group in groups
        if not group.get("sparse")
        and group.get(marker) is not None
        and lo <= group[marker] <= hi
        and group.get("lat") is not None
        and group["total"] > 0
    ]


def fit_wave(points: list[dict], kind: str) -> dict:
    """Fit relative timing against latitude using sqrt(total) weighted least squares."""
    result = {
        "n": len(points),
        "clear": False,
        "points": [
            {"id": p.get("id"), "lat": p["lat"], "day": p["day"]} for p in points
        ],
    }
    if len(points) < 5:
        result["reason"] = "too few clusters with enough detections"
        return result

    sw = sum(p["weight"] for p in points)
    mx = sum(p["lat"] * p["weight"] for p in points) / sw
    my = sum(p["day"] * p["weight"] for p in points) / sw
    sxx = sum(p["weight"] * (p["lat"] - mx) ** 2 for p in points)
    sxy = sum(p["weight"] * (p["lat"] - mx) * (p["day"] - my) for p in points)
    syy = sum(p["weight"] * (p["day"] - my) ** 2 for p in points)
    if sxx == 0:
        result["reason"] = "no spread in latitude or timing"
        return result

    slope = sxy / sxx
    r2 = sxy * sxy / (sxx * syy) if syy > 0 else 0.0
    result.update(
        {
            "days_per_degree": slope,
            "intercept": my - slope * mx,
            "r2": r2,
        }
    )
    expected_sign = 1 if kind == "spring" else -1
    if expected_sign * slope > 0.2 and r2 >= 0.3:
        result["clear"] = True
        if kind == "spring":
            result["km_per_day"] = KM_PER_DEGREE_LAT / slope
    else:
        result["reason"] = (
            "no clear north-south timing"
            if r2 < 0.3
            else "season does not move north"
            if kind == "spring"
            else "season does not move south"
        )
    return result


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
        m = meta.get(gid, {})
        groups.append(
            {
                "id": gid,
                "label": m.get("label", gid),
                "country": m.get("country"),
                "lat": m.get("lat"),
                "total": sum(w["n"] for w in weeks),
                "peak_rate": max((w["rate"] or 0) for w in weeks),
                "weeks": weeks,
            }
        )
    groups.sort(key=lambda g: -(g["lat"] or 0))
    # Groups with very few detections are mostly isolated false positives:
    # flag them so the chart can de-emphasise them.
    max_total = max((g["total"] for g in groups), default=0)
    for g in groups:
        g["sparse"] = g["total"] < max(100, 0.01 * max_total)
    start = season_start(groups)
    for group in groups:
        group.update(season_markers(group["weeks"], start))

    ecology_row = store.one(
        "SELECT migration FROM species_ecology WHERE species = ?", [species]
    )
    migration_kind = ecology_row["migration"] if ecology_row else None
    show_waves = migration_kind in {"long_distance", "short_distance", "migrant"}
    migration_reason = {
        "resident": "resident species",
        "partial": "partial migrant",
    }.get(migration_kind)
    if not show_waves and migration_reason is None:
        migration_reason = "migration strategy unknown"
    migration = {
        "kind": migration_kind,
        "show_waves": show_waves,
        "reason": None if show_waves else migration_reason,
        "spring": fit_wave(_wave_points(groups, "onset_week", start), "spring"),
        "autumn": fit_wave(_wave_points(groups, "end_week", start), "autumn"),
    }
    return {
        "species": species,
        "season_start_week": start,
        "migration": migration,
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


def species_diel(
    store: DataStore, settings: Settings, species: str, year: int | None
) -> dict:
    """Hourly detection rate (local time) per country and overall, plus a month x hour
    grid, at the sites where the species occurs."""
    rows = store.query(
        f"""
        WITH occ AS (SELECT DISTINCT site_id FROM phenology WHERE species = ?),
        ef AS (
            SELECT s.country, month(e.date) AS month, e.hour,
                   sum(e.recorded_minutes) AS minutes
            FROM effort e JOIN sites s USING (site_id)
            WHERE e.site_id IN (SELECT site_id FROM occ) {_year_clause("e", year)}
            GROUP BY ALL
        ),
        ph AS (
            SELECT s.country, month(p.date) AS month, p.hour, sum(p.n_detections) AS n
            FROM phenology p JOIN sites s USING (site_id)
            WHERE p.species = ? {_year_clause("p", year)}
            GROUP BY ALL
        )
        SELECT ef.country, ef.month, ef.hour, ef.minutes, COALESCE(ph.n, 0) AS n
        FROM ef LEFT JOIN ph USING (country, month, hour)
        """,
        [species, species],
    )

    def profile(filtered: list[dict]) -> list[float | None]:
        n = [0.0] * 24
        m = [0.0] * 24
        for r in filtered:
            n[r["hour"]] += r["n"]
            m[r["hour"]] += r["minutes"]
        return [
            n[h] / (m[h] / 60) if m[h] >= settings.min_hour_effort_minutes else None
            for h in range(24)
        ]

    overall = profile(rows)
    countries = {}
    for country in sorted({r["country"] for r in rows}):
        sub = [r for r in rows if r["country"] == country]
        if sum(r["n"] for r in sub) >= 50:  # skip countries with only stray detections
            countries[country] = profile(sub)

    grid = [[None] * 24 for _ in range(12)]
    cells: dict[tuple[int, int], list[float]] = {}
    for r in rows:
        acc = cells.setdefault((r["month"], r["hour"]), [0.0, 0.0])
        acc[0] += r["n"]
        acc[1] += r["minutes"]
    for (month, hour), (n, minutes) in cells.items():
        if minutes >= settings.min_hour_effort_minutes:
            grid[month - 1][hour] = n / (minutes / 60)

    valid = [(h, v) for h, v in enumerate(overall) if v is not None]
    total = sum(v for _, v in valid)
    night = sum(v for h, v in valid if h in (23, 0, 1, 2, 3))
    return {
        "species": species,
        "year": year,
        "overall": overall,
        "countries": countries,
        "grid": grid,
        "peak_hour": max(valid, key=lambda x: x[1])[0] if total > 0 else None,
        "night_share": night / total if total > 0 else None,
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
    eco = store.one("SELECT * FROM species_ecology WHERE species = ?", [species])
    info = store.one(
        "SELECT * EXCLUDE (species) FROM species_info WHERE species = ?", [species]
    )

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
        "info": info,
        "ecology": ecology.describe(eco),
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


KM_PER_DEGREE_LAT = 111.2
BACKGROUND_FRACTION = 0.1
MAX_SEASON_GAP = 2
