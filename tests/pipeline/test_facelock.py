"""TDD for pipeline.facelock compositing math (pure numpy/PIL).

Face *detection* is a model call (smoke-tested live); the *compositing* — build a
feathered elliptical mask in the face box and blend the real face over the
generated body — is deterministic and tested here with solid-color images.
"""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from pipeline.facelock import composite_face, feather_mask


def test_feather_mask_is_one_at_center_zero_at_edges():
    m = feather_mask((100, 100), box=(25, 25, 75, 75), feather=6)
    assert m.shape == (100, 100)
    assert m.max() <= 1.0 and m.min() >= 0.0
    assert m[50, 50] > 0.99       # center of box -> fully the face
    assert m[5, 5] < 0.01         # far corner -> fully the base


def test_feather_mask_has_a_soft_transition():
    m = feather_mask((100, 100), box=(25, 25, 75, 75), feather=8)
    # some intermediate (partial-blend) pixels must exist
    mid = ((m > 0.1) & (m < 0.9)).sum()
    assert mid > 0


def test_composite_takes_face_inside_box_and_base_outside():
    base = np.zeros((100, 100, 3), dtype=np.uint8)
    base[:] = (200, 0, 0)          # red body/background
    face = np.zeros((100, 100, 3), dtype=np.uint8)
    face[:] = (0, 0, 200)          # blue "real face"

    out = composite_face(base, face, box=(30, 30, 70, 70), feather=4)

    assert out.shape == base.shape
    # center of box -> mostly the blue face
    assert out[50, 50][2] > 150 and out[50, 50][0] < 60
    # far corner -> untouched red base
    assert out[2, 2][0] > 150 and out[2, 2][2] < 60


def test_composite_preserves_dtype_uint8():
    base = np.full((40, 40, 3), 100, dtype=np.uint8)
    face = np.full((40, 40, 3), 200, dtype=np.uint8)
    out = composite_face(base, face, box=(10, 10, 30, 30), feather=2)
    assert out.dtype == np.uint8
