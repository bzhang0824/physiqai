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


# --- per-region, engine-number-driven content (the moat) ---------------------
def test_prompt_renders_per_region_cm_deltas():
    """Each non-negligible measurement delta becomes a calibrated body-part phrase."""
    spec = _spec("gain", +14, 15, 15, 12)
    spec.measurements_cm = {"chest_cm": 4.2, "arms_cm": 1.8, "waist_cm": 0.3, "thighs_cm": 1.1}
    p = build_prompt(spec).lower()
    assert "chest" in p and "4 cm" in p        # big delta -> stated in cm
    assert "arms" in p and "2 cm" in p
    assert "thighs" in p
    # 0.3 cm waist is below the negligible floor -> not instructed
    assert "waist" not in p


def test_prompt_calibrates_language_to_magnitude():
    """Small delta -> 'slightly'; large delta -> 'clearly'. Anti over/undershoot."""
    small = _spec("gain", +5, 15, 15, 4)
    small.measurements_cm = {"chest_cm": 1.0}
    assert "slightly" in build_prompt(small).lower()

    big = _spec("gain", +20, 15, 15, 18)
    big.measurements_cm = {"chest_cm": 5.0}
    assert "clearly" in build_prompt(big).lower()


def test_negligible_regions_are_omitted():
    spec = _spec("recomp", -2, 18, 15, 1.0)
    spec.measurements_cm = {"chest_cm": 0.1, "arms_cm": 0.2, "waist_cm": -2.5}
    p = build_prompt(spec).lower()
    assert "chest" not in p and "arms" not in p   # both below 0.4 cm
    assert "waist" in p                            # 2.5 cm is real


# ---------------------------------------------------------------------------
# multi-ref support: build_prompt(spec, ref_angles=...) — new API
# ---------------------------------------------------------------------------

# Captured from build_prompt at implementation time — used as the regression lock.
# Any change to build_prompt(spec) with NO ref_angles must break this test first.
# (spec uses _MEAS = {waist_cm: -4.0, chest_cm: 1.0, arms_cm: 0.5, thighs_cm: 0.5})
_BASELINE_SPEC_OUTPUT = "Edit this exact photo to show the SAME person after a realistic 6-month fat-loss program. Body fat from ~14% down to ~9% (about 10 lb lighter), keeping the same muscle size. Specifically: chest and upper back slightly fuller and broader (~1 cm); arms slightly fuller with more muscle; waist clearly tighter and slimmer (~4 cm); thighs slightly fuller and stronger. The fat loss should be clearly visible but believable for 6 months — a tighter waist and more defined muscle, not a dramatic crash transformation. Natural, realistic natural-lifter result, NOT a stage or professional bodybuilder, no oil, no extreme vascularity, no exaggeration. CRITICAL: keep the face, hair, skin tone and identity EXACTLY the same; keep the same pose, body position, clothing, background, lighting, camera angle and image quality. Photorealistic, natural result."


def _cut_spec():
    return _spec("cut", -10, 14, 9, -0.5)


def test_empty_ref_angles_output_byte_identical_to_baseline():
    """REGRESSION LOCK: build_prompt(spec) with empty ref_angles must be byte-identical
    to the current implementation's output (no-change guarantee)."""
    assert build_prompt(_cut_spec()) == _BASELINE_SPEC_OUTPUT
    assert build_prompt(_cut_spec(), ref_angles=()) == _BASELINE_SPEC_OUTPUT
    assert build_prompt(_cut_spec(), ref_angles=[]) == _BASELINE_SPEC_OUTPUT


def test_ref_angles_back_prepends_preamble():
    p = build_prompt(_cut_spec(), ref_angles=("back",))
    # preamble must come first
    assert p.startswith("You are given multiple photos")
    # preamble names the angle
    assert "back" in p
    # body content still present somewhere
    assert "fat-loss" in p or "fat loss" in p


def test_ref_angles_side_back_names_both_angles():
    p = build_prompt(_cut_spec(), ref_angles=("side", "back"))
    assert "side" in p and "back" in p


def test_ref_angles_preamble_first_image_is_to_edit():
    p = build_prompt(_cut_spec(), ref_angles=("back",))
    idx_preamble = p.index("FIRST image is the photo to edit")
    idx_body = p.index("Edit this exact photo")
    assert idx_preamble < idx_body


def test_ref_angles_lock_clause_still_present():
    p = build_prompt(_cut_spec(), ref_angles=("back",))
    assert "face" in p and "identity" in p
    assert "background" in p and "lighting" in p


def test_ref_angles_no_exaggeration_clause_still_present():
    p = build_prompt(_cut_spec(), ref_angles=("side",))
    assert "bodybuilder" in p.lower()
    assert "photorealistic" in p.lower()


def test_ref_angles_preamble_mentions_body_proportions():
    p = build_prompt(_cut_spec(), ref_angles=("back",))
    # preamble should instruct "ground truth for... body proportions"
    assert "body proportions" in p or "proportions" in p


def test_ref_angles_preamble_says_not_to_blend_poses():
    p = build_prompt(_cut_spec(), ref_angles=("back",))
    assert "collage" in p or "blend" in p
