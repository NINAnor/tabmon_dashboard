"""Audio clip extraction and photo proxying."""

import asyncio
import logging
import shutil
from pathlib import Path
from urllib.parse import quote

import httpx
from fastapi import HTTPException

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


async def clip_file(
    settings: Settings, clip_id: str, path: str, start_s: float
) -> Path:
    """Cut a short mp3 around a detection, cached on disk."""
    cache = settings.clip_cache_dir
    cache.mkdir(parents=True, exist_ok=True)
    target = cache / f"{clip_id}.mp3"
    if target.exists():
        return target

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise HTTPException(503, "ffmpeg is not installed on the API server")

    lock = _locks.setdefault(clip_id, asyncio.Lock())
    async with lock:
        if target.exists():
            return target
        tmp = target.with_suffix(".part.mp3")
        offset = max(0.0, start_s - settings.clip_pre_roll_s)
        proc = await asyncio.create_subprocess_exec(
            ffmpeg,
            "-nostdin",
            "-loglevel",
            "error",
            "-ss",
            f"{offset:.2f}",
            "-t",
            f"{settings.clip_length_s:.2f}",
            "-i",
            bucket_url(settings, path),
            "-ac",
            "1",
            "-b:a",
            "128k",
            "-y",
            str(tmp),
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0 or not tmp.exists():
            log.error("ffmpeg failed for %s: %s", clip_id, stderr.decode()[-500:])
            tmp.unlink(missing_ok=True)
            raise HTTPException(502, "Could not extract audio clip")
        tmp.rename(target)
    _locks.pop(clip_id, None)
    return target


async def fetch_bytes(settings: Settings, path: str) -> tuple[bytes, str]:
    if not is_remote(settings):
        local = Path(bucket_url(settings, path))
        if not local.is_file():
            raise HTTPException(404, "File not available")
        ctype = "image/png" if local.suffix.lower() == ".png" else "image/jpeg"
        return local.read_bytes(), ctype
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(bucket_url(settings, path))
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, "Upstream file not available")
    return resp.content, resp.headers.get("content-type", "application/octet-stream")
