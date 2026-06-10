"""Tests for POST /progress and GET /progress (tamagotchi evolution loop).

Pattern: FakeSupaProgress extends the existing FakeSupa style — all state in
plain dicts, no network calls. AVATAR_STAGES_FACTORY is patched to the fast
fake so a triggered re-bake completes without fal.

Test matrix:
  - 401 without token (both routes)
  - 409 when no avatar exists yet
  - check-in that doesn't move projection -> rebake_triggered False
  - check-in that moves projection past threshold + past cooldown -> rebake_triggered True,
    new avatar job exists, rebakes_used incremented
  - cooldown blocks a 2nd re-bake (avatar just created)
  - REBAKE_CAP blocks when rebakes_used >= REBAKE_CAP
  - streak increments on a recent prior check-in
  - streak resets after a >10-day gap
  - GET /progress shape
"""
from __future__ import annotations

import io
import json
import pathlib
import sys
from datetime import datetime, timedelta, timezone

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

# Guard: skip if Agent A modules missing (same pattern as test_avatar_routes.py)
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
    import numpy as np
    from fastapi.testclient import TestClient
    from PIL import Image

    import server.app as app_module
    import server.supa as supa_module
    from pipeline.avatar import AvatarResult, AvatarStages
    from server.avatar_jobs import AvatarJobStore


# ---------------------------------------------------------------------------
# Constants (mirrors test_avatar_routes.py)
# ---------------------------------------------------------------------------

_TEST_TOKEN = "testtoken-progress"
_AUTH_HEADER = {"Authorization": f"Bearer {_TEST_TOKEN}"}
_ALICE_ID = "alice-progress-0000-000000000001"
_ALICE_USER = {"id": _ALICE_ID, "email": "alice-progress@example.com"}

_BASE_INPUTS = dict(
    age="28", sex="M", height_in="70", weight_lb="185",
    bf_pct="15", goal="fat_loss", weeks="16",
)

# A projection that clearly differs from the base by >2 lb and >1% bf.
_SHIFTED_INPUTS = dict(
    age="28", sex="M", height_in="70", weight_lb="175",  # -10 lb
    bf_pct="12",                                          # -3 %
    goal="fat_loss", weeks="16",
)


# ---------------------------------------------------------------------------
# Fake stages (identical style to test_avatar_routes.py)
# ---------------------------------------------------------------------------

def _make_fake_stages(tmp_path: pathlib.Path):
    def still(photo_path: str, spec) -> "np.ndarray":
        return np.zeros((4, 4, 3), dtype=np.uint8)

    def orbit(after_jpg_path: str) -> str:
        mp4 = tmp_path / "orbit.mp4"
        mp4.write_bytes(b"\x00" * 8)
        return str(mp4)

    def matte(orbit_mp4_path: str) -> str:
        webm = tmp_path / "master.webm"
        webm.write_bytes(b"\x00" * 8)
        return str(webm)

    def extract(webm_path: str, n: int) -> int:
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir(exist_ok=True)
        frames_mobile = tmp_path / "frames_mobile"
        frames_mobile.mkdir(exist_ok=True)
        count = min(n, 4)
        for i in range(count):
            name = f"f{i:03d}"
            img = Image.new("RGBA", (4, 4))
            img.save(frames_dir / f"{name}.png")
            img.save(frames_mobile / f"{name}.webp", format="WEBP")
        return count

    return AvatarStages(still=still, orbit=orbit, matte=matte, extract=extract)


# ---------------------------------------------------------------------------
# Extended FakeSupa — adds checkins, profile, latest_avatar_for_user, update_checkin
# ---------------------------------------------------------------------------

