"""Shared image loading for user photos — the one place that normalizes EXIF orientation.

iPhone (and many phone) JPEGs encode portrait orientation as an EXIF flag over
landscape pixel data. PIL's Image.open does NOT apply it, so every consumer must load
through here or risk processing a sideways image (which both rotates the output and
breaks the upright face detector → face-lock silently skips).
"""
from __future__ import annotations

from typing import Union

import numpy as np
from PIL import Image, ImageOps

PathOrFile = Union[str, "os.PathLike", "io.IOBase"]


def load_rgb(src: PathOrFile) -> np.ndarray:
    """Open an image (path or file-like), apply EXIF orientation, return an RGB uint8 array."""
    img = Image.open(src)
    img = ImageOps.exif_transpose(img)  # idempotent / no-op when there's no EXIF
    return np.array(img.convert("RGB"))
