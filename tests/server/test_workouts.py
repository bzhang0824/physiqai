"""Tests for POST /workouts and DELETE /workouts/{log_id}.

TDD spec:
  - 401 without token (both routes)
  - first POST -> row created, week_count=1, week_days[6] is True (today)
  - same-UTC-day second POST -> already_logged=true, no new row
  - DELETE own log -> 200 {deleted: true, week_count}
  - DELETE foreign log -> 404
  - DELETE unknown log -> 404
  - backdated rows do NOT contribute to the 7-day window
  - ENGINE-FREE: no avatar rows created by these endpoints
"""
from __future__ import annotations

import pathlib
import sys
import uuid
from datetime import datetime, timedelta, timezone

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

# Guard: skip if Agent A pipeline modules are missing
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
    from PIL import Image
    import io

    import server.app as app_module
    import server.supa as supa_module
    from server.avatar_jobs import AvatarJobStore


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TEST_TOKEN = "testtoken-workouts"
_AUTH_HEADER = {"Authorization": f"Bearer {_TEST_TOKEN}"}
_BOB_TOKEN = "bobtoken-workouts"

_ALICE_ID = "alice-workouts-000-000000000001"
_BOB_ID   = "bob-workouts-00000-000000000002"
_ALICE_USER = {"id": _ALICE_ID, "email": "alice-workouts@example.com"}
_BOB_USER   = {"id": _BOB_ID,   "email": "bob-workouts@example.com"}


# ---------------------------------------------------------------------------
# In-memory fakes
# ---------------------------------------------------------------------------

class FakeSupaWorkouts:
    """Minimal supa double covering only what workout routes touch."""

    def __init__(self):
        self._tokens = {_TEST_TOKEN: _ALICE_USER, _BOB_TOKEN: _BOB_USER}
        self._avatars: dict[str, dict] = {}
        self._logs: dict[str, dict] = {}  # id -> row
        self._limits: dict[str, int] = {}
        self._counter = 0

    # ── token ────────────────────────────────────────────────────────────────
    def verify_token(self, token: str) -> dict | None:
        return self._tokens.get(token)

    # ── avatars (needed so the app boots cleanly) ────────────────────────────
    def count_user_avatars(self, user_id: str) -> int:
        return sum(1 for r in self._avatars.values() if r.get("user_id") == user_id)

    def get_avatar_limit(self, user_id: str) -> int:
        return self._limits.get(user_id, 10)

    def insert_avatar(self, record: dict) -> dict:
        self._counter += 1
        row = dict(record)
        row.setdefault("created_at", f"2024-01-01T00:00:{self._counter:02d}Z")
        self._avatars[record["job"]] = row
        return row

    def update_avatar(self, job: str, fields: dict) -> None:
        if job in self._avatars:
            self._avatars[job].update(fields)

    def get_avatar_by_job(self, job: str) -> dict | None:
        return self._avatars.get(job)

    def latest_done_for_user(self, user_id: str) -> dict | None:
        done = [r for r in self._avatars.values()
                if r.get("user_id") == user_id and r.get("status") == "done"]
        return max(done, key=lambda r: r.get("created_at", "")) if done else None

    def latest_avatar_for_user(self, user_id: str) -> dict | None:
        rows = [r for r in self._avatars.values() if r.get("user_id") == user_id]
        return max(rows, key=lambda r: r.get("created_at", "")) if rows else None

    # ── checkins (stubs — workouts never touch these) ────────────────────────
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

    # ── workout logs ─────────────────────────────────────────────────────────
    def insert_workout_log(self, record: dict) -> dict:
        row = dict(record)
        row.setdefault("id", str(uuid.uuid4()))
        row.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        self._logs[row["id"]] = row
        return row

    def list_workout_logs(self, user_id: str, since_iso=None, limit: int = 60) -> list:
        rows = [r for r in self._logs.values() if r.get("user_id") == user_id]
        if since_iso:
            rows = [r for r in rows if r.get("created_at", "") >= since_iso]
        rows.sort(key=lambda r: r.get("created_at", ""), reverse=True)
        return rows[:limit]

    def delete_workout_log(self, log_id: str, user_id: str) -> bool:
        row = self._logs.get(log_id)
        if row is None or row.get("user_id") != user_id:
            return False
        del self._logs[log_id]
        return True

    # ── avatars listing ──────────────────────────────────────────────────────
    def list_avatars_for_user(self, user_id: str, limit: int = 50) -> list:
        rows = [r for r in self._avatars.values()
                if r.get("user_id") == user_id and r.get("status") != "failed"]
        rows.sort(key=lambda r: r.get("created_at", ""), reverse=True)
        return rows[:limit]


def _patch_supa(monkeypatch, fs: FakeSupaWorkouts) -> None:
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


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def fake_supa() -> FakeSupaWorkouts:
    return FakeSupaWorkouts()


