from datetime import date, timedelta

import duckdb
import pytest
from fastapi.testclient import TestClient

from tabmon_api.config import Settings, get_settings
from tabmon_api.main import app


@pytest.fixture
def data_dir(tmp_path):
    """A tiny bucket mirror: two clusters, one species that arrives later up north."""
    tables = tmp_path / "data/preprocessed/dashboard"
    tables.mkdir(parents=True)
    con = duckdb.connect()
    con.execute(
        """
        CREATE TABLE deployments AS SELECT * FROM (VALUES
            ('D1', 'aaaa1111', 'Spain', 'South', 'Site S', 'spain-south-site-s',
             'spain-south', 41.0, 2.0, true, 'Forest', 200.0, 'N', 5.0,
             TIMESTAMP '2025-01-01', NULL::TIMESTAMP, NULL),
            ('D2', 'bbbb2222', 'Norway', 'North', 'Site N', 'norway-north-site-n',
             'norway-north', 69.0, 25.0, true, 'Forest', 200.0, 'N', 5.0,
             TIMESTAMP '2025-01-01', NULL::TIMESTAMP, NULL)
        ) t(deployment_id, device_id, country, cluster, site, site_id, cluster_id,
            lat, lon, active, habitat, mic_height_cm, mic_direction,
            coord_uncertainty_m, begin_ts, end_ts, comments)
        """
    )
    days = [date(2025, 1, 1) + timedelta(days=i) for i in range(365)]
    effort = [
        (s, d, h, 60.0)
        for s in ("spain-south-site-s", "norway-north-site-n")
        for d in days
        for h in (5, 6)
    ]
    con.execute(
        "CREATE TABLE effort (site_id VARCHAR, date DATE, hour TINYINT, recorded_minutes FLOAT)"
    )
    con.executemany("INSERT INTO effort VALUES (?, ?, ?, ?)", effort)
    phen = []
    for d in days:
        doy = d.timetuple().tm_yday
        if 100 <= doy <= 160:
            phen.append(("Cuculus canorus", "spain-south-site-s", d, 5, 10))
        if 140 <= doy <= 190:
            phen.append(("Cuculus canorus", "norway-north-site-n", d, 5, 10))
    con.execute(
        "CREATE TABLE phenology (species VARCHAR, site_id VARCHAR, date DATE, hour TINYINT, n_detections INTEGER)"
    )
    con.executemany("INSERT INTO phenology VALUES (?, ?, ?, ?, ?)", phen)
    con.execute(
        """
        CREATE TABLE species AS SELECT 'Cuculus canorus' AS species,
            'Common Cuckoo' AS common_en, NULL AS common_fr, NULL AS common_es,
            NULL AS common_nl, NULL AS common_no, 1120::BIGINT AS n_detections,
            2::BIGINT AS n_sites, 2::BIGINT AS n_countries, 0.45 AS threshold,
            'calibrated' AS threshold_source, 193::BIGINT AS n_validated,
            0.9 AS precision_at_threshold
        """
    )
    con.execute(
        """
        CREATE TABLE clips AS SELECT 'abc' AS clip_id, 'Cuculus canorus' AS species,
            'spain-south-site-s' AS site_id, 'spain-south' AS cluster_id,
            'Spain' AS country, 'secret/path.mp3' AS path, 3 AS start_s,
            0.95 AS confidence, true AS validated, TIMESTAMP '2025-05-01 05:00' AS recorded_at
        """
    )
    con.execute(
        "CREATE TABLE photos (path VARCHAR, name VARCHAR, device_id VARCHAR, picture_type VARCHAR)"
    )
    con.execute(
        "CREATE TABLE validations (country VARCHAR, species VARCHAR, source VARCHAR, "
        "n_validated BIGINT, n_correct BIGINT)"
    )
    for t in (
        "deployments",
        "effort",
        "phenology",
        "species",
        "clips",
        "photos",
        "validations",
    ):
        con.execute(f"COPY {t} TO '{tables}/{t}.parquet' (FORMAT parquet)")
    return tmp_path


@pytest.fixture
def client(data_dir):
    settings = Settings(
        data_url=str(data_dir),
        session_secret="test",
        dashboard_password="pw",
        species_media_csv=data_dir / "none.csv",
    )
    app.dependency_overrides[get_settings] = lambda: settings
    from tabmon_api import main

    original = main.get_settings
    main.get_settings = lambda: settings
    with TestClient(app) as c:
        import time

        for _ in range(50):
            if c.get("/api/health").json()["loaded_at"]:
                break
            time.sleep(0.1)
        yield c
    main.get_settings = original
    app.dependency_overrides.clear()


def test_public_clusters_are_generalised(client):
    rows = client.get("/api/public/clusters").json()
    assert {r["id"] for r in rows} == {"spain-south", "norway-north"}
    for r in rows:
        assert round(r["lat"], 1) == r["lat"]
        assert "path" not in r


def test_phenology_orders_north_first_and_shows_later_arrival(client):
    data = client.get(
        "/api/public/phenology/species", params={"species": "Cuculus canorus"}
    ).json()
    labels = [g["label"] for g in data["groups"]]
    assert labels == ["North", "South"]
    north, south = data["groups"]
    assert north["median_week"] > south["median_week"]
    assert north["first_week"] > south["first_week"]
    week = north["weeks"][north["median_week"] - 1]
    assert week["rate"] == pytest.approx(week["n"] / (week["minutes"] / 60))


def test_site_level_requires_login(client):
    params = {"species": "Cuculus canorus", "level": "site"}
    assert client.get("/api/public/phenology/species", params=params).status_code == 401
    assert client.get("/api/ops/devices").status_code == 401
    assert (
        client.post(
            "/api/auth/login", json={"username": "tabmon", "password": "no"}
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/auth/login", json={"username": "tabmon", "password": "pw"}
        ).status_code
        == 200
    )
    assert client.get("/api/public/phenology/species", params=params).status_code == 200
    assert client.get("/api/ops/sites").status_code == 200


def test_clip_metadata_hides_bucket_path(client):
    clips = client.get(
        "/api/public/clips", params={"species": "Cuculus canorus"}
    ).json()
    assert clips and all("path" not in c for c in clips)


def test_species_card(client):
    card = client.get("/api/public/species/Cuculus canorus").json()
    assert 0 < card["hour_share"] < 1
    assert card["trend"]["label"] == "uncertain"
