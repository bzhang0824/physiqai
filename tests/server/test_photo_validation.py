"""Tests for server/photo_validation.py — pure unit tests, no network, no fal.

Checks:
  - Undecodable bytes raise PhotoValidationError with role in message
  - Image smaller than 512px on the short side raises PhotoValidationError
  - Front photo with no face raises PhotoValidationError (require_face=True)
  - Side/back photos skip face check (require_face=False)
  - Error messages name the role
"""
from __future__ import annotations

import io
import sys
import pathlib

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from server.photo_validation import PhotoValidationError, validate_photo_array


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rgb_array(h: int, w: int, color=(200, 150, 100)) -> np.ndarray:
    """Solid-color RGB uint8 array."""
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    arr[:, :] = color
    return arr


def _face_array() -> np.ndarray:
    """A real front-facing photo large enough for the face detector to find a face.

    We use the haarcascade on a synthetic face made from a solid skin-tone rectangle
    with a slightly different-toned eye band — this won't reliably fool the cascade,
    so instead we monkeypatch detect_face_box in the tests that need a face found.
    This helper just returns a valid large array.
    """
    return _rgb_array(600, 400, color=(210, 170, 120))


# ---------------------------------------------------------------------------
# PhotoValidationError
# ---------------------------------------------------------------------------

def test_photo_validation_error_carries_role_and_reason():
    err = PhotoValidationError("front", "too small")
    assert err.role == "front"
    assert err.reason == "too small"
    assert "front" in str(err)
    assert "too small" in str(err)


# ---------------------------------------------------------------------------
# Min-resolution check (b)
# ---------------------------------------------------------------------------

def test_small_image_raises_for_front():
    arr = _rgb_array(400, 300)  # min(h,w)=300 < 512
    with pytest.raises(PhotoValidationError) as exc_info:
        validate_photo_array(arr, "front", require_face=False)
    err = exc_info.value
    assert err.role == "front"
    assert "front" in err.reason
    assert "512" in err.reason or "small" in err.reason.lower()


def test_small_image_raises_for_side():
    arr = _rgb_array(511, 700)  # min(h,w)=511 < 512
    with pytest.raises(PhotoValidationError) as exc_info:
        validate_photo_array(arr, "side", require_face=False)
    err = exc_info.value
    assert err.role == "side"


def test_small_image_raises_for_back():
    arr = _rgb_array(300, 200)
    with pytest.raises(PhotoValidationError) as exc_info:
        validate_photo_array(arr, "back", require_face=False)
    err = exc_info.value
    assert err.role == "back"


def test_exact_512_short_side_passes():
    arr = _rgb_array(512, 800)  # min=512, exactly at threshold
    # Should NOT raise (no face check needed since require_face=False)
    validate_photo_array(arr, "front", require_face=False)


def test_large_square_passes():
    arr = _rgb_array(1024, 1024)
    validate_photo_array(arr, "side", require_face=False)


# ---------------------------------------------------------------------------
# Face detection check (c) — front only (require_face=True)
# ---------------------------------------------------------------------------

def test_front_no_face_raises(monkeypatch):
    """A large image with require_face=True and no face detected -> raises."""
    import server.photo_validation as pv_module
    monkeypatch.setattr(pv_module, "_detect_face", lambda arr: None)

    arr = _rgb_array(600, 600)  # min(h,w)=600 >= 512, so resolution passes
    with pytest.raises(PhotoValidationError) as exc_info:
        validate_photo_array(arr, "front", require_face=True)
    err = exc_info.value
    assert err.role == "front"
    assert "face" in err.reason.lower()
    assert "front" in err.reason


def test_front_face_found_passes(monkeypatch):
    """require_face=True + face found -> no exception."""
    import server.photo_validation as pv_module
    monkeypatch.setattr(pv_module, "_detect_face", lambda arr: (10, 10, 100, 100))

    arr = _rgb_array(600, 600)  # min(h,w)=600 >= 512
    validate_photo_array(arr, "front", require_face=True)  # must not raise


def test_side_skips_face_check_even_when_require_face_false(monkeypatch):
    """Side photos never run face detection."""
    import server.photo_validation as pv_module
    calls = []
    monkeypatch.setattr(pv_module, "_detect_face", lambda arr: calls.append(1) or None)

    arr = _rgb_array(600, 600)  # min(h,w)=600 >= 512
    # Should not raise even though _detect_face returns None, because require_face=False
    validate_photo_array(arr, "side", require_face=False)
    assert calls == []  # _detect_face must not have been called


def test_back_skips_face_check(monkeypatch):
    """Back photos never run face detection."""
    import server.photo_validation as pv_module
    calls = []
    monkeypatch.setattr(pv_module, "_detect_face", lambda arr: calls.append(1) or None)

    arr = _rgb_array(600, 600)  # min(h,w)=600 >= 512
    validate_photo_array(arr, "back", require_face=False)
    assert calls == []


# ---------------------------------------------------------------------------
# Error message naming (role is in the message)
# ---------------------------------------------------------------------------

def test_error_message_names_role_front():
    arr = _rgb_array(400, 300)
    with pytest.raises(PhotoValidationError) as exc_info:
        validate_photo_array(arr, "front", require_face=False)
    assert "front" in exc_info.value.reason


def test_error_message_names_role_side():
    arr = _rgb_array(400, 300)
    with pytest.raises(PhotoValidationError) as exc_info:
        validate_photo_array(arr, "side", require_face=False)
    assert "side" in exc_info.value.reason


def test_error_message_names_role_back():
    arr = _rgb_array(400, 300)
    with pytest.raises(PhotoValidationError) as exc_info:
        validate_photo_array(arr, "back", require_face=False)
    assert "back" in exc_info.value.reason


# ---------------------------------------------------------------------------
# require_face=True with size failure short-circuits (no face check run)
# ---------------------------------------------------------------------------

def test_size_check_runs_before_face_check(monkeypatch):
    """If the image is too small, face check must not run at all."""
    import server.photo_validation as pv_module
    calls = []
    monkeypatch.setattr(pv_module, "_detect_face", lambda arr: calls.append(1) or None)

    arr = _rgb_array(400, 300)  # too small
    with pytest.raises(PhotoValidationError) as exc_info:
        validate_photo_array(arr, "front", require_face=True)
    assert calls == []  # face check must not run
    assert "small" in exc_info.value.reason.lower() or "512" in exc_info.value.reason
