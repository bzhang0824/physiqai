"""Tests for server.storage and storage-related behaviour in server.app.

All tests are hermetic — no network calls. storage.storage_enabled() is
monkeypatched to False in the existing route tests so local-URL behaviour is
preserved unchanged.  The focused tests here verify:

  (a) public_url builds the right string
  (b) _avatar_response returns Supabase URLs when meta has frame_base_url
  (c) when storage_enabled() is True, _run_avatar_job stores storage URLs
      in meta (upload_file is monkeypatched to avoid network)
  (d) existing route fixtures keep storage disabled so they continue to
      exercise local-URL paths (regression guard)
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
    import numpy as np
    from fastapi.testclient import TestClient
    from PIL import Image

    import server.app as app_module
    import server.storage as storage_module
    import server.supa as supa_module
    from pipeline.avatar import AvatarResult, AvatarStages
    from server.avatar_jobs import AvatarJobStore

    # Reuse helpers from test_avatar_routes
    from tests.server.test_avatar_routes import (
        FakeSupa,
        _base_form,
        _make_fake_stages,
        _patch_supa,
        _tiny_jpeg_bytes,
        _AUTH_HEADER,
        _ALICE_ID,
        _ALICE_USER,
        _TEST_TOKEN,
    )


# ---------------------------------------------------------------------------
# (a) public_url builds the correct string
# ---------------------------------------------------------------------------

def test_public_url_media_bucket(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://abc.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "fake-key")
    url = storage_module.public_url("avatar-media", "job123/after.jpg")
    assert url == "https://abc.supabase.co/storage/v1/object/public/avatar-media/job123/after.jpg"


def test_public_url_strips_trailing_slash(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://abc.supabase.co/")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "fake-key")
    url = storage_module.public_url("avatar-media", "job/frames_mobile")
    assert url == "https://abc.supabase.co/storage/v1/object/public/avatar-media/job/frames_mobile"


def test_storage_enabled_both_set(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://abc.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "sk")
    assert storage_module.storage_enabled() is True


def test_storage_enabled_missing_url(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "sk")
    assert storage_module.storage_enabled() is False


def test_storage_enabled_missing_key(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://abc.supabase.co")
    monkeypatch.delenv("SUPABASE_SERVICE_KEY", raising=False)
    assert storage_module.storage_enabled() is False


# ---------------------------------------------------------------------------
# (b) _avatar_response returns Supabase URLs when meta has frame_base_url
# ---------------------------------------------------------------------------

def test_avatar_response_uses_storage_urls_when_frame_base_url_set(tmp_path):
    """_avatar_response must use Storage URLs when meta['frame_base_url'] is set."""
    real_store = AvatarJobStore(tmp_path / "media", tmp_path / "private")
    job = "testjob0001"
    real_store.create(job, user=_ALICE_ID, inputs={})
    real_store.update(
        job,
        status="done",
        progress_pct=100,
        frame_count=10,
        frame_base_url="https://abc.supabase.co/storage/v1/object/public/avatar-media/testjob0001/frames_mobile",
        after_url="https://abc.supabase.co/storage/v1/object/public/avatar-media/testjob0001/after.jpg",
        master_url="https://abc.supabase.co/storage/v1/object/public/avatar-media/testjob0001/master.webm",
    )

    # Temporarily swap the module-level store
    original_store = app_module._job_store
    app_module._job_store = real_store
    try:
        meta = real_store.get(job)
        result = app_module._avatar_response(meta, "http://localhost:8000")
    finally:
        app_module._job_store = original_store

    # Should use Storage URLs, not local /outputs paths
    assert result["after_url"] == "https://abc.supabase.co/storage/v1/object/public/avatar-media/testjob0001/after.jpg"
    assert result["master_url"] == "https://abc.supabase.co/storage/v1/object/public/avatar-media/testjob0001/master.webm"
    frames = result["frames"]
    assert frames is not None
    assert frames["count"] == 10
    assert frames["base_url"].endswith("/frames_mobile")
    assert "supabase" in frames["base_url"]
    assert frames["ext"] == "webp"


def test_avatar_response_falls_back_to_local_when_no_frame_base_url(tmp_path):
    """Without frame_base_url in meta, response must use local /outputs paths."""
    real_store = AvatarJobStore(tmp_path / "media", tmp_path / "private")
    job = "localjob0001"
    real_store.create(job, user=_ALICE_ID, inputs={})
    real_store.update(job, status="done", progress_pct=100, frame_count=5)

    # Write a fake after.jpg so the existence check passes
    job_dir = real_store.job_dir(job)
    (job_dir / "after.jpg").write_bytes(b"\xff\xd8\xff")

    original_store = app_module._job_store
    app_module._job_store = real_store
    try:
        meta = real_store.get(job)
        result = app_module._avatar_response(meta, "http://localhost:8000")
    finally:
        app_module._job_store = original_store

    assert result["after_url"] is not None
    assert "/outputs/" in result["after_url"]
    frames = result["frames"]
    assert frames is not None
    assert "/outputs/" in frames["base_url"]
    assert frames["base_url"].endswith("/frames_mobile")
    assert frames["ext"] == "webp"


# ---------------------------------------------------------------------------
# (c) _run_avatar_job stores storage URLs in meta when storage is enabled
# ---------------------------------------------------------------------------

@pytest.fixture()
def storage_client(monkeypatch, tmp_path):
    """TestClient with storage_enabled=True and upload_file monkeypatched."""
    real_store = AvatarJobStore(tmp_path / "media", tmp_path / "private")
    monkeypatch.setattr(app_module, "_job_store", real_store)

    def fake_factory(out_dir: pathlib.Path, **kwargs) -> AvatarStages:
        return _make_fake_stages(out_dir)

    monkeypatch.setattr(app_module, "AVATAR_STAGES_FACTORY", fake_factory)

    fake_supa = FakeSupa()
    _patch_supa(monkeypatch, fake_supa)

    # Enable storage, but intercept upload_file and download_to so no network
    monkeypatch.setattr(storage_module, "storage_enabled", lambda: True)

    uploaded: list[tuple[str, str]] = []

    def fake_upload(bucket, key, local_path, content_type, *, _client=None):
        uploaded.append((bucket, key))

    monkeypatch.setattr(storage_module, "upload_file", fake_upload)

    # Patch public_url to return a predictable Supabase-style URL
    real_public_url = storage_module.public_url

    def fake_public_url(bucket, key):
        return f"https://test.supabase.co/storage/v1/object/public/{bucket}/{key}"

    monkeypatch.setattr(storage_module, "public_url", fake_public_url)

    tc = TestClient(app_module.app, raise_server_exceptions=False)
    return tc, real_store, uploaded, fake_supa


def test_run_avatar_job_stores_storage_urls_in_meta(storage_client, tmp_path):
    """After a successful generation with storage enabled, meta must have
    frame_base_url, after_url, master_url pointing to Supabase."""
    tc, real_store, uploaded, fake_supa = storage_client

    resp = tc.post(
        "/avatar",
        data=_base_form(),
        files={"photo": ("photo.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
        headers=_AUTH_HEADER,
    )
    assert resp.status_code == 202
    job = resp.json()["job"]

    meta = real_store.get(job)
    assert meta["status"] == "done"
    assert "frame_base_url" in meta
    assert "after_url" in meta
    assert "master_url" in meta
    assert "supabase" in meta["frame_base_url"]
    assert meta["frame_base_url"].endswith("/frames_mobile")
    assert "supabase" in meta["after_url"]


def test_run_avatar_job_upload_calls_recorded(storage_client):
    """upload_file must be called for each frames_mobile webp + after.jpg + before.jpg."""
    tc, real_store, uploaded, _ = storage_client

    resp = tc.post(
        "/avatar",
        data=_base_form(),
        files={"photo": ("photo.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
        headers=_AUTH_HEADER,
    )
    assert resp.status_code == 202

    # Expect uploads into both buckets
    buckets_used = {b for b, _ in uploaded}
    assert "avatar-media" in buckets_used
    assert "avatar-private" in buckets_used

    # after.jpg should be uploaded to media bucket
    media_keys = [k for b, k in uploaded if b == "avatar-media"]
    assert any(k.endswith("/after.jpg") for k in media_keys)

    # before.jpg should be uploaded to private bucket
    private_keys = [k for b, k in uploaded if b == "avatar-private"]
    assert any(k.endswith("/before.jpg") for k in private_keys)


def test_run_avatar_job_storage_urls_in_get_response(storage_client):
    """GET /avatar/{job} must return Supabase URLs when frame_base_url is in meta."""
    tc, _, _, _ = storage_client

    resp = tc.post(
        "/avatar",
        data=_base_form(),
        files={"photo": ("photo.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
        headers=_AUTH_HEADER,
    )
    job = resp.json()["job"]

    get_resp = tc.get(f"/avatar/{job}", headers=_AUTH_HEADER)
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["status"] == "done"

    frames = body["frames"]
    assert frames is not None
    assert frames["base_url"].endswith("/frames_mobile")
    assert "supabase" in frames["base_url"]
    assert frames["ext"] == "webp"

    assert body["after_url"] is not None
    assert "supabase" in body["after_url"]


def test_storage_upload_failure_doesnt_fail_job(monkeypatch, tmp_path):
    """An upload failure must be swallowed — the job should still complete as done."""
    real_store = AvatarJobStore(tmp_path / "media", tmp_path / "private")
    monkeypatch.setattr(app_module, "_job_store", real_store)

    def fake_factory(out_dir, **kwargs):
        return _make_fake_stages(out_dir)

    monkeypatch.setattr(app_module, "AVATAR_STAGES_FACTORY", fake_factory)

    fake_supa = FakeSupa()
    _patch_supa(monkeypatch, fake_supa)

    monkeypatch.setattr(storage_module, "storage_enabled", lambda: True)

    def exploding_upload(bucket, key, local_path, content_type, *, _client=None):
        raise RuntimeError("network blew up")

    monkeypatch.setattr(storage_module, "upload_file", exploding_upload)

    tc = TestClient(app_module.app, raise_server_exceptions=False)
    resp = tc.post(
        "/avatar",
        data=_base_form(),
        files={"photo": ("photo.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
        headers=_AUTH_HEADER,
    )
    assert resp.status_code == 202
    job = resp.json()["job"]

    meta = real_store.get(job)
    # Job must still succeed — upload failure is non-fatal
    assert meta["status"] == "done"
    # No storage URLs stored (fallback to local)
    assert not meta.get("frame_base_url")


# ---------------------------------------------------------------------------
# (d) Regression: existing route tests hit local-URL fallback (storage=False)
# ---------------------------------------------------------------------------

def test_route_with_storage_disabled_uses_local_urls(monkeypatch, tmp_path):
    """When storage_enabled() returns False, GET /avatar/{job} uses /outputs paths."""
    real_store = AvatarJobStore(tmp_path / "media", tmp_path / "private")
    monkeypatch.setattr(app_module, "_job_store", real_store)

    def fake_factory(out_dir, **kwargs):
        return _make_fake_stages(out_dir)

    monkeypatch.setattr(app_module, "AVATAR_STAGES_FACTORY", fake_factory)

    fake_supa = FakeSupa()
    _patch_supa(monkeypatch, fake_supa)

    # Explicitly disable storage
    monkeypatch.setattr(storage_module, "storage_enabled", lambda: False)

    tc = TestClient(app_module.app, raise_server_exceptions=False)
    resp = tc.post(
        "/avatar",
        data=_base_form(),
        files={"photo": ("photo.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
        headers=_AUTH_HEADER,
    )
    assert resp.status_code == 202
    job = resp.json()["job"]

    get_resp = tc.get(f"/avatar/{job}", headers=_AUTH_HEADER)
    body = get_resp.json()

    frames = body["frames"]
    assert frames is not None
    assert frames["base_url"].endswith("/frames_mobile")
    assert "/outputs/" in frames["base_url"]
    assert "supabase" not in frames["base_url"]


# ---------------------------------------------------------------------------
# list_objects / remove_objects (account-deletion media cleanup)
# ---------------------------------------------------------------------------

class _FakeResp:
    def __init__(self, status_code=200, body=None):
        self.status_code = status_code
        self._body = body if body is not None else []

    def json(self):
        return self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class _FakeClient:
    def __init__(self, resp):
        self._resp = resp
        self.calls = []

    def post(self, url, **kw):
        self.calls.append({"method": "POST", "url": url, **kw})
        return self._resp

    def request(self, method, url, **kw):
        self.calls.append({"method": method, "url": url, **kw})
        return self._resp

    def close(self):
        pass


@pytest.fixture
def _storage_env(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "svc-key")


def test_list_objects_returns_prefixed_keys(_storage_env):
    client = _FakeClient(_FakeResp(200, [{"name": "a.webp"}, {"name": "b.webp"}]))
    keys = storage_module.list_objects("avatar-media", "job1/frames_mobile", _client=client)
    assert keys == ["job1/frames_mobile/a.webp", "job1/frames_mobile/b.webp"]
    assert client.calls[0]["url"] == "https://fake.supabase.co/storage/v1/object/list/avatar-media"
    assert client.calls[0]["json"]["prefix"] == "job1/frames_mobile"


def test_remove_objects_sends_prefixes(_storage_env):
    client = _FakeClient(_FakeResp(200, {}))
    storage_module.remove_objects("avatar-media", ["job1/after.jpg", "job1/master.webm"], _client=client)
    call = client.calls[0]
    assert call["method"] == "DELETE"
    assert call["url"] == "https://fake.supabase.co/storage/v1/object/avatar-media"
    assert call["json"]["prefixes"] == ["job1/after.jpg", "job1/master.webm"]


def test_remove_objects_noop_on_empty(_storage_env):
    client = _FakeClient(_FakeResp(200, {}))
    storage_module.remove_objects("avatar-media", [], _client=client)
    assert client.calls == []  # no request made
