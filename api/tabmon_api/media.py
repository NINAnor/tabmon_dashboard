"""Audio clip serving and photo proxying."""

import asyncio
import logging
import re
from pathlib import Path
from urllib.parse import quote

import httpx
from fastapi import HTTPException

from . import mp3
from .config import Settings

log = logging.getLogger("tabmon.media")

_locks: dict[str, asyncio.Lock] = {}


def is_remote(settings: Settings) -> bool:
    return settings.data_url.startswith(("http://", "https://"))


def bucket_url(settings: Settings, path: str) -> str:
    """URL (or local path, when developing against a mirror) of a bucket object."""
    base = settings.data_url.rstrip("/")
    if is_remote(settings):
        return f"{base}/{quote(path.lstrip('/'))}"
    return str(Path(base) / path.lstrip("/"))


def precut_key(settings: Settings, clip_id: str) -> str:
    """Bucket path of a pre-cut clip produced by the data-transfer pipeline."""
    return f"{settings.tables_prefix.strip('/')}/clips/{mp3.CLIP_VERSION}/{clip_id}.mp3"


def range_reader(settings: Settings, path: str) -> mp3.RangeReader:
    """Synchronous byte-range reader for a bucket object (HTTP via rclone, or local)."""
    if not is_remote(settings):
        local = Path(bucket_url(settings, path))

        def read_local(start: int, end: int) -> tuple[bytes, int]:
            with local.open("rb") as fh:
                fh.seek(start)
                return fh.read(end - start + 1), local.stat().st_size

        return read_local

    url = bucket_url(settings, path)

    def read_http(start: int, end: int) -> tuple[bytes, int]:
        resp = httpx.get(
            url,
            headers={"Range": f"bytes={start}-{end}"},
            timeout=settings.upstream_timeout_s,
        )
        if resp.status_code == 206:
            match = re.search(r"/(\d+)$", resp.headers.get("content-range", ""))
            total = int(match.group(1)) if match else start + len(resp.content)
            return resp.content, total
        if resp.status_code == 200:  # server ignored the range
            return resp.content[start : end + 1], len(resp.content)
        raise HTTPException(resp.status_code, "Recording not available")

    return read_http


async def clip_file(
    settings: Settings, clip_id: str, path: str, start_s: float
) -> Path:
    """Path to a cached clip: local cache, else pre-cut clip, else cut on demand."""
    cache = settings.clip_cache_dir
    cache.mkdir(parents=True, exist_ok=True)
    target = cache / f"{clip_id}.{mp3.CLIP_VERSION}.mp3"
    if target.exists():
        return target

    lock = _locks.setdefault(clip_id, asyncio.Lock())
    async with lock:
        if target.exists():
            return target
        try:
            content, _ = await fetch_bytes(settings, precut_key(settings, clip_id))
        except HTTPException:
            try:
                content = await asyncio.to_thread(
                    mp3.cut_clip,
                    range_reader(settings, path),
                    start_s,
                    settings.clip_context_s,
                    settings.clip_detection_s,
                )
            except (RuntimeError, ValueError) as exc:
                log.error("clip %s failed: %s", clip_id, exc)
                raise HTTPException(502, "Could not extract audio clip") from exc
        tmp = target.with_suffix(".part")
        tmp.write_bytes(content)
        tmp.rename(target)
    _locks.pop(clip_id, None)
    return target


async def fetch_bytes(settings: Settings, path: str) -> tuple[bytes, str]:
    if not is_remote(settings):
        local = Path(bucket_url(settings, path))
        if not local.is_file():
            raise HTTPException(404, "File not available")
        ctype = {".png": "image/png", ".mp3": "audio/mpeg"}.get(
            local.suffix.lower(), "image/jpeg"
        )
        return local.read_bytes(), ctype
    async with httpx.AsyncClient(timeout=settings.upstream_timeout_s) as client:
        resp = await client.get(bucket_url(settings, path))
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, "Upstream file not available")
    return resp.content, resp.headers.get("content-type", "application/octet-stream")