class FakeSupaProgress:
    """In-memory supa double for progress tests."""

    def __init__(self):
        # avatar rows keyed by job
        self._avatars: dict[str, dict] = {}
        # checkin rows keyed by id (uuid str)
        self._checkins: dict[str, dict] = {}
        # profile rows keyed by user_id
        self._profiles: dict[str, dict] = {}
        self._limits: dict[str, int] = {}
        self._tokens: dict[str, dict] = {_TEST_TOKEN: _ALICE_USER}
        self._counter = 0

    # ── helpers ──────────────────────────────────────────────────────────────
    def _next_ts(self) -> str:
        self._counter += 1
        return f"2025-01-01T00:00:{self._counter:02d}Z"

    # ── token ────────────────────────────────────────────────────────────────
    def verify_token(self, token: str) -> dict | None:
        return self._tokens.get(token)

    # ── avatars ──────────────────────────────────────────────────────────────
    def count_user_avatars(self, user_id: str) -> int:
        return sum(1 for r in self._avatars.values() if r.get("user_id") == user_id)

    def get_avatar_limit(self, user_id: str) -> int:
        return self._limits.get(user_id, 100)  # generous default for progress tests

    def insert_avatar(self, record: dict) -> dict:
        self._counter += 1
        row = dict(record)
        row.setdefault("created_at", self._next_ts())
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

    # ── checkins ─────────────────────────────────────────────────────────────
    def insert_checkin(self, record: dict) -> dict:
        import uuid
        row = dict(record)
        row.setdefault("id", str(uuid.uuid4()))
        row.setdefault("created_at", self._next_ts())
        self._checkins[row["id"]] = row
        return row

    def list_checkins(self, user_id: str, limit: int = 12) -> list:
        rows = [r for r in self._checkins.values() if r.get("user_id") == user_id]
        rows.sort(key=lambda r: r.get("created_at", ""), reverse=True)
        return rows[:limit]

    def update_checkin(self, checkin_id: str, fields: dict) -> None:
        if checkin_id in self._checkins:
            self._checkins[checkin_id].update(fields)

    # ── profiles ─────────────────────────────────────────────────────────────
    def get_profile(self, user_id: str) -> dict | None:
        return self._profiles.get(user_id)

    def update_profile(self, user_id: str, fields: dict) -> None:
        if user_id not in self._profiles:
            self._profiles[user_id] = {"id": user_id}
        self._profiles[user_id].update(fields)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _patch_supa(monkeypatch, fs: FakeSupaProgress) -> None:
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


@pytest.fixture()
def store_root(tmp_path: pathlib.Path):
    return tmp_path


@pytest.fixture()
def fake_supa() -> FakeSupaProgress:
    return FakeSupaProgress()


@pytest.fixture()
def client(monkeypatch, store_root, fake_supa):
    real_store = AvatarJobStore(store_root / "media", store_root / "private")
    monkeypatch.setattr(app_module, "_job_store", real_store)

    def fake_factory(out_dir: pathlib.Path) -> AvatarStages:
        return _make_fake_stages(out_dir)

    monkeypatch.setattr(app_module, "AVATAR_STAGES_FACTORY", fake_factory)
    _patch_supa(monkeypatch, fake_supa)
    return TestClient(app_module.app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tiny_jpeg_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (1, 1), color=(200, 200, 200)).save(buf, format="JPEG")
    return buf.getvalue()


