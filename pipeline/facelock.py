"""Face-lock: the hard identity backstop.

The image model paints a new body; face-lock then composites the user's REAL face
pixels back over the generated image so identity is guaranteed, not hoped-for.

Two layers:
- pure compositing math (feather_mask, composite_face) — deterministic, tested.
- face *detection* + the end-to-end apply_facelock — uses OpenCV's bundled face
  detector and is exercised by the live smoke test.
"""
from __future__ import annotations

from typing import Optional, Tuple

import numpy as np


def feather_mask(shape_hw: Tuple[int, int], box: Tuple[int, int, int, int],
                 feather: int) -> np.ndarray:
    """Soft elliptical mask: ~1 inside `box`, ~0 outside, smooth `feather`-px edge.

    box = (x0, y0, x1, y1). Returned array is float32 in [0, 1], shape (H, W).
    """
    h, w = shape_hw
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    rx, ry = max(1.0, (x1 - x0) / 2.0), max(1.0, (y1 - y0) / 2.0)

    ys, xs = np.ogrid[0:h, 0:w]
    # normalized elliptical distance: <=1 inside the ellipse, >1 outside
    dist = np.sqrt(((xs - cx) / rx) ** 2 + ((ys - cy) / ry) ** 2)

    # feather expressed as a fraction of the ellipse radius
    edge = max(feather, 1) / max(rx, ry)
    # 1 where dist<=1, ramps to 0 over the feather band beyond the boundary
    mask = np.clip((1.0 + edge - dist) / edge, 0.0, 1.0)
    return mask.astype(np.float32)


def composite_face(base: np.ndarray, face: np.ndarray,
                   box: Tuple[int, int, int, int], feather: int = 12) -> np.ndarray:
    """Blend `face` over `base` within a feathered ellipse at `box`. uint8 in/out."""
    mask = feather_mask(base.shape[:2], box, feather)[:, :, None]
    out = base.astype(np.float32) * (1.0 - mask) + face.astype(np.float32) * mask
    return np.clip(out, 0, 255).astype(np.uint8)


def detect_face_box(img_rgb: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
    """Largest frontal face box (x0, y0, x1, y1) via OpenCV's bundled detector, or None."""
    import cv2

    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
    if len(faces) == 0:
        return None
    x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])
    # pad to include hair/jaw, which the face box clips
    pad_x, pad_y = int(fw * 0.25), int(fh * 0.45)
    h, w = img_rgb.shape[:2]
    x0 = max(0, x - pad_x); y0 = max(0, y - pad_y)
    x1 = min(w, x + fw + pad_x); y1 = min(h, y + fh + pad_y)
    return (x0, y0, x1, y1)


def apply_facelock(original_rgb: np.ndarray, generated_rgb: np.ndarray,
                   feather: int = 18) -> Tuple[np.ndarray, bool]:
    """Composite the original face onto the generated image.

    Returns (image, locked). `locked` is False if no face was found in the
    original (then the generated image is returned unchanged). Assumes the edit
    preserved pose/framing (true for prompt-based identity-preserving edits), so
    the face sits in ~the same place; we composite at the original's face box.
    """
    box = detect_face_box(original_rgb)
    if box is None:
        return generated_rgb, False
    if generated_rgb.shape != original_rgb.shape:
        import cv2
        generated_rgb = cv2.resize(generated_rgb,
                                   (original_rgb.shape[1], original_rgb.shape[0]))
    return composite_face(generated_rgb, original_rgb, box, feather), True
