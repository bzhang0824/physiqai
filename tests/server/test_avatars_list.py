"""Tests for GET /avatars (avatar list endpoint).

TDD spec:
  - 401 without token
  - empty list when no avatars
  - newest-first ordering
  - failed avatars excluded
  - in-progress avatars included
  - weight_lb and bf_pct parsed as floats from string inputs
  - rows from other users never appear
"""
from __future__ import annotations

import pathlib
import sys
from datetime import datetime, timezone

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

try:
    import pipeline.avatar  # noqa: F401
    import server.avatar_jobs  # noqa: F401
    _MODULES_MISSING = False
except ImportError:
    _MODULES_MISSING = True

pytestmark = pytest.mark.skipif(
    _MODULES_MISSING,
    reason="pipeline/avatar.py or server/avatar_jobs.py not yet written",
)

if not _MODULES_MISSING:
    from fastapi.testclient import TestClient
    import server.app as app_module
    import server.supa as supa_module
    from server.avatar_jobs import AvatarJobStore


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ALICE_TOKEN = "testtoken-avlist"
_BOB_TOKEN   = "bobtoken-avlist"
_AUTH_HEADER = {"Authorization": f"Bearer {_ALICE_TOKEN}"}

_ALICE_ID = "alice-avlist-000-000000000001"
_BOB_ID   = "bob-avlist-000000-000000000002"
_ALICE_USER = {"id": _ALICE_ID, "email": "alice-avlist@example.com"}
_BOB_USER   = {"id": _BOB_ID,   "email": "bob-avlist@example.com"}


# ---------------------------------------------------------------------------
# Fake supa
# ---------------------------------------------------------------------------

class FakeSupaAvatarList:
    def __init__(self):
        self._tokens = {_ALICE_TOKEN: _ALICE_USER, _BOB_TOKEN: _BOB_USER}
        self._avatar_rows: list[dict] = []  # ordered insertion list
        self._limits: dict[str, int] = {}
        self._counter = 0

    def verify_token(self, token: str) -> dict | None:
        return self._tokens.get(token)

    def count_user_avatars(self, user_id: str) -> int:
        return sum(1 for r in self._avatar_rows if r.get("user_id") == user_id)

    def get_avatar_limit(self, user_id: str) -> int:
        return self._limits.get(user_id, 10)

    def insert_avatar(self, record: dict) -> dict:
        self._counter += 1
        row = dict(record)
        row.setdefault("created_at", f"2024-01-01T00:00:{self._counter:02d}Z")
        self._avatar_rows.append(row)
        return row

    def update_avatar(self, job: str, fields: dict) -> None:
        for r in self._avatar_rows:
            if r.get("job") == job:
                r.update(fields)

    def get_avatar_by_job(self, job: str) -> dict | None:
        for r in self._avatar_rows:
            if r.get("job") == job:
                return r
        return None

    def latest_done_for_user(self, user_id: str) -> dict | None:
        done = [r for r in self._avatar_rows
                if r.get("user_id") == user_id and r.get("status") == "done"]
        return max(done, key=lambda r: r.get("created_at", "")) if done else None

    def latest_avatar_for_user(self, user_id: str) -> dict | None:
        rows = [r for r in self._avatar_rows if r.get("user_id") == user_id]
        return max(rows, key=lambda r: r.get("created_at", "")) if rows else None

    def insert_checkin(self, record: dict) -> dict:
        return record

    def list_checkins(self, user_id: str, limit: int = 12) -> list:
        return []

    def update_checkin(self, checkin_id: str, fields: dict) -> None:
        pass

    def get_profile(self, user_id: str) -> dict | None:
        return None

    def update_profile(self, user_id: str, fields: dict) -> None:
        pass

    def insert_workout_log(self, record: dict) -> dict:
        return record

    def list_workout_logs(self, user_id: str, since_iso=None, limit: int = 60) -> list:
        return []

    def delete_workout_log(self, log_id: str, user_id: str) -> bool:
        return False

    def list_avatars_for_user(self, user_id: str, limit: int = 50) -> list:
        rows = [r for r in self._avatar_rows
                if r.get("user_id") == user_id and r.get("status") != "failed"]
        rows.sort(key=lambda r: r.get("created_at", ""), reverse=True)
        return rows[:limit]