@pytest.fixture()
def client(monkeypatch, tmp_path, fake_supa):
    real_store = AvatarJobStore(tmp_path / "media", tmp_path / "private")
    monkeypatch.setattr(app_module, "_job_store", real_store)
    _patch_supa(monkeypatch, fake_supa)
    return TestClient(app_module.app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def test_post_workouts_no_token_401(client):
    resp = client.post("/workouts", json={})
    assert resp.status_code == 401


def test_delete_workouts_no_token_401(client):
    resp = client.delete("/workouts/some-log-id")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /workouts — first log of the day
# ---------------------------------------------------------------------------

def test_post_workouts_first_log(client, fake_supa):
    resp = client.post("/workouts", json={}, headers=_AUTH_HEADER)
    assert resp.status_code == 200
    body = resp.json()

    assert body["already_logged"] is False
    assert body["week_count"] == 1
    assert "id" in body
    assert "created_at" in body

    # week_days is a list of 7 booleans, oldest->today; today (index 6) must be True
    week_days = body["week_days"]
    assert isinstance(week_days, list)
    assert len(week_days) == 7
    assert week_days[6] is True  # today
    assert sum(week_days) == 1   # only today logged

    # The row must actually exist in the fake store
    assert len(fake_supa._logs) == 1
    row = next(iter(fake_supa._logs.values()))
    assert row["user_id"] == _ALICE_ID


def test_post_workouts_with_note(client, fake_supa):
    resp = client.post("/workouts", json={"note": "Heavy squat day"}, headers=_AUTH_HEADER)
    assert resp.status_code == 200
    row = next(iter(fake_supa._logs.values()))
    assert row.get("note") == "Heavy squat day"


# ---------------------------------------------------------------------------
# POST /workouts — idempotent same-UTC-day second call
# ---------------------------------------------------------------------------

def test_post_workouts_same_day_idempotent(client, fake_supa):
    resp1 = client.post("/workouts", json={}, headers=_AUTH_HEADER)
    assert resp1.status_code == 200
    first_id = resp1.json()["id"]

    resp2 = client.post("/workouts", json={"note": "ignored"}, headers=_AUTH_HEADER)
    assert resp2.status_code == 200
    body2 = resp2.json()

    assert body2["already_logged"] is True
    assert body2["id"] == first_id           # same row returned
    assert body2["week_count"] == 1          # still 1 — no dupe inserted
    assert len(fake_supa._logs) == 1         # only one row in the store


# ---------------------------------------------------------------------------
# DELETE /workouts/{log_id}
# ---------------------------------------------------------------------------

def test_delete_own_log(client, fake_supa):
    post_resp = client.post("/workouts", json={}, headers=_AUTH_HEADER)
    log_id = post_resp.json()["id"]

    del_resp = client.delete(f"/workouts/{log_id}", headers=_AUTH_HEADER)
    assert del_resp.status_code == 200
    body = del_resp.json()
    assert body["deleted"] is True
    assert "week_count" in body
    assert body["week_count"] == 0  # now zero after deletion


def test_delete_nonexistent_log_404(client):
    resp = client.delete("/workouts/no-such-id", headers=_AUTH_HEADER)
    assert resp.status_code == 404


def test_delete_foreign_log_404(client, fake_supa):
    """Alice creates a log; Bob tries to delete it — should get 404 (not 403)."""
    post_resp = client.post("/workouts", json={}, headers=_AUTH_HEADER)
    log_id = post_resp.json()["id"]

    resp = client.delete(
        f"/workouts/{log_id}",
        headers={"Authorization": f"Bearer {_BOB_TOKEN}"},
    )
    assert resp.status_code == 404
    # Alice's log must still exist
    assert log_id in fake_supa._logs


# ---------------------------------------------------------------------------
# 7-day window: backdated logs roll out
# ---------------------------------------------------------------------------

def test_backdated_logs_outside_window_not_counted(client, fake_supa):
    """A log from 8 days ago must NOT appear in week_count."""
    # Manually insert a backdated row into the fake store
    old_ts = (datetime.now(timezone.utc) - timedelta(days=8)).isoformat()
    old_id = str(uuid.uuid4())
    fake_supa._logs[old_id] = {
        "id": old_id,
        "user_id": _ALICE_ID,
        "created_at": old_ts,
    }

    resp = client.post("/workouts", json={}, headers=_AUTH_HEADER)
    assert resp.status_code == 200
    body = resp.json()

    # Only today's log should count
    assert body["week_count"] == 1
    assert sum(body["week_days"]) == 1


# ---------------------------------------------------------------------------
# ENGINE-FREE: workout routes must never create avatar rows
# ---------------------------------------------------------------------------

def test_post_workouts_no_avatar_side_effects(client, fake_supa):
    client.post("/workouts", json={}, headers=_AUTH_HEADER)
    assert len(fake_supa._avatars) == 0


def test_delete_workouts_no_avatar_side_effects(client, fake_supa):
    post_resp = client.post("/workouts", json={}, headers=_AUTH_HEADER)
    log_id = post_resp.json()["id"]
    client.delete(f"/workouts/{log_id}", headers=_AUTH_HEADER)
    assert len(fake_supa._avatars) == 0


def test_get_progress_degrades_when_workout_table_missing(client, fake_supa, monkeypatch):
    """Deploy-ordering insurance: if the workout_logs table doesn't exist yet
    (migration not applied), GET /progress must still return 200 with
    workouts=null instead of 500ing the whole dashboard."""
    import server.supa as supa_module

    def boom(*a, **k):
        raise RuntimeError("relation workout_logs does not exist")

    monkeypatch.setattr(supa_module, "list_workout_logs", boom)
    resp = client.get("/progress", headers=_AUTH_HEADER)
    assert resp.status_code == 200, resp.text
    assert resp.json()["workouts"] is None
