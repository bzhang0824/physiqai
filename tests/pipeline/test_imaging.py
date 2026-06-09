"""TDD for pipeline.imaging.load_rgb — apply EXIF orientation when loading user photos.

iPhone photos store portrait orientation as an EXIF flag over landscape pixels.
PIL's Image.open does NOT auto-apply it, so without this the whole pipeline runs on
a sideways image (rotated output + the upright face detector misses → face-lock skips).
"""
import io
import pathlib
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from pipeline.imaging import load_rgb

_ORIENTATION_TAG = 274


def _jpeg_with_orientation(w, h, orientation):
    """A JPEG whose stored pixels are w×h with the given EXIF orientation flag."""
    img = Image.new("RGB", (w, h), (10, 10, 10))
    img.putpixel((0, 0), (255, 0, 0))        # top-left marker
    exif = img.getexif()
    exif[_ORIENTATION_TAG] = orientation
    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif, quality=95)
    buf.seek(0)
    return buf


def test_orientation_6_landscape_pixels_become_portrait():
    # stored 100×40 landscape, orientation 6 (rotate 90° CW on display) -> portrait
    arr = load_rgb(_jpeg_with_orientation(100, 40, 6))
    assert arr.shape[0] > arr.shape[1]       # height > width => portrait
    assert arr.shape[:2] == (100, 40)


def test_orientation_1_is_unchanged():
    # orientation 1 = "normal"; dims stay as stored (50 wide × 80 tall)
    arr = load_rgb(_jpeg_with_orientation(50, 80, 1))
    assert arr.shape[:2] == (80, 50)


def test_no_exif_image_loads_as_is():
    buf = io.BytesIO()
    Image.new("RGB", (80, 50)).save(buf, format="PNG")
    buf.seek(0)
    arr = load_rgb(buf)
    assert arr.shape[:2] == (50, 80)         # (height, width)


def test_accepts_a_path(tmp_path):
    p = tmp_path / "x.png"
    Image.new("RGB", (30, 20)).save(p)
    arr = load_rgb(str(p))
    assert arr.shape[:2] == (20, 30)
    assert arr.dtype == np.uint8


def test_returns_rgb_three_channels():
    p = _jpeg_with_orientation(40, 40, 1)
    arr = load_rgb(p)
    assert arr.ndim == 3 and arr.shape[2] == 3
