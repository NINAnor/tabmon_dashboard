import asyncio
import threading
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
        data_dir=data_dir,
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


def test_phenology_orders_north_first_and_shows_later_onset(client):
    data = client.get(
        "/api/public/phenology/species", params={"species": "Cuculus canorus"}
    ).json()
    labels = [g["label"] for g in data["groups"]]
    assert labels == ["North", "South"]
    north, south = data["groups"]
    assert north["onset_week"] > south["onset_week"]
    assert {"onset_week", "peak_week", "end_week"} <= north.keys()
    week = north["weeks"][north["peak_week"] - 1]
    assert week["rate"] == pytest.approx(week["n"] / (week["minutes"] / 60))


def test_phenology_wave_response_shape(client):
    data = client.get(
        "/api/public/phenology/species", params={"species": "Cuculus canorus"}
    ).json()
    assert "season_start_week" in data
    assert 1 <= data["season_start_week"] <= 53
    assert data["migration"]["kind"] is None
    assert data["migration"]["show_waves"] is False
    assert data["migration"]["reason"] == "migration strategy unknown"
    assert {"spring", "autumn"} <= data["migration"].keys()
    for wave in (data["migration"]["spring"], data["migration"]["autumn"]):
        assert {"n", "clear", "points", "reason"} <= wave.keys()
    assert all(
        {"onset_week", "peak_week", "end_week"} <= group.keys()
        for group in data["groups"]
    )


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


def test_clip_prefetch_runs_for_listed_ids(client, monkeypatch):
    from tabmon_api import media

    called = []
    cut_done = threading.Event()

    def fake_cut(settings, clip_id, path, start_s):
        called.append(clip_id)
        cut_done.set()
        return b"mp3 bytes"

    monkeypatch.setattr(media, "_cut_clip", fake_cut)
    response = client.get("/api/public/clips", params={"species": "Cuculus canorus"})
    listed_ids = [clip["clip_id"] for clip in response.json()]

    assert response.status_code == 200
    assert listed_ids
    assert cut_done.wait(2)
    assert called == listed_ids


def test_clip_cache_lru_and_in_flight_deduplication():
    from tabmon_api.media import ClipCache

    async def exercise_cache():
        cache = ClipCache(max_entries=2)

        async def make(content):
            async def producer():
                return content

            return await cache.get_or_create(content.decode(), producer)

        await make(b"a")
        await make(b"b")
        assert cache.get("a") == b"a"  # refresh a's LRU position
        await make(b"c")
        assert len(cache) == 2
        assert cache.contains("a")
        assert not cache.contains("b")
        assert cache.contains("c")

        calls = 0

        async def shared_producer():
            nonlocal calls
            calls += 1
            await asyncio.sleep(0.01)
            return b"shared"

        results = await asyncio.gather(
            cache.get_or_create("same", shared_producer),
            cache.get_or_create("same", shared_producer),
        )
        assert results == [b"shared", b"shared"]
        assert calls == 1

    asyncio.run(exercise_cache())


def test_s3_config_reads_rclone_and_env_overrides(tmp_path, monkeypatch):
    config = tmp_path / "rclone.conf"
    config.write_text(
        "[nirds3]\n"
        "type = s3\n"
        "access_key_id = config-key\n"
        "secret_access_key = config-secret%with%percent\n"
        "endpoint = https://config.s3.example\n"
    )
    monkeypatch.setenv("RCLONE_CONFIG", str(config))
    for name in (
        "S3_ACCESS_KEY_ID",
        "S3_SECRET_ACCESS_KEY",
        "S3_ENDPOINT",
        "S3_BUCKET",
    ):
        monkeypatch.delenv(name, raising=False)

    from_config = Settings()
    assert from_config.s3_access_key_id == "config-key"
    assert from_config.s3_secret_access_key == "config-secret%with%percent"
    assert from_config.s3_endpoint == "https://config.s3.example"

    monkeypatch.setenv("S3_ACCESS_KEY_ID", "env-key")
    monkeypatch.setenv("S3_SECRET_ACCESS_KEY", "env-secret")
    monkeypatch.setenv("S3_ENDPOINT", "https://env.s3.example")
    monkeypatch.setenv("S3_BUCKET", "env-bucket")
    from_env = Settings()
    assert from_env.s3_access_key_id == "env-key"
    assert from_env.s3_secret_access_key == "env-secret"
    assert from_env.s3_endpoint == "https://env.s3.example"
    assert from_env.s3_bucket == "env-bucket"

    from tabmon_api.media import _endpoint_url

    assert _endpoint_url("s3.nird.sigma2.no") == "https://s3.nird.sigma2.no"
    assert _endpoint_url("https://s3.example") == "https://s3.example"


