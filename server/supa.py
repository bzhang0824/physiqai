"""Thin httpx wrapper for Supabase Auth + PostgREST.

All functions are hermetic-testable: they read env vars at call time (so tests
can monkeypatch os.environ) and accept an optional `_client` kwarg (so tests
can inject a fake httpx client without touching the network).

Env vars required at runtime:
  SUPABASE_URL         — https://<project>.supabase.co
  SUPABASE_SERVICE_KEY — service-role JWT (bypasses RLS)
"""
from __future__ import annotations

import logging
import os
from typing import Any, Optional

import httpx

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal helpers — read env at call time so tests can patch os.environ
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


def _auth_headers(token: str) -> dict:
    """Headers for Supabase Auth admin calls (verify token)."""
    return {
        "apikey": _service_key(),
        "Authorization": f"Bearer {token}",
    }


def _postgrest_headers() -> dict:
    """Headers for PostgREST calls (service-role — bypasses RLS)."""
    key = _service_key()
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def verify_token(token: str, *, _client: Optional[httpx.Client] = None) -> Optional[dict]:
    """Verify a Supabase user JWT.

    Returns {"id": "<uuid>", "email": "<email>"} on success, or None if the
    token is invalid / expired. The caller is responsible for mapping None to
    a 401 response.
    """
    url = f"{_url()}/auth/v1/user"
    headers = _auth_headers(token)

    client = _client or httpx.Client(timeout=10)
    try:
        resp = client.get(url, headers=headers)
    finally:
        if _client is None:
            client.close()

    if resp.status_code != 200:
        return None
    body = resp.json()
    # Supabase returns the user object; we only surface id + email.
    return {"id": body["id"], "email": body.get("email", "")}


def count_user_avatars(user_id: str, *, _client: Optional[httpx.Client] = None) -> int:
    """Count how many avatar rows exist for a user (all statuses)."""
    url = f"{_url()}/rest/v1/avatars"
    headers = {**_postgrest_headers(), "Prefer": "count=exact"}
    params = {"user_id": f"eq.{user_id}", "select": "id"}

    client = _client or httpx.Client(timeout=10)
    try:
        resp = client.get(url, headers=headers, params=params)
        resp.raise_for_status()
    finally:
        if _client is None:
            client.close()

    # PostgREST returns the count in Content-Range: 0-N/total
    content_range = resp.headers.get("content-range", "")
    # e.g. "0-0/1" or "*/0" (empty)
    if "/" in content_range:
        total_part = content_range.split("/")[-1]
        try:
            return int(total_part)
        except ValueError:
            pass
    # Fallback: count the returned rows
    return len(resp.json())


def get_avatar_limit(user_id: str, *, _client: Optional[httpx.Client] = None) -> int:
    """Return the user's avatar_limit from the profiles table (default 1)."""
    url = f"{_url()}/rest/v1/profiles"
    params = {"id": f"eq.{user_id}", "select": "avatar_limit"}

    client = _client or httpx.Client(timeout=10)
    try:
        resp = client.get(url, headers=_postgrest_headers(), params=params)
        resp.raise_for_status()
    finally:
        if _client is None:
            client.close()

    rows = resp.json()
    if not rows:
        return 1  # no profile row yet → default
    return rows[0].get("avatar_limit", 1)


def insert_avatar(record: dict, *, _client: Optional[httpx.Client] = None) -> dict:
    """Insert a row into the avatars table. Returns the inserted row."""
    url = f"{_url()}/rest/v1/avatars"
    headers = {**_postgrest_headers(), "Prefer": "return=representation"}

    client = _client or httpx.Client(timeout=10)
    try:
        resp = client.post(url, headers=headers, json=record)
        resp.raise_for_status()
    finally:
        if _client is None:
            client.close()

    rows = resp.json()
    return rows[0] if rows else record


def update_avatar(job: str, fields: dict, *, _client: Optional[httpx.Client] = None) -> None:
    """PATCH the avatars row identified by job."""
    url = f"{_url()}/rest/v1/avatars"
    params = {"job": f"eq.{job}"}

    client = _client or httpx.Client(timeout=10)
    try:
        resp = client.patch(url, headers=_postgrest_headers(), params=params, json=fields)
        resp.raise_for_status()
    finally:
        if _client is None:
            client.close()


