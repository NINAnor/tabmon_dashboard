"""Audio clip serving and photo proxying."""

import asyncio
import logging
import re
import ssl
from collections import OrderedDict
from functools import lru_cache
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException

from . import mp3
from .config import Settings

log = logging.getLogger("tabmon.media")

_PREFETCH_CONCURRENCY = 4
_cut_semaphore = asyncio.Semaphore(_PREFETCH_CONCURRENCY)


class ClipCache:
    """An LRU of clip bytes with one shared producer task per clip ID."""

    def __init__(self, max_entries: int = 500):
        self.max_entries = max(0, max_entries)
        self._items: OrderedDict[str, bytes] = OrderedDict()
        self._inflight: dict[str, asyncio.Task[bytes]] = {}

    def resize(self, max_entries: int) -> None:
        self.max_entries = max(0, max_entries)
        while len(self._items) > self.max_entries:
            self._items.popitem(last=False)

    def get(self, clip_id: str) -> bytes | None:
        if clip_id not in self._items:
            return None
        self._items.move_to_end(clip_id)
        return self._items[clip_id]

    def contains(self, clip_id: str) -> bool:
        return clip_id in self._items

    def in_flight(self, clip_id: str) -> bool:
        return clip_id in self._inflight

    def _task(self, clip_id: str, producer) -> tuple[asyncio.Task[bytes], bool]:
        existing = self._inflight.get(clip_id)
        if existing is not None:
            return existing, False

        async def load() -> bytes:
            current = asyncio.current_task()
            try:
                content = await producer()
                if self.max_entries:
                    self._items[clip_id] = content
                    self._items.move_to_end(clip_id)
                    while len(self._items) > self.max_entries:
                        self._items.popitem(last=False)
                return content
            finally:
                if self._inflight.get(clip_id) is current:
                    self._inflight.pop(clip_id, None)

        task = asyncio.create_task(load())
        self._inflight[clip_id] = task
        return task, True

    async def get_or_create(self, clip_id: str, producer) -> bytes:
        content = self.get(clip_id)
        if content is not None:
            return content
        task, _ = self._task(clip_id, producer)
        # A cancelled request must not cancel work shared with another waiter.
        return await asyncio.shield(task)

    def prefetch(self, clip_id: str, producer) -> bool:
        if self.contains(clip_id) or self.in_flight(clip_id):
            return False
        task, created = self._task(clip_id, producer)
        if created:
            task.add_done_callback(lambda done: self._log_prefetch_error(clip_id, done))
        return created

    @staticmethod
    def _log_prefetch_error(clip_id: str, task: asyncio.Task[bytes]) -> None:
        try:
            task.result()
        except asyncio.CancelledError:
            pass
        except Exception:
            log.exception("clip prefetch failed for %s", clip_id)

    def __len__(self) -> int:
        return len(self._items)


_clip_cache = ClipCache()


@lru_cache(maxsize=4)
def _s3_client(
    endpoint: str,
    region: str,
    access_key_id: str,
    secret_access_key: str,
    timeout_s: float,
):
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        region_name=region,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        verify=ssl.get_default_verify_paths().cafile or True,
        config=Config(
            connect_timeout=10,
            read_timeout=timeout_s,
            max_pool_connections=32,
            retries={"mode": "adaptive", "max_attempts": 8},
            s3={"addressing_style": "path"},
        ),
    )


def _object_key(path: str) -> str:
    return path.lstrip("/")


def _endpoint_url(endpoint: str) -> str:
    return endpoint if "://" in endpoint else f"https://{endpoint}"


def _client(settings: Settings):
    if not settings.s3_access_key_id or not settings.s3_secret_access_key:
        raise HTTPException(503, "S3 credentials are not configured")
    return _s3_client(
        _endpoint_url(settings.s3_endpoint or "https://s3.nird.sigma2.no"),
        settings.s3_region,
        settings.s3_access_key_id,
        settings.s3_secret_access_key,
        settings.upstream_timeout_s,
    )