def _patch_supa(monkeypatch, fs) -> None:
    monkeypatch.setattr(supa_module, "verify_token",           fs.verify_token)
    monkeypatch.setattr(supa_module, "count_user_avatars",     fs.count_user_avatars)
    monkeypatch.setattr(supa_module, "get_avatar_limit",       fs.get_avatar_limit)
    monkeypatch.setattr(supa_module, "insert_avatar",          fs.insert_avatar)
    monkeypatch.setattr(supa_module, "update_avatar",          fs.update_avatar)
    monkeypatch.setattr(supa_module, "get_avatar_by_job",      fs.get_avatar_by_job)
    monkeypatch.setattr(supa_module, "latest_done_for_user",   fs.latest_done_for_user)
    monkeypatch.setattr(supa_module, "latest_avatar_for_user", fs.latest_avatar_for_user)
    monkeypatch.setattr(supa_module, "insert_checkin",         fs.insert_checkin)
    monkeypatch.setattr(supa_module, "list_checkins",          fs.list_checkins)
    monkeypatch.setattr(supa_module, "update_checkin",         fs.update_checkin)
    monkeypatch.setattr(supa_module, "get_profile",            fs.get_profile)
    monkeypatch.setattr(supa_module, "update_profile",         fs.update_profile)
    monkeypatch.setattr(supa_module, "insert_workout_log",     fs.insert_workout_log)
    monkeypatch.setattr(supa_module, "list_workout_logs",      fs.list_workout_logs)
    monkeypatch.setattr(supa_module, "delete_workout_log",     fs.delete_workout_log)
    monkeypatch.setattr(supa_module, "list_avatars_for_user",  fs.list_avatars_for_user)


@pytest.fixture()
def fake_supa():
    return FakeSupaAvatarList()


@pytest.fixture()
def client(monkeypatch, tmp_path, fake_supa):
    real_store = AvatarJobStore(tmp_path / "media", tmp_path / "private")
    monkeypatch.setattr(app_module, "_job_store", real_store)
    _patch_supa(monkeypatch, fake_supa)
    return TestClient(app_module.app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# 401 — no token
# ---------------------------------------------------------------------------

def test_get_avatars_no_token_401(client):
    resp = client.get("/avatars")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Empty list
# ---------------------------------------------------------------------------

def test_get_avatars_empty(client):
    resp = client.get("/avatars", headers=_AUTH_HEADER)
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"avatars": []}


# ---------------------------------------------------------------------------
# Newest-first ordering
# ---------------------------------------------------------------------------

def test_get_avatars_newest_first(client, fake_supa):
    fake_supa._avatar_rows.extend([
        {
            "user_id": _ALICE_ID, "job": "job-old", "status": "done",
            "after_url": None, "created_at": "2024-01-01T00:00:01Z",
            "projection": None, "inputs": {"weight_lb": "180", "bf_pct": "18"},
        },
        {
            "user_id": _ALICE_ID, "job": "job-new", "status": "done",
            "after_url": None, "created_at": "2024-06-01T00:00:01Z",
            "projection": None, "inputs": {"weight_lb": "175", "bf_pct": "15"},
        },
    ])

    resp = client.get("/avatars", headers=_AUTH_HEADER)
    assert resp.status_code == 200
    avatars = resp.json()["avatars"]
    assert len(avatars) == 2
    assert avatars[0]["job"] == "job-new"
    assert avatars[1]["job"] == "job-old"


# ---------------------------------------------------------------------------
# Failed avatars excluded; in-progress included
# ---------------------------------------------------------------------------