def _create_avatar(client, inputs: dict | None = None) -> str:
    """POST /avatar and return the job id. Backgrounds run synchronously."""
    data = dict(_BASE_INPUTS, **(inputs or {}))
    resp = client.post(
        "/avatar",
        data=data,
        files={"photo": ("photo.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
        headers=_AUTH_HEADER,
    )
    assert resp.status_code == 202, resp.text
    return resp.json()["job"]


def _post_progress(client, **body_overrides) -> dict:
    """POST /progress with default body and return parsed JSON."""
    body = {"workouts_done": 3}
    body.update(body_overrides)
    resp = client.post("/progress", json=body, headers=_AUTH_HEADER)
    return resp


# ---------------------------------------------------------------------------
# Auth tests
# ---------------------------------------------------------------------------

def test_post_progress_no_token_401(client):
    resp = client.post("/progress", json={"workouts_done": 0})
    assert resp.status_code == 401


def test_get_progress_no_token_401(client):
    resp = client.get("/progress")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 409 when no avatar exists
# ---------------------------------------------------------------------------

def test_post_progress_no_avatar_409(client):
    resp = _post_progress(client)
    assert resp.status_code == 409
    assert "avatar" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Check-in that doesn't shift projection -> rebake_triggered False
# ---------------------------------------------------------------------------

def test_checkin_no_shift_no_rebake(client, fake_supa, store_root, monkeypatch):
    # Age the avatar so cooldown is satisfied, but the inputs are identical
    # so the projection won't shift past the threshold.
    job = _create_avatar(client)
    # Age the avatar by backdating its created_at in the fake store.
    old_ts = "2020-01-01T00:00:00+00:00"
    fake_supa._avatars[job]["created_at"] = old_ts

    resp = _post_progress(client)
    assert resp.status_code == 200
    body = resp.json()
    assert body["rebake_triggered"] is False
    assert body["rebake_recommended"] is False
    assert isinstance(body["reasons"], list)
    assert body["streak_weeks"] == 1
    assert body["state"] in ("on_track", "ahead", "behind")
    assert "projection" in body
    assert "baked_projection" in body


# ---------------------------------------------------------------------------
# Check-in that moves projection past threshold + past cooldown -> rebake_triggered True
# ---------------------------------------------------------------------------

def test_checkin_shift_past_cooldown_triggers_rebake(client, fake_supa, store_root):
    job = _create_avatar(client)
    # Age the avatar well past cooldown.
    old_ts = "2020-01-01T00:00:00+00:00"
    fake_supa._avatars[job]["created_at"] = old_ts

    # Shift inputs enough: weight -10 lb, bf -3%.
    resp = _post_progress(client, weight_lb=175.0, bf_pct=12.0)
    assert resp.status_code == 200
    body = resp.json()

    assert body["rebake_triggered"] is True
    assert body["rebake_recommended"] is True
    assert body["rebake_job"] is not None
    assert body["state"] == "evolving"

    # A new avatar job must exist in the fake store.
    new_job = body["rebake_job"]
    assert new_job in fake_supa._avatars
    assert fake_supa._avatars[new_job]["user_id"] == _ALICE_ID

    # rebakes_used must have been incremented.
    prof = fake_supa._profiles.get(_ALICE_ID, {})
    assert (prof.get("rebakes_used") or 0) == 1


# ---------------------------------------------------------------------------
# Cooldown blocks a 2nd re-bake (avatar just created — within 5 days)
# ---------------------------------------------------------------------------

def test_checkin_within_cooldown_blocks_rebake(client, fake_supa):
    # Avatar was just created — mark its created_at as 1 day ago (within 5-day cooldown).
    job = _create_avatar(client)
    one_day_ago = (
        datetime.now(timezone.utc) - timedelta(days=1)
    ).isoformat()
    fake_supa._avatars[job]["created_at"] = one_day_ago

    resp = _post_progress(client, weight_lb=175.0, bf_pct=12.0)
    assert resp.status_code == 200
    body = resp.json()

    # rebake may be recommended but should NOT be triggered due to cooldown.
    assert body["rebake_triggered"] is False
    assert body["rebake_job"] is None


# ---------------------------------------------------------------------------
# REBAKE_CAP blocks when rebakes_used >= cap
# ---------------------------------------------------------------------------

def test_rebake_cap_blocks(client, fake_supa, monkeypatch):
    job = _create_avatar(client)
    # Age the avatar past cooldown.
    fake_supa._avatars[job]["created_at"] = "2020-01-01T00:00:00+00:00"

    # Simulate the user already having used the full cap.
    fake_supa._profiles[_ALICE_ID] = {
        "id": _ALICE_ID,
        "rebakes_used": app_module.REBAKE_CAP,
    }

    resp = _post_progress(client, weight_lb=175.0, bf_pct=12.0)
    assert resp.status_code == 200
    body = resp.json()
    assert body["rebake_triggered"] is False
    assert body["rebake_job"] is None


# ---------------------------------------------------------------------------
# Streak increments on recent prior check-in
# ---------------------------------------------------------------------------

def test_streak_increments_on_recent_checkin(client, fake_supa):
    _create_avatar(client)
    # Seed profile with a prior check-in 3 days ago (within 10-day window).
    three_days_ago = (
        datetime.now(timezone.utc) - timedelta(days=3)
    ).isoformat()
    fake_supa._profiles[_ALICE_ID] = {
        "id": _ALICE_ID,
        "streak_weeks": 4,
        "last_checkin_at": three_days_ago,
    }

    resp = _post_progress(client)
    assert resp.status_code == 200
    body = resp.json()
    assert body["streak_weeks"] == 5


# ---------------------------------------------------------------------------
# Streak resets after a >10-day gap
# ---------------------------------------------------------------------------

def test_streak_resets_after_gap(client, fake_supa):
    _create_avatar(client)
    # Last check-in was 15 days ago.
    fifteen_days_ago = (
        datetime.now(timezone.utc) - timedelta(days=15)
    ).isoformat()
    fake_supa._profiles[_ALICE_ID] = {
        "id": _ALICE_ID,
        "streak_weeks": 10,
        "last_checkin_at": fifteen_days_ago,
    }

    resp = _post_progress(client)
    assert resp.status_code == 200
    body = resp.json()
    assert body["streak_weeks"] == 1


# ---------------------------------------------------------------------------
# GET /progress shape
# ---------------------------------------------------------------------------

def test_get_progress_shape(client, fake_supa):
    _create_avatar(client)
    # Log a check-in first so there's data.
    _post_progress(client)

    resp = client.get("/progress", headers=_AUTH_HEADER)
    assert resp.status_code == 200
    body = resp.json()

    for key in ("streak_weeks", "last_checkin_at", "current_weight_lb",
                "current_bf_pct", "rebakes_used", "checkins", "latest_avatar"):
        assert key in body, f"missing key: {key}"

    assert isinstance(body["checkins"], list)
    assert len(body["checkins"]) >= 1

    av = body["latest_avatar"]
    assert av is not None
    assert "job" in av
    assert "status" in av


def test_get_progress_no_avatar_returns_empty(client):
    resp = client.get("/progress", headers=_AUTH_HEADER)
    assert resp.status_code == 200
    body = resp.json()
    assert body["streak_weeks"] == 0
    assert body["checkins"] == []
    assert body["latest_avatar"] is None
