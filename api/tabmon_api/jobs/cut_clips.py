"""
Pre-cut every example clip listed in clips.parquet and upload it to the bucket,
so the dashboard can serve small files instantly instead of reading recordings.

Incremental: clips already present in the bucket are skipped.

    python -m tabmon_api.jobs.cut_clips --workers 16
Needs S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY, S3_ENDPOINT and S3_BUCKET.
"""

import argparse
import logging
import os
import re
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3
import duckdb
from botocore.config import Config

from .. import mp3
from ..config import get_settings

log = logging.getLogger("tabmon.cut_clips")


def s3_client():
    endpoint = os.environ.get("S3_ENDPOINT", "s3.nird.sigma2.no")
    if not endpoint.startswith("http"):
        endpoint = f"https://{endpoint}"
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=os.environ["S3_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["S3_SECRET_ACCESS_KEY"],
        region_name=os.environ.get("S3_REGION", "us-east-1"),
        config=Config(
            retries={"max_attempts": 5, "mode": "adaptive"},
            read_timeout=180,
            max_pool_connections=64,
        ),
    )


def s3_range_reader(s3, bucket: str, key: str) -> mp3.RangeReader:
    def read(start: int, end: int) -> tuple[bytes, int]:
        obj = s3.get_object(Bucket=bucket, Key=key, Range=f"bytes={start}-{end}")
        match = re.search(r"/(\d+)$", obj.get("ContentRange", ""))
        body = obj["Body"].read()
        return body, int(match.group(1)) if match else start + len(body)

    return read


def existing_keys(s3, bucket: str, prefix: str) -> set[str]:
    keys = set()
    for page in s3.get_paginator("list_objects_v2").paginate(
        Bucket=bucket, Prefix=prefix
    ):
        keys.update(o["Key"] for o in page.get("Contents", []))
    return keys


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--limit", type=int, help="Only cut this many (for testing)")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    settings = get_settings()
    bucket = os.environ.get("S3_BUCKET", "bencretois-ns8129k-proj-tabmon")
    prefix = settings.tables_prefix.strip("/")
    s3 = s3_client()

    with tempfile.NamedTemporaryFile(suffix=".parquet") as tmp:
        s3.download_fileobj(bucket, f"{prefix}/clips.parquet", tmp)
        tmp.flush()
        clips = duckdb.sql(
            f"SELECT clip_id, path, start_s FROM read_parquet('{tmp.name}')"
        ).fetchall()

    clip_prefix = f"{prefix}/clips/{mp3.CLIP_VERSION}/"
    done = existing_keys(s3, bucket, clip_prefix)
    todo = [c for c in clips if f"{clip_prefix}{c[0]}.mp3" not in done]
    if args.limit:
        todo = todo[: args.limit]
    log.info(
        "%d clips listed, %d already cut, %d to do", len(clips), len(done), len(todo)
    )

    def work(clip):
        clip_id, path, start_s = clip
        audio = mp3.cut_clip(
            s3_range_reader(s3, bucket, path),
            float(start_s),
            settings.clip_context_s,
            settings.clip_detection_s,
        )
        s3.put_object(
            Bucket=bucket,
            Key=f"{clip_prefix}{clip_id}.mp3",
            Body=audio,
            ContentType="audio/mpeg",
        )
        return len(audio)

    started, ok, failed = time.monotonic(), 0, 0
    with ThreadPoolExecutor(args.workers) as pool:
        futures = {pool.submit(work, c): c for c in todo}
        for fut in as_completed(futures):
            try:
                fut.result()
                ok += 1
            except Exception as exc:  # keep going; failures are retried next run
                failed += 1
                log.warning("clip %s failed: %s", futures[fut][0], exc)
            if (ok + failed) % 250 == 0:
                rate = (ok + failed) / (time.monotonic() - started)
                log.info("%d/%d done (%.1f clips/s)", ok + failed, len(todo), rate)
    log.info(
        "finished: %d cut, %d failed in %.0fs", ok, failed, time.monotonic() - started
    )


if __name__ == "__main__":
    main()
