"""Tests for server/share_card.py (composer) and GET /share-card/{job} route.

TDD spec:
  Composer:
    - render_share_card returns a PIL.Image with dims 1080x1350
    - no network calls (pure composition)
    - works with a tiny fixture PIL.Image for after_img
    - works with before_img=None (after-only variant)
    - works with before_img provided (side-by-side variant)

  Route:
    - 401 when unauthenticated on avatar job
    - 403 when authenticated as foreign user on avatar job
    - 404 when job unknown (neither avatar nor transform)
    - 200 PNG (Content-Type image/png) for owner with avatar job
    - transform path: no auth needed if projection.json present; 404 if absent
"""
from __future__ import annotations

import io
import json
import pathlib
import sys

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
    from PIL import Image
    from fastapi.testclient import TestClient

    import server.app as app_module
    import server.supa as supa_module
    import server.storage as storage_module
    from server.avatar_jobs import AvatarJobStore
    from server.share_card import render_share_card


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ALICE_TOKEN = "testtoken-sharecard"
_BOB_TOKEN   = "bobtoken-sharecard"
_AUTH_HEADER = {"Authorization": f"Bearer {_ALICE_TOKEN}"}

_ALICE_ID = "alice-sharecard-000-000000000001"
_BOB_ID   = "bob-sharecard-0000-000000000002"
_ALICE_USER = {"id": _ALICE_ID, "email": "alice-sharecard@example.com"}
_BOB_USER   = {"id": _BOB_ID,   "email": "bob-sharecard@example.com"}

_SAMPLE_PROJECTION = {
    "direction": "cut",
    "months": 6,
    "weight_before_lb": 185.0,
    "weight_after_lb": 172.0,
    "weight_delta_lb": -13.0,
    "bf_before": 20.0,
    "bf_after": 13.0,
    "bf_delta": -7.0,
    "lean_delta_lb": 2.5,
    "confidence_score": 0.85,
}


def _tiny_img(w=4, h=4) -> Image.Image:
    return Image.new("RGB", (w, h), color=(128, 64, 64))


# ---------------------------------------------------------------------------
# Composer unit tests — no route, no network
# ---------------------------------------------------------------------------

class TestRenderShareCard:
    def test_returns_pil_image(self):
        after = _tiny_img()
        result = render_share_card(after, _SAMPLE_PROJECTION)
        assert isinstance(result, Image.Image)

    def test_dims_1080x1350(self):
        after = _tiny_img()
        result = render_share_card(after, _SAMPLE_PROJECTION)
        assert result.size == (1080, 1350)

    def test_after_only_variant(self):
        after = _tiny_img()
        result = render_share_card(after, _SAMPLE_PROJECTION, before_img=None)
        assert result.size == (1080, 1350)

    def test_side_by_side_variant(self):
        after = _tiny_img()
        before = _tiny_img()
        result = render_share_card(after, _SAMPLE_PROJECTION, before_img=before)
        assert result.size == (1080, 1350)

    def test_no_network_calls(self, monkeypatch):
        """Composer must be pure — no httpx or requests imports triggered."""
        import unittest.mock as mock
        after = _tiny_img()
        # Patch httpx.Client to raise if instantiated
        with mock.patch("httpx.Client", side_effect=AssertionError("network call in composer")):
            result = render_share_card(after, _SAMPLE_PROJECTION)
        assert result.size == (1080, 1350)

    def test_can_save_as_png(self, tmp_path):
        after = _tiny_img()
        result = render_share_card(after, _SAMPLE_PROJECTION)
        out = tmp_path / "card.png"
        result.save(out, format="PNG")
        loaded = Image.open(out)
        assert loaded.format == "PNG"


# ---------------------------------------------------------------------------
# Fake supa + fixtures for route tests
# ---------------------------------------------------------------------------

