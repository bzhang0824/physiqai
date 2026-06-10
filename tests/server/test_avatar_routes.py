"""Tests for POST /avatar, GET /avatar/{job}, GET /avatar/latest, POST /avatar/refresh.

Fakes for pipeline.avatar stages are injected via monkeypatch so no fal.ai calls happen.
BackgroundTasks run synchronously under FastAPI TestClient — tests rely on that.
All Supabase calls are monkeypatched — no network traffic.

If Agent A's modules (pipeline.avatar, server.avatar_jobs) are not yet present on disk,
the entire module is skipped gracefully with a clear message.
"""
from __future__ import annotations

import io
import json
import pathlib
import sys

import pytest

# ── guard: skip if Agent A's modules aren't written yet ─────────────────────
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
try:
    import pipeline.avatar  # noqa: F401
    import server.avatar_jobs  # noqa: F401
    _AGENT_A_MISSING = False
except ImportError:
    _AGENT_A_MISSING = True

pytestmark = pytest.mark.skipif(
    _AGENT_A_MISSING,
    reason="Agent A's pipeline/avatar.py or server/avatar_jobs.py not yet written",
)

# ── real imports (only reached when modules exist) ───────────────────────────
if not _AGENT_A_MISSING:
    from dataclasses import dataclass
    from typing import Callable

    import numpy as np
    from fastapi.testclient import TestClient
    from PIL import Image

    import server.app as app_module
    import server.supa as supa_module
    from pipeline.avatar import AvatarResult, AvatarStages
    from server.avatar_jobs import AvatarJobStore


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TEST_TOKEN = "testtoken"
_AUTH_HEADER = {"Authorization": f"Bearer {_TEST_TOKEN}"}

_ALICE_ID = "alice-uuid-0000-0000-000000000001"
_BOB_ID   = "bob-uuid-0000-0000-000000000002"

