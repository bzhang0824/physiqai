"""TDD for pipeline.stages multi-ref support.

Tests that:
- _generate / generate_nano_banana upload front image first, then each ref path,
  and send image_urls = [front_url, *ref_urls].
- refs=None sends exactly one url (front only) — unchanged behavior.
- generate_seededit never receives refs (stays front-only).
- build_default_stages(ref_photos=...) closes over ref_photos and passes them
  through to generate_nano_banana only.
"""
from __future__ import annotations

import pathlib
import sys
from typing import List, Optional

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeRes:
    """Minimal fal_client response object."""
    def __init__(self):
        self._data = {"images": [{"url": "http://fake/out.jpg"}]}

    def get(self, key, default=None):
        return self._data.get(key, default)


class _FakeFalClient:
    """Replaces fal_client so no network calls happen.

    Tracks every upload_file() call in upload_calls and every subscribe()
    call in subscribe_calls.
    """

    def __init__(self, responses=None):
        self.upload_calls: List[str] = []
        self.subscribe_calls: List[dict] = []
        self._responses = responses or {}

    def upload_file(self, path: str) -> str:
        self.upload_calls.append(path)
        return f"http://fake/{pathlib.Path(path).name}"

    def subscribe(self, endpoint: str, arguments: dict, **kwargs) -> _FakeRes:
        self.subscribe_calls.append({"endpoint": endpoint, "arguments": arguments})
        return _FakeRes()


def _fake_download(url: str) -> np.ndarray:
    """Replaces _download_rgb — returns a tiny black image."""
    return np.zeros((4, 4, 3), dtype=np.uint8)


# ---------------------------------------------------------------------------
# _generate: refs upload order and image_urls list
# ---------------------------------------------------------------------------

def test_generate_no_refs_sends_single_url(monkeypatch, tmp_path):
    from pipeline import stages
    fal = _FakeFalClient()
    monkeypatch.setattr(stages, "_ensure_fal_key", lambda: None)
    monkeypatch.setattr(stages, "_download_rgb", _fake_download)

    photo = str(tmp_path / "front.jpg")
    pathlib.Path(photo).write_bytes(b"fake")

    # Import fal_client and monkeypatch it
    import types
    fake_mod = types.ModuleType("fal_client")
    fake_mod.upload_file = fal.upload_file
    fake_mod.subscribe = fal.subscribe
    monkeypatch.setitem(sys.modules, "fal_client", fake_mod)

    stages._generate(photo, "prompt", None, stages.NANO_BANANA, refs=None)

    assert len(fal.upload_calls) == 1
    assert fal.upload_calls[0] == photo
    args = fal.subscribe_calls[0]["arguments"]
    assert args["image_urls"] == ["http://fake/front.jpg"]


def test_generate_with_one_ref_uploads_front_first(monkeypatch, tmp_path):
    from pipeline import stages
    fal = _FakeFalClient()
    monkeypatch.setattr(stages, "_ensure_fal_key", lambda: None)
    monkeypatch.setattr(stages, "_download_rgb", _fake_download)

    photo = str(tmp_path / "front.jpg")
    ref1 = str(tmp_path / "back.jpg")
    pathlib.Path(photo).write_bytes(b"fake")
    pathlib.Path(ref1).write_bytes(b"fake")

    import types
    fake_mod = types.ModuleType("fal_client")
    fake_mod.upload_file = fal.upload_file
    fake_mod.subscribe = fal.subscribe
    monkeypatch.setitem(sys.modules, "fal_client", fake_mod)

    stages._generate(photo, "prompt", None, stages.NANO_BANANA, refs=[ref1])

    # front uploaded first, then ref
    assert fal.upload_calls == [photo, ref1]
    args = fal.subscribe_calls[0]["arguments"]
    assert args["image_urls"] == ["http://fake/front.jpg", "http://fake/back.jpg"]


def test_generate_with_two_refs_uploads_front_then_refs_in_order(monkeypatch, tmp_path):
    from pipeline import stages
    fal = _FakeFalClient()
    monkeypatch.setattr(stages, "_ensure_fal_key", lambda: None)
    monkeypatch.setattr(stages, "_download_rgb", _fake_download)

    photo = str(tmp_path / "front.jpg")
    ref_side = str(tmp_path / "side.jpg")
    ref_back = str(tmp_path / "back.jpg")
    for p in [photo, ref_side, ref_back]:
        pathlib.Path(p).write_bytes(b"fake")

    import types
    fake_mod = types.ModuleType("fal_client")
    fake_mod.upload_file = fal.upload_file
    fake_mod.subscribe = fal.subscribe
    monkeypatch.setitem(sys.modules, "fal_client", fake_mod)

    stages._generate(photo, "prompt", None, stages.NANO_BANANA, refs=[ref_side, ref_back])

    assert fal.upload_calls == [photo, ref_side, ref_back]
    args = fal.subscribe_calls[0]["arguments"]
    assert args["image_urls"] == [
        "http://fake/front.jpg",
        "http://fake/side.jpg",
        "http://fake/back.jpg",
    ]