class FakeSupaShareCard:
    def __init__(self):
        self._tokens = {_ALICE_TOKEN: _ALICE_USER, _BOB_TOKEN: _BOB_USER}
        self._avatars: dict[str, dict] = {}
        self._limits: dict[str, int] = {}
        self._counter = 0

    def verify_token(self, token: str) -> dict | None:
        return self._tokens.get(token)

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
        rows = [r for r in self._avatars.values()
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
    return FakeSupaShareCard()


@pytest.fixture()
def client(monkeypatch, tmp_path, fake_supa):
    real_store = AvatarJobStore(tmp_path / "media", tmp_path / "private")
    monkeypatch.setattr(app_module, "_job_store", real_store)
    monkeypatch.setattr(storage_module, "storage_enabled", lambda: False)
    _patch_supa(monkeypatch, fake_supa)
    return TestClient(app_module.app, raise_server_exceptions=False)


def _write_after_jpg(store: AvatarJobStore, job: str) -> pathlib.Path:
    """Write a tiny JPEG into the job's public outputs dir."""
    out = store.job_dir(job)
    out.mkdir(parents=True, exist_ok=True)
    img_path = out / "after.jpg"
    _tiny_img(8, 8).save(img_path, format="JPEG")
    return img_path


def _make_avatar_job(store: AvatarJobStore, fake_supa, job: str, user_id: str) -> None:
    """Create a done avatar job with local files + supa row."""
    store.create(job, user=user_id, inputs={})
    store.update(job, status="done", projection=_SAMPLE_PROJECTION)
    _write_after_jpg(store, job)
    fake_supa._avatars[job] = {
        "job": job,
        "user_id": user_id,
        "status": "done",
        "after_url": None,
        "projection": _SAMPLE_PROJECTION,
        "created_at": "2024-01-01T00:00:01Z",
        "inputs": {},
    }


# ---------------------------------------------------------------------------
# Route: avatar job path
# ---------------------------------------------------------------------------

def test_share_card_avatar_no_token_401(client, monkeypatch, tmp_path, fake_supa):
    store = AvatarJobStore(tmp_path / "media", tmp_path / "private")
    monkeypatch.setattr(app_module, "_job_store", store)
    _make_avatar_job(store, fake_supa, "avjob-auth", _ALICE_ID)

    resp = client.get("/share-card/avjob-auth")
    assert resp.status_code == 401


def test_share_card_avatar_foreign_403(client, monkeypatch, tmp_path, fake_supa):
    store = AvatarJobStore(tmp_path / "media", tmp_path / "private")
    monkeypatch.setattr(app_module, "_job_store", store)
    _make_avatar_job(store, fake_supa, "avjob-foreign", _ALICE_ID)

    resp = client.get(
        "/share-card/avjob-foreign",
        headers={"Authorization": f"Bearer {_BOB_TOKEN}"},
    )
    assert resp.status_code == 403


def test_share_card_unknown_job_404(client):
    resp = client.get("/share-card/no-such-job", headers=_AUTH_HEADER)
    assert resp.status_code == 404


def test_share_card_avatar_owner_returns_png(client, monkeypatch, tmp_path, fake_supa):
    store = AvatarJobStore(tmp_path / "media", tmp_path / "private")
    monkeypatch.setattr(app_module, "_job_store", store)
    _make_avatar_job(store, fake_supa, "avjob-owner", _ALICE_ID)

    resp = client.get("/share-card/avjob-owner", headers=_AUTH_HEADER)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("image/png")


# ---------------------------------------------------------------------------
# Route: transform job path (job-id-as-capability, no auth)
# ---------------------------------------------------------------------------

def test_share_card_transform_with_projection_200(client, monkeypatch, tmp_path, fake_supa):
    """A transform job (outputs/{job}/after.jpg + JOBS_PRIVATE/{job}/projection.json) — no auth."""
    store = AvatarJobStore(tmp_path / "media", tmp_path / "private")
    monkeypatch.setattr(app_module, "_job_store", store)

    job = "xformjob001"
    # Public output: after.jpg (served via static mount)
    job_dir = app_module.OUTPUTS / job
    job_dir.mkdir(parents=True, exist_ok=True)
    _tiny_img(8, 8).save(job_dir / "after.jpg", format="JPEG")
    # Private projection: written by /transform to JOBS_PRIVATE/{job}/projection.json
    priv_dir = app_module.JOBS_PRIVATE / job
    priv_dir.mkdir(parents=True, exist_ok=True)
    (priv_dir / "projection.json").write_text(json.dumps(_SAMPLE_PROJECTION))

    resp = client.get(f"/share-card/{job}")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("image/png")

    # Cleanup
    import shutil
    shutil.rmtree(job_dir, ignore_errors=True)
    shutil.rmtree(priv_dir, ignore_errors=True)


def test_share_card_transform_without_projection_404(client, monkeypatch, tmp_path):
    """Transform job dir exists but no projection.json → 404."""
    store = AvatarJobStore(tmp_path / "media", tmp_path / "private")
    monkeypatch.setattr(app_module, "_job_store", store)

    job = "xformjob002"
    job_dir = app_module.OUTPUTS / job
    job_dir.mkdir(parents=True, exist_ok=True)
    _tiny_img(8, 8).save(job_dir / "after.jpg", format="JPEG")
    # No projection.json written in JOBS_PRIVATE

    resp = client.get(f"/share-card/{job}")
    assert resp.status_code == 404

    import shutil
    shutil.rmtree(job_dir, ignore_errors=True)
