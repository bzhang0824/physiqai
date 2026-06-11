"""TDD for pipeline.run: the orchestration loop.

Stages (mask/generate/facelock/score) are I/O at the edges and injected here as
fakes — the orchestration *control flow* (retry, fallback, pick-best, always
face-lock) is the real behavior under test.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from pipeline.engine_bridge import MorphSpec
from pipeline.identity import IdentityPolicy
from pipeline.run import Stages, run_transformation


def _spec():
    return MorphSpec(
        direction="cut", months=6, weight_before_lb=192, weight_after_lb=182,
        weight_delta_lb=-10, bf_before=14, bf_after=9, bf_delta=-5,
        lean_delta_lb=-0.5, measurements_cm={"waist_cm": -4.0}, confidence_score=0.7,
        confidence_lo_lb=-12, confidence_hi_lb=-8,
    )


class FakeStages:
    """Records calls and returns scripted identity scores."""

    def __init__(self, scores, fallback_score=None):
        self.scores = list(scores)
        self.fallback_score = fallback_score
        self.calls = {"mask": 0, "generate": 0, "facelock": 0, "score": 0, "fallback": 0}
        self.last_prompt = None

    def mask(self, photo):
        self.calls["mask"] += 1
        return "BODY_MASK"

    def generate(self, photo, prompt, mask):
        self.calls["generate"] += 1
        self.last_prompt = prompt
        return f"gen{self.calls['generate']}"

    def generate_fallback(self, photo, prompt, mask):
        self.calls["fallback"] += 1
        return "gen_fallback"

    def facelock(self, photo, generated):
        self.calls["facelock"] += 1
        return f"locked:{generated}"

    def score(self, photo, candidate):
        self.calls["score"] += 1
        if candidate == "locked:gen_fallback":
            return self.fallback_score
        return self.scores.pop(0)

    def as_stages(self):
        return Stages(mask=self.mask, generate=self.generate, facelock=self.facelock,
                      score=self.score, generate_fallback=self.generate_fallback)


def test_happy_path_first_try_passes():
    fs = FakeStages(scores=[0.90])
    res = run_transformation("photo.jpg", _spec(), fs.as_stages())
    assert res.accepted is True
    assert res.attempts == 1
    assert res.used_fallback is False
    assert fs.calls["mask"] == 1
    assert fs.calls["generate"] == 1
    # the returned image always passed through face-lock
    assert str(res.image).startswith("locked:")


def test_retries_until_pass():
    fs = FakeStages(scores=[0.70, 0.90])
    res = run_transformation("photo.jpg", _spec(), fs.as_stages(),
                             policy=IdentityPolicy(max_attempts=3))
    assert res.accepted is True
    assert res.attempts == 2
    assert fs.calls["generate"] == 2
    assert fs.calls["fallback"] == 0


def test_falls_back_after_exhausting_attempts():
    fs = FakeStages(scores=[0.70, 0.71, 0.72], fallback_score=0.91)
    res = run_transformation("photo.jpg", _spec(), fs.as_stages(),
                             policy=IdentityPolicy(max_attempts=3))
    assert res.attempts == 3
    assert res.used_fallback is True
    assert res.accepted is True
    assert fs.calls["fallback"] == 1


def test_returns_best_candidate_even_when_none_pass():
    fs = FakeStages(scores=[0.60, 0.78, 0.65], fallback_score=0.70)
    res = run_transformation("photo.jpg", _spec(), fs.as_stages(),
                             policy=IdentityPolicy(max_attempts=3))
    assert res.accepted is False
    assert res.identity_score == 0.78  # the best of all attempts incl fallback


def test_prompt_is_built_from_spec_and_passed_to_generate():
    fs = FakeStages(scores=[0.90])
    run_transformation("photo.jpg", _spec(), fs.as_stages())
    assert "fat" in fs.last_prompt.lower()
    assert "identity" in fs.last_prompt.lower()


# ---------------------------------------------------------------------------
# ref_angles threads into the prompt
# ---------------------------------------------------------------------------

def test_ref_angles_default_empty_prompt_unchanged():
    """run_transformation with default ref_angles produces identical prompt to the old call."""
    fs_old = FakeStages(scores=[0.90])
    run_transformation("photo.jpg", _spec(), fs_old.as_stages())
    old_prompt = fs_old.last_prompt

    fs_new = FakeStages(scores=[0.90])
    run_transformation("photo.jpg", _spec(), fs_new.as_stages(), ref_angles=())
    assert fs_new.last_prompt == old_prompt


def test_ref_angles_back_threads_into_prompt():
    """run_transformation(ref_angles=('back',)) should produce a prompt with preamble."""
    fs = FakeStages(scores=[0.90])
    run_transformation("photo.jpg", _spec(), fs.as_stages(), ref_angles=("back",))
    assert "You are given multiple photos" in fs.last_prompt
    assert "back" in fs.last_prompt


def test_ref_angles_side_back_both_appear_in_prompt():
    fs = FakeStages(scores=[0.90])
    run_transformation("photo.jpg", _spec(), fs.as_stages(), ref_angles=("side", "back"))
    assert "side" in fs.last_prompt and "back" in fs.last_prompt