def test_species_card(client):
    card = client.get("/api/public/species/Cuculus canorus").json()
    assert 0 < card["hour_share"] < 1
    assert card["trend"]["label"] == "uncertain"


def test_season_markers_preserve_winter_visitor_year_wrap():
    from tabmon_api.phenology import season_markers, season_start

    weeks = []
    for week in range(1, 54):
        rate = 10 if week >= 45 or week <= 8 else 0.5
        if 25 <= week <= 35:
            rate = 0
        weeks.append(
            {
                "week": week,
                "rate": rate,
                "low_effort": False,
            }
        )
    group = {"sparse": False, "weeks": weeks}
    start = season_start([group])
    markers = season_markers(weeks, start)
    assert 20 <= start <= 40
    assert markers["onset_week"] > markers["end_week"]
    assert markers["onset_week"] in range(45, 54)
    assert markers["peak_week"] in range(45, 54)


def test_spring_and_autumn_wave_fits():
    from tabmon_api.phenology import fit_wave

    lats = [40 + i * 5 for i in range(6)]
    spring_points = [
        {"lat": lat, "day": 80 + (lat - 40) * 1.1, "weight": 10.0} for lat in lats
    ]
    spring = fit_wave(spring_points, "spring")
    assert spring["clear"]
    assert spring["days_per_degree"] == pytest.approx(1.1)
    assert spring["km_per_day"] == pytest.approx(111.2 / 1.1)

    autumn_points = [
        {"lat": lat, "day": 250 - (lat - 40) * 1.2, "weight": 10.0} for lat in lats
    ]
    autumn = fit_wave(autumn_points, "autumn")
    assert autumn["clear"]
    assert autumn["days_per_degree"] == pytest.approx(-1.2)
    assert "km_per_day" not in autumn

    flat = [{**point, "day": 150} for point in spring_points]
    assert not fit_wave(flat, "spring")["clear"]
    assert not fit_wave(spring_points[:4], "spring")["clear"]


def test_mp3_layout_from_xing_header():
    from tabmon_api.mp3 import clip_window, parse_layout

    frame_header = bytes([0xFF, 0xFB, 0x90, 0xC0])  # MPEG-1 L3, 128 kbps, 44.1 kHz
    xing = b"Xing" + (3).to_bytes(4, "big") + (11486).to_bytes(4, "big")
    xing += (4_000_000).to_bytes(4, "big")
    head = b"ID3\x04\x00\x00\x00\x00\x00\x05" + b"\x00" * 5 + frame_header
    head += b"\x00" * 32 + xing + b"\x00" * 200
    layout = parse_layout(head, 4_000_100)
    assert layout.audio_start == 15
    assert layout.duration == pytest.approx(11486 * 1152 / 44100)
    assert layout.byte_at(layout.duration / 2) == 15 + 2_000_000
    assert clip_window(3, 5, 3) == (0, 11)
    assert clip_window(100, 5, 3) == (95, 13)


def test_ecology_description():
    import json as _json

    from tabmon_api.ecology import _month_span, describe

    assert _month_span([4, 5, 6]) == "Apr–Jun"
    assert _month_span([10, 11, 12, 1, 2]) == "Oct–Feb"
    assert _month_span(list(range(1, 13))) == "all year"
    assert _month_span([3, 4, 5, 9]) == "mainly Mar–May"

    d = describe(
        {
            "iucn": "VU",
            "migration": "long_distance",
            "habitats": ["woodland"],
            "diet": ["insects & spiders"],
            "peak_hour": 5,
            "night_share": 0.05,
            "active_months": _json.dumps({"Norway": [5, 6], "Spain": [4, 5, 6]}),
        }
    )
    assert d["iucn_label"] == "Vulnerable"
    assert d["migration_label"] == "Long-distance migrant"
    assert "Sahara" in d["how_to_read"][0]
    assert "amber spring wave" in d["how_to_read"][0]
    assert "coral autumn wave" in d["how_to_read"][0]
    assert "fall silent" in d["how_to_read"][0]
    assert "at dawn" in d["how_to_read"][1]
    assert d["how_to_read"][1].index("Spain") < d["how_to_read"][1].index("Norway")

    owl = describe({"migration": "resident", "peak_hour": 23, "night_share": 0.7})
    assert "at night" in owl["how_to_read"][1]
    assert describe(None) is None


