"""TDD for pipeline.engine_bridge: turn engine output into a MorphSpec
(the structured facts the prompt builder + report need)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from models.governor.schemas import UserProfile, GoalSpec, NutritionSpec, TrainingSpec
from pipeline.engine_bridge import build_morph_spec

KG, INCH = 0.453592, 0.0254


def _brian(weight_lb=192, bf=11, years=5, sex="M", age=24, height_in=72):
    return UserProfile(age=age, sex=sex, height_m=height_in * INCH,
                       weight_kg=weight_lb * KG, bf_pct=bf, years_training=years)


def test_fat_loss_profile_is_a_cut():
    spec = build_morph_spec(_brian(), GoalSpec(primary="fat_loss"),
                            NutritionSpec(), TrainingSpec(days_per_week=5), weeks=26)
    assert spec.direction == "cut"
    assert spec.months == 6
    assert spec.weight_delta_lb < 0
    assert spec.bf_delta < 0


def test_lean_bulk_profile_is_a_gain():
    # untrained lifter, lean-bulk muscle-gain over 6mo -> clear lean gain
    p = _brian(weight_lb=160, bf=15, years=0.3)
    spec = build_morph_spec(p, GoalSpec(primary="muscle_gain", lean_preference="lean_bulk"),
                            NutritionSpec(protein_g=p.weight_kg * 1.8),
                            TrainingSpec(days_per_week=5), weeks=26)
    assert spec.direction == "gain"
    assert spec.lean_delta_lb > 0
    assert spec.weight_delta_lb > 0


def test_recomp_profile_is_a_recomp():
    # trained lifter recomp: lose fat, gain/hold muscle, weight ~flat
    p = _brian(weight_lb=180, bf=18, years=3)
    spec = build_morph_spec(p, GoalSpec(primary="recomp"),
                            NutritionSpec(protein_g=p.weight_kg * 1.8),
                            TrainingSpec(days_per_week=4), weeks=16)
    assert spec.direction == "recomp"
    assert spec.bf_delta < 0


def test_maintenance_profile_is_maintain():
    p = _brian()
    spec = build_morph_spec(p, GoalSpec(primary="maintenance"),
                            NutritionSpec(), TrainingSpec(days_per_week=3), weeks=12)
    assert spec.direction == "maintain"


def test_measurements_and_confidence_carried_through():
    spec = build_morph_spec(_brian(), GoalSpec(primary="fat_loss"),
                            NutritionSpec(), TrainingSpec(days_per_week=5), weeks=26)
    assert set(spec.measurements_cm) >= {"waist_cm", "chest_cm", "arms_cm", "thighs_cm"}
    assert 0.0 <= spec.confidence_score <= 1.0
    assert spec.confidence_lo_lb <= spec.confidence_hi_lb