def _s3_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ClientError):
        response = exc.response
        status = int(response.get("ResponseMetadata", {}).get("HTTPStatusCode", 502))
        if status == 404 or response.get("Error", {}).get("Code") in {
            "NoSuchKey",
            "NotFound",
        }:
            status = 404
    else:
        status = 502
    return HTTPException(status, "S3 object is not available")


def _read_s3_object(settings: Settings, path: str) -> tuple[bytes, str]:
    try:
        response = _client(settings).get_object(
            Bucket=settings.s3_bucket, Key=_object_key(path)
        )
        with response["Body"] as body:
            content = body.read()
        return content, response.get("ContentType", "application/octet-stream")
    except (BotoCoreError, ClientError) as exc:
        raise _s3_http_error(exc) from None


def _local_file(settings: Settings, path: str) -> Path:
    if settings.data_dir is None:
        raise RuntimeError("local data directory is not configured")
    return settings.data_dir / _object_key(path)


async def fetch_bytes(settings: Settings, path: str) -> tuple[bytes, str]:
    """Read an object from the local bucket mirror or directly from S3."""
    if settings.data_dir is None:
        return await asyncio.to_thread(_read_s3_object, settings, path)

    local = _local_file(settings, path)

    def read_local() -> tuple[bytes, str]:
        try:
            content = local.read_bytes()
        except FileNotFoundError:
            raise HTTPException(404, "File not available") from None
        ctype = {".png": "image/png", ".mp3": "audio/mpeg"}.get(
            local.suffix.lower(), "image/jpeg"
        )
        return content, ctype

    return await asyncio.to_thread(read_local)


def range_reader(settings: Settings, path: str) -> mp3.RangeReader:
    """Synchronous byte-range reader used by mp3.cut_clip in a worker thread."""
    if settings.data_dir is not None:
        local = _local_file(settings, path)

        def read_local(start: int, end: int) -> tuple[bytes, int]:
            try:
                with local.open("rb") as file:
                    file.seek(start)
                    content = file.read(end - start + 1)
                return content, local.stat().st_size
            except FileNotFoundError:
                raise HTTPException(404, "Recording not available") from None

        return read_local

    def read_s3(start: int, end: int) -> tuple[bytes, int]:
        try:
            response = _client(settings).get_object(
                Bucket=settings.s3_bucket,
                Key=_object_key(path),
                Range=f"bytes={start}-{end}",
            )
            with response["Body"] as body:
                content = body.read()
            match = re.search(r"/(\d+)$", response.get("ContentRange", ""))
            total = int(match.group(1)) if match else start + len(content)
            return content, total
        except (BotoCoreError, ClientError) as exc:
            raise _s3_http_error(exc) from None

    return read_s3


def _cut_clip(settings: Settings, clip_id: str, path: str, start_s: float) -> bytes:
    try:
        return mp3.cut_clip(
            range_reader(settings, path),
            start_s,
            settings.clip_context_s,
            settings.clip_detection_s,
        )
    except (RuntimeError, ValueError):
        log.error("clip %s failed while extracting audio", clip_id)
        raise HTTPException(502, "Could not extract audio clip") from None


def _producer(settings: Settings, clip_id: str, path: str, start_s: float):
    async def cut() -> bytes:
        async with _cut_semaphore:
            return await asyncio.to_thread(_cut_clip, settings, clip_id, path, start_s)

    return cut


async def clip_bytes(
    settings: Settings, clip_id: str, path: str, start_s: float
) -> bytes:
    _clip_cache.resize(settings.clip_cache_max_entries)
    return await _clip_cache.get_or_create(
        clip_id, _producer(settings, clip_id, path, start_s)
    )


def schedule_prefetch(settings: Settings, clips: list[dict]) -> None:
    """Start best-effort clip cuts without holding up the clips-list response."""
    _clip_cache.resize(settings.clip_cache_max_entries)
    for clip in clips:
        if clip.get("path") is None or clip.get("start_s") is None:
            continue
        clip_id = str(clip["clip_id"])
        _clip_cache.prefetch(
            clip_id,
            _producer(settings, clip_id, clip["path"], float(clip["start_s"])),
        )