def get_avatar_by_job(job: str, *, _client: Optional[httpx.Client] = None) -> Optional[dict]:
    """Return the avatars row for the given job id, or None."""
    url = f"{_url()}/rest/v1/avatars"
    params = {"job": f"eq.{job}", "select": "*"}

    client = _client or httpx.Client(timeout=10)
    try:
        resp = client.get(url, headers=_postgrest_headers(), params=params)
        resp.raise_for_status()
    finally:
        if _client is None:
            client.close()

    rows = resp.json()
    return rows[0] if rows else None


def latest_done_for_user(user_id: str, *, _client: Optional[httpx.Client] = None) -> Optional[dict]:
    """Return the most recently created 'done' avatar row for the user, or None."""
    url = f"{_url()}/rest/v1/avatars"
    params = {
        "user_id": f"eq.{user_id}",
        "status": "eq.done",
        "order": "created_at.desc",
        "limit": "1",
        "select": "*",
    }

    client = _client or httpx.Client(timeout=10)
    try:
        resp = client.get(url, headers=_postgrest_headers(), params=params)
        resp.raise_for_status()
    finally:
        if _client is None:
            client.close()

    rows = resp.json()
    return rows[0] if rows else None


def insert_checkin(record: dict, *, _client: Optional[httpx.Client] = None) -> dict:
    """Insert a row into the checkins table. Returns the inserted row."""
    url = f"{_url()}/rest/v1/checkins"
    headers = {**_postgrest_headers(), "Prefer": "return=representation"}

    client = _client or httpx.Client(timeout=10)
    try:
        resp = client.post(url, headers=headers, json=record)
        resp.raise_for_status()
    finally:
        if _client is None:
            client.close()

    rows = resp.json()
    return rows[0] if rows else record


def list_checkins(user_id: str, limit: int = 12, *, _client: Optional[httpx.Client] = None) -> list:
    """Return the most recent check-in rows for a user (newest first)."""
    url = f"{_url()}/rest/v1/checkins"
    params = {
        "user_id": f"eq.{user_id}",
        "order": "created_at.desc",
        "limit": str(limit),
        "select": "*",
    }

    client = _client or httpx.Client(timeout=10)
    try:
        resp = client.get(url, headers=_postgrest_headers(), params=params)
        resp.raise_for_status()
    finally:
        if _client is None:
            client.close()

    return resp.json()


def get_profile(user_id: str, *, _client: Optional[httpx.Client] = None) -> Optional[dict]:
    """Return the profiles row for a user, or None if it doesn't exist."""
    url = f"{_url()}/rest/v1/profiles"
    params = {"id": f"eq.{user_id}", "select": "*"}

    client = _client or httpx.Client(timeout=10)
    try:
        resp = client.get(url, headers=_postgrest_headers(), params=params)
        resp.raise_for_status()
    finally:
        if _client is None:
            client.close()

    rows = resp.json()
    return rows[0] if rows else None


def update_profile(user_id: str, fields: dict, *, _client: Optional[httpx.Client] = None) -> None:
    """PATCH the profiles row identified by id."""
    url = f"{_url()}/rest/v1/profiles"
    params = {"id": f"eq.{user_id}"}

    client = _client or httpx.Client(timeout=10)
    try:
        resp = client.patch(url, headers=_postgrest_headers(), params=params, json=fields)
        resp.raise_for_status()
    finally:
        if _client is None:
            client.close()


def latest_avatar_for_user(user_id: str, *, _client: Optional[httpx.Client] = None) -> Optional[dict]:
    """Return the most recently created avatar row (any status) for the user, or None."""
    url = f"{_url()}/rest/v1/avatars"
    params = {
        "user_id": f"eq.{user_id}",
        "order": "created_at.desc",
        "limit": "1",
        "select": "*",
    }

    client = _client or httpx.Client(timeout=10)
    try:
        resp = client.get(url, headers=_postgrest_headers(), params=params)
        resp.raise_for_status()
    finally:
        if _client is None:
            client.close()

    rows = resp.json()
    return rows[0] if rows else None


def update_checkin(checkin_id: str, fields: dict, *, _client: Optional[httpx.Client] = None) -> None:
    """PATCH the checkins row identified by id."""
    url = f"{_url()}/rest/v1/checkins"
    params = {"id": f"eq.{checkin_id}"}

    client = _client or httpx.Client(timeout=10)
    try:
        resp = client.patch(url, headers=_postgrest_headers(), params=params, json=fields)
        resp.raise_for_status()
    finally:
        if _client is None:
            client.close()
