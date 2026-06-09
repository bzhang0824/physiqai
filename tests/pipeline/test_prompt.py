"""TDD for pipeline.prompt: MorphSpec -> a bounded, identity-preserving edit prompt.

The prompt is the only natural-language guardrail in Arch A, so it must (1) state
the engine's magnitude, (2) forbid exaggeration, and (3) hard-lock identity/scene.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from pipeline.engine_bridge import MorphSpec
from pipeline.prompt import build_prompt

_MEAS = {"waist_cm": -4.0, "chest_cm": 1.0, "arms_cm": 0.5, "thighs_cm": 0.5}


def _spec(direction, weight_delta_lb, bf_before, bf_after, lean_delta_lb, months=6):
    return MorphSpec(
        direction=direction, months=months,
        weight_before_lb=192, weight_after_lb=192 + weight_delta_lb,
        weight_delta_lb=weight_delta_lb, bf_before=bf_before, bf_after=bf_after,
        bf_delta=bf_after - bf_before, lean_delta_lb=lean_delta_lb,
        measurements_cm=dict(_MEAS), confidence_score=0.7,
        confidence_lo_lb=weight_delta_lb * 0.8, confidence_hi_lb=weight_delta_lb * 1.2,
    )


# --- identity / scene lock is non-negotiable on EVERY prompt -----------------
def _all_specs():
    return [
        _spec("cut", -10, 14, 9, -0.5),
        _spec("gain", +14, 15, 15, 12),
        _spec("recomp", -2, 18, 15, 1.0),
        _spec("maintain", 0, 11, 11, 0),
    ]


def test_every_prompt_locks_identity_and_scene():
    for spec in _all_specs():
        p = build_prompt(spec).lower()
        assert "face" in p and "identity" in p
        assert "background" in p and "lighting" in p
        assert "pose" in p


def test_every_prompt_forbids_exaggeration():
    for spec in _all_specs():
        p = build_prompt(spec).lower()
        assert "bodybuilder" in p  # "not a stage/pro bodybuilder"
        assert "photorealistic" in p


# --- direction-specific content ---------------------------------------------
def test_cut_prompt_describes_fat_loss_magnitude():
    p = build_prompt(_spec("cut", -10, 14, 9, -0.5)).lower()
    assert "fat" in p
    assert "9" in p          # target bf
    assert "10" in p         # lb change magnitude


def test_gain_prompt_describes_added_muscle():
    p = build_prompt(_spec("gain", +14, 15, 15, 12)).lower()
    assert "muscle" in p
    assert "12" in p         # lean lb added
    assert "natural" in p


def test_recomp_prompt_mentions_both_fat_loss_and_muscle():
    p = build_prompt(_spec("recomp", -2, 18, 15, 1.0)).lower()
    assert "fat" in p and "muscle" in p


def test_maintain_prompt_is_conservative():
    p = build_prompt(_spec("maintain", 0, 11, 11, 0)).lower()
    # no dramatic change language
    assert "minimal" in p or "subtle" in p or "maintain" in p
