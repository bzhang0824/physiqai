"""Integration: side/back photos flow from the routes into the pipeline as
morph references (front stays the canvas), and raw side/back photos never
land under the public outputs mount.

This is the wiring the multi-photo and pipeline-multiref tracks each left to
the integrator (the INTEGRATION(launch-build) markers in server/app.py).
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import server.app as app_module
from server.avatar_jobs import AvatarJobStore

# Reuse the canonical fakes/fixtures from test_avatar_routes
from tests.server.test_avatar_routes import (  # noqa: E402
    FakeSupa,
    _AUTH_HEADER,
    _base_form,
    _make_fake_stages,
    _patch_supa,
    _tiny_jpeg_bytes,
)


def _photos3():
    return [
        ("photo_front", ("f.jpg", _tiny_jpeg_bytes(), "image/jpeg")),
        ("photo_side", ("s.jpg", _tiny_jpeg_bytes(), "image/jpeg")),
        ("photo_back", ("b.jpg", _tiny_jpeg_bytes(), "image/jpeg")),
    ]


@pytest.fixture()
def fake_supa() -> FakeSupa:
    return FakeSupa()


# ---------------------------------------------------------------------------
# /transform
# ---------------------------------------------------------------------------

@pytest.fixture()
def transform_client(monkeypatch, tmp_path, fake_supa):
    outputs = tmp_path / "outputs"
    private = tmp_path / "private"
    outputs.mkdir()
    private.mkdir()
    monkeypatch.setattr(app_module, "OUTPUTS", outputs)
    monkeypatch.setattr(app_module, "JOBS_PRIVATE", private)
    _patch_supa(monkeypatch, fake_supa)  # also no-ops photo content validation

    calls: dict = {}

    def fake_gen(photo, prompt, mask, refs=None):
        calls["photo"] = photo
        calls["prompt"] = prompt
        calls["refs"] = refs
        return np.zeros((8, 8, 3), dtype=np.uint8)

    monkeypatch.setattr(app_module, "generate_nano_banana", fake_gen)
    return TestClient(app_module.app, raise_server_exceptions=False), calls


def test_transform_passes_refs_and_keeps_side_back_private(transform_client):
    client, calls = transform_client
    resp = client.post("/transform", data=_base_form(), files=_photos3())
    assert resp.status_code == 200, resp.text
    job = resp.json()["job"]

    # refs: side then back, pointing at PRIVATE paths
    refs = calls["refs"]
    assert refs is not None and len(refs) == 2
    assert refs[0].endswith("before_side.jpg")
    assert refs[1].endswith("before_back.jpg")
    for r in refs:
        assert str(app_module.JOBS_PRIVATE) in r

    # the prompt carries the multi-ref preamble naming the extra angles
    assert "side" in calls["prompt"] and "back" in calls["prompt"]

    # public outputs: only before.jpg/after.jpg — raw side/back never public
    pub = sorted(p.name for p in (app_module.OUTPUTS / job).iterdir())
    assert "before.jpg" in pub and "after.jpg" in pub
    assert not any("side" in n or "back" in n for n in pub)


def test_transform_single_photo_no_refs(transform_client):
    client, calls = transform_client
    resp = client.post(
        "/transform",
        data=_base_form(),
        files={"photo": ("p.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
    )
    assert resp.status_code == 200, resp.text
    job = resp.json()["job"]
    assert not calls["refs"]
    # before_url regression: the public before.jpg must exist
    assert (app_module.OUTPUTS / job / "before.jpg").exists()


# ---------------------------------------------------------------------------
# /avatar — factory receives refs
# ---------------------------------------------------------------------------

@pytest.fixture()
def avatar_client(monkeypatch, tmp_path, fake_supa):
    real_store = AvatarJobStore(tmp_path / "media", tmp_path / "privstore")
    monkeypatch.setattr(app_module, "_job_store", real_store)

    captured: dict = {}

    def fake_factory(out_dir, **kwargs):
        captured["called"] = True
        captured.update(kwargs)
        return _make_fake_stages(out_dir)

    monkeypatch.setattr(app_module, "AVATAR_STAGES_FACTORY", fake_factory)
    _patch_supa(monkeypatch, fake_supa)
    return TestClient(app_module.app, raise_server_exceptions=False), captured


def test_avatar_factory_receives_refs(avatar_client):
    client, captured = avatar_client
    resp = client.post(
        "/avatar", data=_base_form(), files=_photos3(), headers=_AUTH_HEADER
    )
    assert resp.status_code == 202, resp.text
    assert captured.get("called")
    refs = captured.get("ref_photos") or []
    assert [pathlib.Path(r).name for r in refs] == [
        "before_side.jpg",
        "before_back.jpg",
    ]
    assert tuple(captured.get("ref_angles") or ()) == ("side", "back")


def test_avatar_factory_single_photo_no_ref_kwargs(avatar_client):
    client, captured = avatar_client
    resp = client.post(
        "/avatar",
        data=_base_form(),
        files={"photo": ("p.jpg", _tiny_jpeg_bytes(), "image/jpeg")},
        headers=_AUTH_HEADER,
    )
    assert resp.status_code == 202, resp.text
    assert captured.get("called")
    assert not captured.get("ref_photos")