def test_network_summary(client):
    data = client.get("/api/public/network").json()
    assert {c["country"] for c in data["countries"]} == {"Spain", "Norway"}
    spain = next(c for c in data["countries"] if c["country"] == "Spain")
    assert spain["n_clusters"] == 1 and spain["top_species"] == "Common Cuckoo"
    assert data["monthly"] and data["pipeline"]["calibrated"] == 1
    top = client.get("/api/public/clusters/norway-north/species").json()
    assert top[0]["species"] == "Cuculus canorus" and top[0]["rate"] > 0


def test_most_wanted_endpoint(client):
    # The fixture's only species is calibrated, so nothing is "wanted".
    assert client.get("/api/public/most-wanted").json() == []


def test_species_diel(client):
    d = client.get(
        "/api/public/phenology/diel", params={"species": "Cuculus canorus"}
    ).json()
    assert len(d["overall"]) == 24 and len(d["grid"]) == 12
    # The fixture only has detections at 05:00, with effort at 05:00 and 06:00.
    assert d["peak_hour"] == 5
    assert d["overall"][6] == 0 and d["overall"][0] is None
    assert set(d["countries"]) == {"Spain", "Norway"}
    assert d["night_share"] == 0


def test_ops_sites_have_status_field(client):
    client.post("/api/auth/login", json={"username": "tabmon", "password": "pw"})
    sites = client.get("/api/ops/sites").json()
    # No device_status in the fixture: the field exists but is empty.
    assert sites and all("status" in s and s["status"] is None for s in sites)
    detail = client.get(f"/api/ops/sites/{sites[0]['site_id']}").json()
    assert "status" in detail


def test_season_markers_ignore_background_noise():
    from tabmon_api.phenology import season_markers

    # A true season in weeks 18-26 plus weak false positives every other week.
    weeks = [
        {
            "week": w,
            "low_effort": False,
            "rate": 10.0 if 18 <= w <= 26 else 0.3,
        }
        for w in range(1, 54)
    ]
    m = season_markers(weeks, start=32)
    assert m["onset_week"] == 18
    assert m["end_week"] == 26


def test_season_markers_ignore_isolated_bursts():
    from tabmon_api.phenology import season_markers

    weeks = [{"week": w, "low_effort": False, "rate": 0.0} for w in range(1, 54)]
    for w in range(20, 27):
        weeks[w - 1]["rate"] = 8.0
    weeks[43]["rate"] = 6.0  # one-off false-positive burst in week 44
    m = season_markers(weeks, start=32)
    assert (m["onset_week"], m["end_week"]) == (20, 26)


def test_wave_points_use_seasonal_windows():
    from tabmon_api.phenology import _wave_points

    groups = [
        {
            "id": "south",
            "lat": 41.0,
            "total": 900,
            "sparse": False,
            "onset_week": 43,
            "end_week": 10,
        },
        {
            "id": "mid",
            "lat": 52.0,
            "total": 900,
            "sparse": False,
            "onset_week": 14,
            "end_week": 36,
        },
        {
            "id": "north",
            "lat": 65.0,
            "total": 900,
            "sparse": False,
            "onset_week": 19,
            "end_week": 33,
        },
    ]
    spring = _wave_points(groups, "onset_week", start=30)
    autumn = _wave_points(groups, "end_week", start=30)
    # The southern wintering population (onset in October) is not part of the spring wave.
    assert [p["id"] for p in spring] == ["mid", "north"]
    assert [p["id"] for p in autumn] == ["mid", "north"]


def test_clip_window_is_one_second_of_context():
    from tabmon_api.mp3 import clip_window

    assert clip_window(3, 1, 3) == (2, 5)
    assert clip_window(0.5, 1, 3) == (0, 4.5)


def test_clip_metadata_window(client):
    clip = client.get(
        "/api/public/clips", params={"species": "Cuculus canorus"}
    ).json()[0]
    # Fixture detection starts at 3 s: the 5 s clip starts at 2 s, detection at 1-4 s.
    assert (clip["window_start"], clip["window_end"]) == (1, 4)