def test_get_avatars_failed_excluded(client, fake_supa):
    fake_supa._avatar_rows.extend([
        {
            "user_id": _ALICE_ID, "job": "job-done", "status": "done",
            "after_url": "https://store/after.jpg", "created_at": "2024-02-01T00:00:01Z",
            "projection": None, "inputs": {},
        },
        {
            "user_id": _ALICE_ID, "job": "job-failed", "status": "failed",
            "after_url": None, "created_at": "2024-03-01T00:00:01Z",
            "projection": None, "inputs": {},
        },
        {
            "user_id": _ALICE_ID, "job": "job-progress", "status": "processing",
            "after_url": None, "created_at": "2024-04-01T00:00:01Z",
            "projection": None, "inputs": {},
        },
    ])

    resp = client.get("/avatars", headers=_AUTH_HEADER)
    assert resp.status_code == 200
    avatars = resp.json()["avatars"]
    jobs = [a["job"] for a in avatars]
    assert "job-failed" not in jobs
    assert "job-done" in jobs
    assert "job-progress" in jobs


# ---------------------------------------------------------------------------
# Float parsing from string inputs
# ---------------------------------------------------------------------------

def test_get_avatars_float_parsing(client, fake_supa):
    fake_supa._avatar_rows.append({
        "user_id": _ALICE_ID, "job": "job-floats", "status": "done",
        "after_url": None, "created_at": "2024-05-01T00:00:01Z",
        "projection": {"weight_after_lb": 178.5, "bf_after": 12.3, "months": 6, "direction": "cut"},
        "inputs": {"weight_lb": "185.5", "bf_pct": "20.0"},
    })

    resp = client.get("/avatars", headers=_AUTH_HEADER)
    assert resp.status_code == 200
    av = resp.json()["avatars"][0]
    assert av["weight_lb"] == pytest.approx(185.5)
    assert av["bf_pct"] == pytest.approx(20.0)


def test_get_avatars_float_null_on_parse_failure(client, fake_supa):
    fake_supa._avatar_rows.append({
        "user_id": _ALICE_ID, "job": "job-badparse", "status": "done",
        "after_url": None, "created_at": "2024-05-01T00:00:01Z",
        "projection": None,
        "inputs": {"weight_lb": "not-a-number", "bf_pct": ""},
    })

    resp = client.get("/avatars", headers=_AUTH_HEADER)
    av = resp.json()["avatars"][0]
    assert av["weight_lb"] is None
    assert av["bf_pct"] is None


# ---------------------------------------------------------------------------
# Foreign rows never appear
# ---------------------------------------------------------------------------

def test_get_avatars_foreign_rows_excluded(client, fake_supa):
    fake_supa._avatar_rows.extend([
        {
            "user_id": _ALICE_ID, "job": "alice-job", "status": "done",
            "after_url": None, "created_at": "2024-05-01T00:00:01Z",
            "projection": None, "inputs": {},
        },
        {
            "user_id": _BOB_ID, "job": "bob-job", "status": "done",
            "after_url": None, "created_at": "2024-05-02T00:00:01Z",
            "projection": None, "inputs": {},
        },
    ])

    resp = client.get("/avatars", headers=_AUTH_HEADER)
    avatars = resp.json()["avatars"]
    jobs = [a["job"] for a in avatars]
    assert "alice-job" in jobs
    assert "bob-job" not in jobs


# ---------------------------------------------------------------------------
# Projection subset exposed correctly
# ---------------------------------------------------------------------------

def test_get_avatars_projection_subset(client, fake_supa):
    proj = {
        "weight_after_lb": 178.0,
        "bf_after": 12.5,
        "months": 4,
        "direction": "cut",
        "confidence_score": 0.85,  # not in the subset
    }
    fake_supa._avatar_rows.append({
        "user_id": _ALICE_ID, "job": "job-proj", "status": "done",
        "after_url": "https://store/after.jpg", "created_at": "2024-05-01T00:00:01Z",
        "projection": proj, "inputs": {},
    })

    resp = client.get("/avatars", headers=_AUTH_HEADER)
    av = resp.json()["avatars"][0]
    p = av["projection"]
    assert p is not None
    assert "weight_after_lb" in p
    assert "bf_after" in p
    assert "months" in p
    assert "direction" in p
    # confidence_score is NOT in the subset
    assert "confidence_score" not in p
