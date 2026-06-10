"""Supabase Storage helpers for avatar media persistence.

All functions read env vars at call time (so tests can monkeypatch os.environ)
and accept an optional `_client` kwarg (so tests can inject a fake httpx client
without touching the network).

Buckets:
  avatar-media   (PUBLIC)  — generated media: after.jpg, frames_mobile/, master.webm
  avatar-private (PRIVATE) — user-uploaded photos: before.jpg
"""
from __future__ import annotations

import logging
import os
import pathlib
from typing import Optional

import httpx

log = logging.getLogger(__name__)

MEDIA_BUCKET = "avatar-media"
PRIVATE_BUCKET = "avatar-private"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _url() -> str:
    v = os.getenv("SUPABASE_URL")
    if not v:
        raise RuntimeError("SUPABASE_URL env var is not set")
    return v.rstrip("/")


def _service_key() -> str:
    v = os.getenv("SUPABASE_SERVICE_KEY")
    if not v:
        raise RuntimeError("SUPABASE_SERVICE_KEY env var is not set")
    return v


def _storage_headers(content_type: Optional[str] = None) -> dict:
    key = _service_key()
    h = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "x-upsert": "true",
    }
    if content_type:
        h["Content-Type"] = content_type
    return h


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def storage_enabled() -> bool:
    """True iff both SUPABASE_URL and SUPABASE_SERVICE_KEY are set."""
    return bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_KEY"))


def public_url(bucket: str, key: str) -> str:
    """Return the public URL for an object in a public bucket."""
    return f"{_url()}/storage/v1/object/public/{bucket}/{key}"


def upload_file(
    bucket: str,
    key: str,
    local_path: str | pathlib.Path,
    content_type: str,
    *,
    _client: Optional[httpx.Client] = None,
) -> None:
    """Upload local_path to Supabase Storage at bucket/key.

    Uses x-upsert: true so re-uploads overwrite silently.
    Raises on any non-2xx response.
    """
    url = f"{_url()}/storage/v1/object/{bucket}/{key}"
    headers = _storage_headers(content_type)
    data = pathlib.Path(local_path).read_bytes()

    client = _client or httpx.Client(timeout=60)
    try:
        resp = client.post(url, headers=headers, content=data)
        if resp.status_code >= 300:
            raise RuntimeError(
                f"Storage upload failed: {resp.status_code} {resp.text[:200]}"
            )
    finally:
        if _client is None:
            client.close()


def download_to(
    bucket: str,
    key: str,
    local_path: str | pathlib.Path,
    *,
    _client: Optional[httpx.Client] = None,
) -> None:
    """Download bucket/key from Supabase Storage to local_path.

    Raises RuntimeError on 404 or any other non-2xx response.
    """
    url = f"{_url()}/storage/v1/object/{bucket}/{key}"
    sk = _service_key()
    headers = {
        "apikey": sk,
        "Authorization": f"Bearer {sk}",
    }

    client = _client or httpx.Client(timeout=60)
    try:
        resp = client.get(url, headers=headers)
        if resp.status_code == 404:
            raise RuntimeError(f"Storage object not found: {bucket}/{key}")
        if resp.status_code >= 300:
            raise RuntimeError(
                f"Storage download failed: {resp.status_code} {resp.text[:200]}"
            )
        dest = pathlib.Path(local_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(resp.content)
    finally:
        if _client is None:
            client.close()
