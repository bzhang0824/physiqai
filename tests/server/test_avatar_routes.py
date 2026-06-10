"""Tests for POST /avatar, GET /avatar/{job}, GET /avatar/latest, POST /avatar/refresh.

Fakes for pipeline.avatar stages are injected via monkeypatch so no fal.ai calls happen.
BackgroundTasks run synchronously under FastAPI TestClient — tests rely on that.

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
    from pipeline.avatar import AvatarResult, AvatarStages
    from server.avatar_jobs import AvatarJobStore


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
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def store_root(tmp_path: pathlib.Path):
    # Media lands at <root>/media/avatars/<job>, private meta at
    # <root>/private/avatars/<job>/meta.json.
    return tmp_path


@pytest.fixture()
def client(monkeypatch, store_root):
    """TestClient with store and stages patched to use tmp dirs."""
    real_store = AvatarJobStore(store_root / "media", store_root / "private")
    monkeypatch.setattr(app_module, "_job_store", real_store)

    def fake_factory(out_dir: pathlib.Path) -> AvatarStages:
        return _make_fake_stages(out_dir)

    monkeypatch.setattr(app_module, "AVATAR_STAGES_FACTORY", fake_factory)

    return TestClient(app_module.app, raise_server_exceptions=False)


@pytest.fixture()
def client_fail_orbit(monkeypatch, store_root):
    """Client whose stages raise on the orbit step."""
    real_store = AvatarJobStore(store_root / "media", store_root / "private")
    monkeypatch.setattr(app_module, "_job_store", real_store)

    def fail_factory(out_dir: pathlib.Path) -> AvatarStages:
        return _make_fake_stages(out_dir, fail_at="orbit")

    monkeypatch.setattr(app_module, "AVATAR_STAGES_FACTORY", fail_factory)

    return TestClient(app_module.app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# POST /avatar
# ---------------------------------------------------------------------------

def test_post_avatar_returns_202_with_job_id(client):
    resp = client.post(
        "/avatar",
        data=_base_form(),
        files={"photo": ("photo.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
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
    )
    job = resp.json()["job"]
    meta = json.loads((store_root / "private" / "avatars" / job / "meta.json").read_text())
    assert meta["projection"] is not None
    assert "weight_after_lb" in meta["projection"]


def test_post_avatar_422_on_invalid_sex(client):
    resp = client.post(
        "/avatar",
        data=_base_form(sex="X"),
        files={"photo": ("photo.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
    )
    assert resp.status_code == 422


def test_post_avatar_422_on_invalid_goal(client):
    resp = client.post(
        "/avatar",
        data=_base_form(goal="dirty_bulk"),
        files={"photo": ("photo.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
    )
    assert resp.status_code == 422


def test_post_avatar_415_on_unsupported_photo_type(client):
    resp = client.post(
        "/avatar",
        data=_base_form(),
        files={"photo": ("photo.gif", b"GIF89a-not-really", "image/gif")},
    )
    assert resp.status_code == 415


# ---------------------------------------------------------------------------
# GET /avatar/{job}
# ---------------------------------------------------------------------------

def test_get_avatar_done_returns_frames_block(client):
    post = client.post(
        "/avatar",
        data=_base_form(),
        files={"photo": ("photo.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
    )
    job = post.json()["job"]

    resp = client.get(f"/avatar/{job}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "done"

    frames = body["frames"]
    assert frames is not None
    assert frames["count"] > 0
    assert frames["base_url"].endswith("/frames_mobile")
    assert frames["ext"] == "webp"

    # A done job must carry its projection — the mobile screen renders it.
    proj = body["projection"]
    assert proj is not None
    for key in ("direction", "months", "weight_before_lb", "weight_after_lb",
                "bf_before", "bf_after", "confidence_score", "measurements_cm"):
        assert key in proj


def test_get_avatar_done_has_after_url(client):
    post = client.post(
        "/avatar",
        data=_base_form(),
        files={"photo": ("photo.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
    )
    job = post.json()["job"]

    resp = client.get(f"/avatar/{job}")
    body = resp.json()
    assert body["after_url"] is not None
    assert f"/outputs/avatars/{job}/after.jpg" in body["after_url"]


def test_get_avatar_unknown_job_404(client):
    resp = client.get("/avatar/deadbeef0000")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Failure path: orbit raises -> job lands failed
# ---------------------------------------------------------------------------

def test_failed_job_status_and_error_reflected(client_fail_orbit, store_root):
    resp = client_fail_orbit.post(
        "/avatar",
        data=_base_form(),
        files={"photo": ("photo.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
    )
    assert resp.status_code == 202
    job = resp.json()["job"]

    get_resp = client_fail_orbit.get(f"/avatar/{job}")
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["status"] == "failed"
    assert body["error"] is not None
    assert body["frames"] is None


def test_stage_factory_crash_marks_job_failed_not_stuck_queued(monkeypatch, store_root):
    """A crash while BUILDING the stages must land the job in 'failed' —
    BackgroundTasks swallows exceptions, so an unguarded factory would leave
    the job stuck in 'queued' forever (review finding)."""
    real_store = AvatarJobStore(store_root / "media", store_root / "private")
    monkeypatch.setattr(app_module, "_job_store", real_store)

    def exploding_factory(out_dir):
        raise RuntimeError("boom at stage construction")

    monkeypatch.setattr(app_module, "AVATAR_STAGES_FACTORY", exploding_factory)
    client = TestClient(app_module.app, raise_server_exceptions=False)

    resp = client.post(
        "/avatar",
        data=_base_form(),
        files={"photo": ("photo.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
    )
    job = resp.json()["job"]
    body = client.get(f"/avatar/{job}").json()
    assert body["status"] == "failed"
    assert "boom at stage construction" in body["error"]


# ---------------------------------------------------------------------------
# GET /avatar/latest
# ---------------------------------------------------------------------------

def _post_done(client, user: str | None = None):
    data = _base_form()
    if user:
        data["user"] = user
    resp = client.post(
        "/avatar",
        data=data,
        files={"photo": ("photo.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
    )
    assert resp.status_code == 202
    return resp.json()["job"]


def test_latest_returns_newest_done_job(client, store_root, monkeypatch):
    job1 = _post_done(client, user="alice")
    job2 = _post_done(client, user="alice")

    resp = client.get("/avatar/latest?user=alice")
    assert resp.status_code == 200
    body = resp.json()
    assert body["job"] == job2


def test_latest_different_user_404(client):
    _post_done(client, user="alice")
    resp = client.get("/avatar/latest?user=bob")
    assert resp.status_code == 404


def test_latest_no_user_param_422(client):
    resp = client.get("/avatar/latest")
    # FastAPI returns 422 for missing required query param
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /avatar/refresh
# ---------------------------------------------------------------------------

def test_refresh_same_inputs_no_rebake(client):
    post = client.post(
        "/avatar",
        data=_base_form(),
        files={"photo": ("photo.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
    )
    job = post.json()["job"]

    resp = client.post("/avatar/refresh", data={**_base_form(), "job": job})
    assert resp.status_code == 200
    body = resp.json()
    assert body["rebake_recommended"] is False
    assert isinstance(body["reasons"], list)
    assert "current_projection" in body
    assert "baked_projection" in body


def test_refresh_bumped_weight_triggers_rebake(client):
    post = client.post(
        "/avatar",
        data=_base_form(weight_lb="192"),
        files={"photo": ("photo.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
    )
    job = post.json()["job"]

    # +10 lb should shift the projection enough to trigger rebake
    resp = client.post("/avatar/refresh", data={**_base_form(weight_lb="202"), "job": job})
    assert resp.status_code == 200
    body = resp.json()
    assert body["rebake_recommended"] is True
    assert len(body["reasons"]) > 0


def test_refresh_unknown_job_404(client):
    resp = client.post("/avatar/refresh", data={**_base_form(), "job": "deadbeef0000"})
    assert resp.status_code == 404


def test_refresh_invalid_goal_422(client):
    post = client.post(
        "/avatar",
        data=_base_form(),
        files={"photo": ("photo.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
    )
    job = post.json()["job"]
    resp = client.post(
        "/avatar/refresh", data={**_base_form(goal="invalid_goal"), "job": job}
    )
    assert resp.status_code == 422