_ALICE_USER = {"id": _ALICE_ID, "email": "alice@example.com"}
_BOB_USER   = {"id": _BOB_ID,   "email": "bob@example.com"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tiny_jpeg_bytes() -> bytes:
    """1×1 white JPEG in memory."""
    buf = io.BytesIO()
    Image.new("RGB", (1, 1), color=(255, 255, 255)).save(buf, format="JPEG")
    return buf.getvalue()


def _base_form(**extra):
    """Minimal valid form fields for POST /avatar."""
    data = dict(
        age="24", sex="M", height_in="72", weight_lb="192",
        bf_pct="11", goal="fat_loss", weeks="26",
    )
    data.update(extra)
    return data


def _make_fake_stages(tmp_path: pathlib.Path, *, fail_at: str | None = None):
    """Return an AvatarStages whose callables write tiny real files and return fast."""

    def still(photo_path: str, spec) -> "np.ndarray":
        if fail_at == "still":
            raise RuntimeError("still stage failed")
        return np.zeros((4, 4, 3), dtype=np.uint8)

    def orbit(after_jpg_path: str) -> str:
        if fail_at == "orbit":
            raise RuntimeError("orbit stage failed")
        mp4 = tmp_path / "orbit.mp4"
        mp4.write_bytes(b"\x00" * 8)
        return str(mp4)

    def matte(orbit_mp4_path: str) -> str:
        if fail_at == "matte":
            raise RuntimeError("matte stage failed")
        webm = tmp_path / "master.webm"
        webm.write_bytes(b"\x00" * 8)
        return str(webm)

    def extract(webm_path: str, n: int) -> int:
        if fail_at == "extract":
            raise RuntimeError("extract stage failed")
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
# In-memory Supabase fakes
# ---------------------------------------------------------------------------

class FakeSupa:
    """All state lives in a plain dict; no HTTP calls."""

    def __init__(self):
        # job -> row dict (insertion order preserved in Python 3.7+)
        self._rows: dict[str, dict] = {}
        # user_id -> avatar_limit
        self._limits: dict[str, int] = {}
        # Which user token maps to which user dict
        self._tokens: dict[str, dict] = {_TEST_TOKEN: _ALICE_USER}
        # Flags to simulate failures
        self.fail_insert = False
        self.fail_count = False
        # Monotonic counter for created_at ordering
        self._counter = 0

    # ── Token verification ───────────────────────────────────────────────────
    def verify_token(self, token: str) -> dict | None:
        return self._tokens.get(token)

    # ── Count / limit ────────────────────────────────────────────────────────
    def count_user_avatars(self, user_id: str) -> int:
        if self.fail_count:
            raise RuntimeError("Supabase down")
        return sum(1 for r in self._rows.values() if r.get("user_id") == user_id)

    def get_avatar_limit(self, user_id: str) -> int:
        return self._limits.get(user_id, 1)

    # ── CRUD ─────────────────────────────────────────────────────────────────
    def insert_avatar(self, record: dict) -> dict:
        if self.fail_insert:
            raise RuntimeError("Supabase down")
        self._counter += 1
        row = dict(record)
        # Ensure monotonically increasing created_at so latest-ordering works
        row.setdefault("created_at", f"2024-01-01T00:00:{self._counter:02d}Z")
        self._rows[record["job"]] = row
        return row

    def update_avatar(self, job: str, fields: dict) -> None:
        if job in self._rows:
            self._rows[job].update(fields)

    def get_avatar_by_job(self, job: str) -> dict | None:
        return self._rows.get(job)

    def latest_done_for_user(self, user_id: str) -> dict | None:
        done = [
            r for r in self._rows.values()
            if r.get("user_id") == user_id and r.get("status") == "done"
        ]
        if not done:
            return None
        return max(done, key=lambda r: r.get("created_at", ""))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def store_root(tmp_path: pathlib.Path):
    return tmp_path


@pytest.fixture()
def fake_supa() -> FakeSupa:
    return FakeSupa()


@pytest.fixture()
def client(monkeypatch, store_root, fake_supa):
    """TestClient with store, stages, and all Supabase calls patched."""
    real_store = AvatarJobStore(store_root / "media", store_root / "private")
    monkeypatch.setattr(app_module, "_job_store", real_store)

    def fake_factory(out_dir: pathlib.Path) -> AvatarStages:
        return _make_fake_stages(out_dir)

    monkeypatch.setattr(app_module, "AVATAR_STAGES_FACTORY", fake_factory)
    _patch_supa(monkeypatch, fake_supa)

    return TestClient(app_module.app, raise_server_exceptions=False)


@pytest.fixture()
def client_fail_orbit(monkeypatch, store_root, fake_supa):
    """Client whose stages raise on the orbit step."""
    real_store = AvatarJobStore(store_root / "media", store_root / "private")
    monkeypatch.setattr(app_module, "_job_store", real_store)

    def fail_factory(out_dir: pathlib.Path) -> AvatarStages:
        return _make_fake_stages(out_dir, fail_at="orbit")

    monkeypatch.setattr(app_module, "AVATAR_STAGES_FACTORY", fail_factory)
    _patch_supa(monkeypatch, fake_supa)

    return TestClient(app_module.app, raise_server_exceptions=False)


def _patch_supa(monkeypatch, fake_supa: FakeSupa) -> None:
    """Wire all supa_module functions to the FakeSupa instance."""
    monkeypatch.setattr(supa_module, "verify_token",        fake_supa.verify_token)
    monkeypatch.setattr(supa_module, "count_user_avatars",  fake_supa.count_user_avatars)
    monkeypatch.setattr(supa_module, "get_avatar_limit",    fake_supa.get_avatar_limit)
    monkeypatch.setattr(supa_module, "insert_avatar",       fake_supa.insert_avatar)
    monkeypatch.setattr(supa_module, "update_avatar",       fake_supa.update_avatar)
    monkeypatch.setattr(supa_module, "get_avatar_by_job",   fake_supa.get_avatar_by_job)
    monkeypatch.setattr(supa_module, "latest_done_for_user", fake_supa.latest_done_for_user)


# ---------------------------------------------------------------------------
# Shared helper: post a done avatar for the default (Alice) user
# ---------------------------------------------------------------------------

def _post_done(client, *, extra_headers: dict | None = None, **form_extra):
    """POST /avatar with auth header, wait for background task to complete."""
    headers = {**_AUTH_HEADER, **(extra_headers or {})}
    resp = client.post(
        "/avatar",
        data=_base_form(**form_extra),
        files={"photo": ("photo.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
        headers=headers,
    )
    assert resp.status_code == 202, resp.text
    return resp.json()["job"]


# ---------------------------------------------------------------------------
# Auth: missing / invalid token
# ---------------------------------------------------------------------------

def test_post_avatar_no_token_401(client):
    resp = client.post(
        "/avatar",
        data=_base_form(),
        files={"photo": ("photo.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
    )
    assert resp.status_code == 401


def test_post_avatar_bad_token_401(client):
    resp = client.post(
        "/avatar",
        data=_base_form(),
        files={"photo": ("photo.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
        headers={"Authorization": "Bearer badtoken"},
    )
    assert resp.status_code == 401


def test_get_avatar_no_token_401(client):
    job = _post_done(client)
    resp = client.get(f"/avatar/{job}")
    assert resp.status_code == 401


def test_get_latest_no_token_401(client):
    resp = client.get("/avatar/latest")
    assert resp.status_code == 401


def test_refresh_no_token_401(client):
    job = _post_done(client)
    resp = client.post("/avatar/refresh", data={**_base_form(), "job": job})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Ownership: someone else's job → 403
# ---------------------------------------------------------------------------

def test_get_other_users_job_403(client, monkeypatch, fake_supa, store_root):
    # Alice creates a job
    job = _post_done(client)

    # Now Bob tries to access it — register Bob's token
    fake_supa._tokens["bobtoken"] = _BOB_USER

    resp = client.get(f"/avatar/{job}", headers={"Authorization": "Bearer bobtoken"})
    assert resp.status_code == 403


def test_refresh_other_users_job_403(client, monkeypatch, fake_supa):
    job = _post_done(client)
    fake_supa._tokens["bobtoken"] = _BOB_USER

    resp = client.post(
        "/avatar/refresh",
        data={**_base_form(), "job": job},
        headers={"Authorization": "Bearer bobtoken"},
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Spend cap: avatar limit reached → 403
# ---------------------------------------------------------------------------

def test_post_avatar_at_limit_403(client, fake_supa):
    # First avatar succeeds (limit=1, count starts at 0)
    _post_done(client)
    # Second avatar: count is now 1, limit is 1 → 403
    resp = client.post(
        "/avatar",
        data=_base_form(),
        files={"photo": ("photo.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
        headers=_AUTH_HEADER,
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "avatar limit reached for this account"


def test_post_avatar_higher_limit_allowed(client, fake_supa):
    # Raise limit to 2
    fake_supa._limits[_ALICE_ID] = 2
    _post_done(client)  # count=1, limit=2 → OK
    resp = client.post(
        "/avatar",
        data=_base_form(),
        files={"photo": ("photo.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
        headers=_AUTH_HEADER,
    )
    assert resp.status_code == 202


def test_post_avatar_supabase_down_503(client, fake_supa):
    """If Supabase is unreachable during the limit check, we must 503 (not generate)."""
    fake_supa.fail_count = True
    resp = client.post(
        "/avatar",
        data=_base_form(),
        files={"photo": ("photo.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
        headers=_AUTH_HEADER,
    )
    assert resp.status_code == 503


def test_post_avatar_supabase_insert_fail_503(client, fake_supa):
    """If Supabase insert fails, we must 503."""
    fake_supa.fail_insert = True
    resp = client.post(
        "/avatar",
        data=_base_form(),
        files={"photo": ("photo.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
        headers=_AUTH_HEADER,
    )
    assert resp.status_code == 503


# ---------------------------------------------------------------------------
# POST /avatar — happy path
# ---------------------------------------------------------------------------

def test_post_avatar_returns_202_with_job_id(client):
    resp = client.post(
        "/avatar",
        data=_base_form(),
        files={"photo": ("photo.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
        headers=_AUTH_HEADER,
    )
    assert resp.status_code == 202
    body = resp.json()
    assert "job" in body
    assert body["status_url"].endswith(f"/avatar/{body['job']}")


def test_post_avatar_background_task_completes_to_done(client, store_root):
    resp = client.post(
        "/avatar",
        data=_base_form(),
        files={"photo": ("photo.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
        headers=_AUTH_HEADER,
    )
    assert resp.status_code == 202
    job = resp.json()["job"]

    meta_path = store_root / "private" / "avatars" / job / "meta.json"
    assert meta_path.exists()
    meta = json.loads(meta_path.read_text())
    assert meta["status"] == "done"
    assert isinstance(meta["frame_count"], int) and meta["frame_count"] > 0


def test_post_avatar_meta_has_projection(client, store_root):
    resp = client.post(
        "/avatar",
        data=_base_form(),
        files={"photo": ("photo.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
        headers=_AUTH_HEADER,
    )
    job = resp.json()["job"]
    meta = json.loads((store_root / "private" / "avatars" / job / "meta.json").read_text())
    assert meta["projection"] is not None
    assert "weight_after_lb" in meta["projection"]


def test_post_avatar_stores_user_id_in_meta(client, store_root):
    """The local meta.json must store the authenticated user_id."""
    resp = client.post(
        "/avatar",
        data=_base_form(),
        files={"photo": ("photo.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
        headers=_AUTH_HEADER,
    )
    job = resp.json()["job"]
    meta = json.loads((store_root / "private" / "avatars" / job / "meta.json").read_text())
    assert meta["user"] == _ALICE_ID


def test_post_avatar_mirrors_to_supabase(client, fake_supa):
    """After creation the Supabase row must exist with correct user_id and job."""
    resp = client.post(
        "/avatar",
        data=_base_form(),
        files={"photo": ("photo.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
        headers=_AUTH_HEADER,
    )
    job = resp.json()["job"]
    row = fake_supa._rows.get(job)
    assert row is not None
    assert row["user_id"] == _ALICE_ID
    assert row["status"] == "done"  # background task ran synchronously


# ---------------------------------------------------------------------------
# Validation (22-field schema) — still 422 with auth
# ---------------------------------------------------------------------------

def test_post_avatar_422_on_invalid_sex(client):
    resp = client.post(
        "/avatar",
        data=_base_form(sex="X"),
        files={"photo": ("photo.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
        headers=_AUTH_HEADER,
    )
    assert resp.status_code == 422


def test_post_avatar_422_on_invalid_goal(client):
    resp = client.post(
        "/avatar",
        data=_base_form(goal="dirty_bulk"),
        files={"photo": ("photo.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
        headers=_AUTH_HEADER,
    )
    assert resp.status_code == 422


def test_post_avatar_415_on_unsupported_photo_type(client):
    resp = client.post(
        "/avatar",
        data=_base_form(),
        files={"photo": ("photo.gif", b"GIF89a-not-really", "image/gif")},
        headers=_AUTH_HEADER,
    )
    assert resp.status_code == 415


# ---------------------------------------------------------------------------
# GET /avatar/{job}
# ---------------------------------------------------------------------------

def test_get_avatar_done_returns_frames_block(client):
    job = _post_done(client)

    resp = client.get(f"/avatar/{job}", headers=_AUTH_HEADER)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "done"

    frames = body["frames"]
    assert frames is not None
    assert frames["count"] > 0
    assert frames["base_url"].endswith("/frames_mobile")
    assert frames["ext"] == "webp"

    proj = body["projection"]
    assert proj is not None
    for key in ("direction", "months", "weight_before_lb", "weight_after_lb",
                "bf_before", "bf_after", "confidence_score", "measurements_cm"):
        assert key in proj


def test_get_avatar_done_has_after_url(client):
    job = _post_done(client)

    resp = client.get(f"/avatar/{job}", headers=_AUTH_HEADER)
    body = resp.json()
    assert body["after_url"] is not None
    assert f"/outputs/avatars/{job}/after.jpg" in body["after_url"]


def test_get_avatar_unknown_job_404(client):
    resp = client.get("/avatar/deadbeef0000", headers=_AUTH_HEADER)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Failure path: orbit raises -> job lands failed
# ---------------------------------------------------------------------------

def test_failed_job_status_and_error_reflected(client_fail_orbit, store_root):
    resp = client_fail_orbit.post(
        "/avatar",
        data=_base_form(),
        files={"photo": ("photo.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
        headers=_AUTH_HEADER,
    )
    assert resp.status_code == 202
    job = resp.json()["job"]

    get_resp = client_fail_orbit.get(f"/avatar/{job}", headers=_AUTH_HEADER)
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["status"] == "failed"
    assert body["error"] is not None
    assert body["frames"] is None


def test_stage_factory_crash_marks_job_failed_not_stuck_queued(monkeypatch, store_root, fake_supa):
    """A crash while BUILDING the stages must land the job in 'failed' —
    BackgroundTasks swallows exceptions, so an unguarded factory would leave
    the job stuck in 'queued' forever (review finding)."""
    real_store = AvatarJobStore(store_root / "media", store_root / "private")
    monkeypatch.setattr(app_module, "_job_store", real_store)

    def exploding_factory(out_dir):
        raise RuntimeError("boom at stage construction")

    monkeypatch.setattr(app_module, "AVATAR_STAGES_FACTORY", exploding_factory)
    _patch_supa(monkeypatch, fake_supa)
    client = TestClient(app_module.app, raise_server_exceptions=False)

    resp = client.post(
        "/avatar",
        data=_base_form(),
        files={"photo": ("photo.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
        headers=_AUTH_HEADER,
    )
    job = resp.json()["job"]
    body = client.get(f"/avatar/{job}", headers=_AUTH_HEADER).json()
    assert body["status"] == "failed"
    assert "boom at stage construction" in body["error"]


# ---------------------------------------------------------------------------
# GET /avatar/latest
# ---------------------------------------------------------------------------

def test_latest_returns_newest_done_job(client, fake_supa):
    # Alice needs limit=2 to create two avatars
    fake_supa._limits[_ALICE_ID] = 2

    job1 = _post_done(client)
    job2 = _post_done(client, **{"age": "25"})  # small variation to get a different job id

    # latest_done_for_user returns the most recently inserted done row
    resp = client.get("/avatar/latest", headers=_AUTH_HEADER)
    assert resp.status_code == 200
    body = resp.json()
    # job2 was inserted last so it should be newest
    assert body["job"] == job2


def test_latest_no_done_jobs_404(client):
    resp = client.get("/avatar/latest", headers=_AUTH_HEADER)
    assert resp.status_code == 404


def test_latest_returns_own_job_not_others(client, fake_supa, store_root):
    """Alice's /latest must never return Bob's job."""
    # Alice creates a job
    job = _post_done(client)

    # Bob creates a separate job
    fake_supa._tokens["bobtoken"] = _BOB_USER
    fake_supa._limits[_BOB_ID] = 5  # Bob has plenty of limit

    # Bob's latest should 404 because FakeSupa.latest_done_for_user filters by user_id
    resp = client.get("/avatar/latest", headers={"Authorization": "Bearer bobtoken"})
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /avatar/refresh
# ---------------------------------------------------------------------------

def test_refresh_same_inputs_no_rebake(client):
    job = _post_done(client)

    resp = client.post(
        "/avatar/refresh",
        data={**_base_form(), "job": job},
        headers=_AUTH_HEADER,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["rebake_recommended"] is False
    assert isinstance(body["reasons"], list)
    assert "current_projection" in body
    assert "baked_projection" in body


def test_refresh_bumped_weight_triggers_rebake(client):
    job = _post_done(client, **{"weight_lb": "192"})

    # +10 lb should shift the projection enough to trigger rebake
    resp = client.post(
        "/avatar/refresh",
        data={**_base_form(weight_lb="202"), "job": job},
        headers=_AUTH_HEADER,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["rebake_recommended"] is True
    assert len(body["reasons"]) > 0


def test_refresh_unknown_job_404(client):
    resp = client.post(
        "/avatar/refresh",
        data={**_base_form(), "job": "deadbeef0000"},
        headers=_AUTH_HEADER,
    )
    assert resp.status_code == 404


def test_refresh_invalid_goal_422(client):
    job = _post_done(client)
    resp = client.post(
        "/avatar/refresh",
        data={**_base_form(goal="invalid_goal"), "job": job},
        headers=_AUTH_HEADER,
    )
    assert resp.status_code == 422
