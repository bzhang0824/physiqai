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


def test_identity_score_falls_back_when_torch_missing_at_call_time(monkeypatch):
    """The torch import is lazy (inside face_cosine), so a missing torch on the
    deployed box only surfaces when the scorer RUNS — not when it's imported.
    This is the bug that crashed the first live Railway generation."""
    from pipeline import stages, identity_score

    def _no_torch(*_args, **_kwargs):
        raise ModuleNotFoundError("No module named 'torch'")

    monkeypatch.setattr(identity_score, "face_cosine", _no_torch)
    monkeypatch.setattr(stages, "_load_rgb", lambda _p: np.zeros((4, 4, 3), np.uint8))
    monkeypatch.setattr(stages, "_warned_no_facenet", False)

    score = stages.identity_score("does-not-matter.jpg", np.zeros((4, 4, 3), np.uint8))
    assert score == 1.0