# ---------------------------------------------------------------------------
# generate_nano_banana passes refs through; generate_seededit never gets refs
# ---------------------------------------------------------------------------

def test_generate_nano_banana_passes_refs(monkeypatch, tmp_path):
    from pipeline import stages
    captured: dict = {}

    def fake_generate(photo, prompt, mask, endpoint, refs=None):
        captured["refs"] = refs
        captured["endpoint"] = endpoint
        return np.zeros((4, 4, 3), dtype=np.uint8)

    monkeypatch.setattr(stages, "_generate", fake_generate)

    photo = str(tmp_path / "front.jpg")
    ref = str(tmp_path / "back.jpg")
    stages.generate_nano_banana(photo, "prompt", None, refs=[ref])

    assert captured["refs"] == [ref]
    assert captured["endpoint"] == stages.NANO_BANANA


def test_generate_nano_banana_none_refs(monkeypatch, tmp_path):
    from pipeline import stages
    captured: dict = {}

    def fake_generate(photo, prompt, mask, endpoint, refs=None):
        captured["refs"] = refs
        return np.zeros((4, 4, 3), dtype=np.uint8)

    monkeypatch.setattr(stages, "_generate", fake_generate)

    stages.generate_nano_banana(str(tmp_path / "front.jpg"), "prompt", None, refs=None)
    assert captured["refs"] is None


def test_generate_seededit_signature_unchanged(monkeypatch, tmp_path):
    """generate_seededit must NOT accept refs — its signature is (photo, prompt, mask)."""
    from pipeline import stages
    import inspect
    sig = inspect.signature(stages.generate_seededit)
    assert list(sig.parameters.keys()) == ["photo", "prompt", "mask"]


# ---------------------------------------------------------------------------
# build_default_stages factory: closes over ref_photos
# ---------------------------------------------------------------------------

def test_build_default_stages_no_refs_generate_receives_none(monkeypatch, tmp_path):
    """build_default_stages() with no ref_photos closes over None."""
    from pipeline import stages
    captured: dict = {}

    def fake_generate(photo, prompt, mask, endpoint, refs=None):
        captured["refs"] = refs
        return np.zeros((4, 4, 3), dtype=np.uint8)

    monkeypatch.setattr(stages, "_generate", fake_generate)

    built = stages.build_default_stages()
    # Invoke the generate callable
    built.generate("front.jpg", "prompt", None)
    assert captured["refs"] is None


def test_build_default_stages_with_refs_generate_receives_refs(monkeypatch, tmp_path):
    """build_default_stages(ref_photos=[...]) closes over the ref list."""
    from pipeline import stages
    captured: dict = {}

    def fake_generate(photo, prompt, mask, endpoint, refs=None):
        captured["refs"] = refs
        return np.zeros((4, 4, 3), dtype=np.uint8)

    monkeypatch.setattr(stages, "_generate", fake_generate)

    refs = ["/fake/side.jpg", "/fake/back.jpg"]
    built = stages.build_default_stages(ref_photos=refs)
    built.generate("front.jpg", "prompt", None)
    assert captured["refs"] == refs


def test_build_default_stages_generate_fallback_never_gets_refs(monkeypatch, tmp_path):
    """generate_fallback (seededit) must be called front-only regardless of ref_photos."""
    from pipeline import stages
    captured: dict = {}

    def fake_seededit(photo, prompt, mask):
        captured["called"] = True
        return np.zeros((4, 4, 3), dtype=np.uint8)

    monkeypatch.setattr(stages, "generate_seededit", fake_seededit)
    monkeypatch.setattr(stages, "_generate", lambda *a, **kw: np.zeros((4, 4, 3), np.uint8))

    refs = ["/fake/back.jpg"]
    built = stages.build_default_stages(ref_photos=refs)
    # The fallback is generate_seededit; call it directly
    built.generate_fallback("front.jpg", "prompt", None)
    assert captured.get("called") is True


def test_stages_dataclass_fields_unchanged():
    """The Stages dataclass fields must not change — only build_default_stages changes."""
    from pipeline.run import Stages
    import dataclasses
    fields = {f.name for f in dataclasses.fields(Stages)}
    assert fields == {"mask", "generate", "facelock", "score", "generate_fallback"}
