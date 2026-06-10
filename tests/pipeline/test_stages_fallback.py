"""identity_score must degrade to pass-through when facenet/torch is absent —
a missing optional dep should never crash a paid generation."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import numpy as np


def test_identity_score_falls_back_without_facenet(monkeypatch):
    from pipeline import stages

    # Setting the module entry to None makes the lazy import raise ImportError.
    monkeypatch.setitem(sys.modules, "pipeline.identity_score", None)
    monkeypatch.setattr(stages, "_warned_no_facenet", False)

    score = stages.identity_score("does-not-matter.jpg", np.zeros((4, 4, 3), np.uint8))
    assert score == 1.0
