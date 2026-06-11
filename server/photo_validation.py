"""Photo pre-validation — pure module, no HTTP, no fal spend.

Checks in cost order (cheapest first):
  (a) Decode check: caller must handle load_rgb failures and 422 with
      '{role} photo: we couldn't read that image — try re-taking it'
  (b) Min resolution: min(h, w) >= 512
  (c) Face detection: front photo only (require_face=True)
"""
from __future__ import annotations

from typing import Optional, Tuple

import numpy as np


class PhotoValidationError(Exception):
    """Raised when a photo fails pre-flight validation."""

    def __init__(self, role: str, reason: str) -> None:
        self.role = role
        self.reason = reason
        super().__init__(f"{role}: {reason}")


def _detect_face(arr: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
    """Detect the largest frontal face; returns box (x0,y0,x1,y1) or None.

    Thin wrapper around pipeline.facelock.detect_face_box so tests can
    monkeypatch server.photo_validation._detect_face without touching the
    pipeline module.
    """
    from pipeline.facelock import detect_face_box
    return detect_face_box(arr)


def validate_photo_array(
    arr: np.ndarray,
    role: str,
    *,
    require_face: bool,
) -> None:
    """Validate a decoded RGB array.

    Parameters
    ----------
    arr:
        RGB uint8 array already loaded by load_rgb (decode errors are
        handled by the caller, not here).
    role:
        Human-readable name for the photo angle, e.g. "front", "side", "back".
        Included in every error message.
    require_face:
        When True (FRONT ONLY), run face detection and raise if no face found.

    Raises
    ------
    PhotoValidationError
        With a user-friendly message that includes `role`.
    """
    h, w = arr.shape[:2]

    # (b) Resolution check — run before face detection (cheaper)
    if min(h, w) < 512:
        raise PhotoValidationError(
            role,
            f"{role} photo: too small or blurry — use your phone's main camera",
        )

    # (c) Face detection — front only
    if require_face:
        box = _detect_face(arr)
        if box is None:
            raise PhotoValidationError(
                role,
                "front photo: we couldn't find a face — use a clear, well-lit, full-body photo",
            )
