"""TDD for server.inputs.to_engine_inputs: map the app's friendly payload
(imperial units, simple pickers) onto the engine's exact schemas."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from models.governor.schemas import GoalSpec, NutritionSpec, TrainingSpec, UserProfile
from server.inputs import to_engine_inputs

KG, INCH = 0.453592, 0.0254


def _payload(**over):
    base = dict(age=24, sex="M", height_in=72, weight_lb=192, bf_pct=11,
                experience="advanced", goal="fat_loss", weeks=26)
    base.update(over)
    return base


def test_returns_the_four_engine_specs_plus_weeks():
    profile, goal, nutrition, training, weeks = to_engine_inputs(_payload())
    assert isinstance(profile, UserProfile)
    assert isinstance(goal, GoalSpec)
    assert isinstance(nutrition, NutritionSpec)
    assert isinstance(training, TrainingSpec)
    assert weeks == 26


def test_unit_conversions_imperial_to_metric():
    profile, *_ = to_engine_inputs(_payload(height_in=72, weight_lb=192))
    assert profile.height_m == pytest.approx(72 * INCH)
    assert profile.weight_kg == pytest.approx(192 * KG)


def test_bodyfat_is_marked_estimated():
    profile, *_ = to_engine_inputs(_payload(bf_pct=11))
    assert profile.bf_pct == 11
    assert profile.bf_estimated is True


@pytest.mark.parametrize("experience,years", [
    ("beginner", 0.5), ("intermediate", 2.0), ("advanced", 5.0)])
def test_experience_maps_to_years_training(experience, years):
    profile, *_ = to_engine_inputs(_payload(experience=experience))
    assert profile.years_training == years
    assert profile.experience_level == experience


def test_goal_passes_through():
    _, goal, *_ = to_engine_inputs(_payload(goal="recomp"))
    assert goal.primary == "recomp"


def test_muscle_gain_defaults_to_lean_bulk():
    _, goal, *_ = to_engine_inputs(_payload(goal="muscle_gain"))
    assert goal.primary == "muscle_gain"
    assert goal.lean_preference == "lean_bulk"


def test_slice_defaults_for_nutrition_and_training():
    _, _, nutrition, training, _ = to_engine_inputs(_payload())
    assert nutrition.tracking_method == "none"
    assert training.days_per_week == 4


def test_string_numbers_are_coerced():
    # multipart form fields arrive as strings
    profile, _, _, _, weeks = to_engine_inputs(_payload(age="30", weight_lb="180", weeks="12"))
    assert profile.age == 30
    assert profile.weight_kg == pytest.approx(180 * KG)
    assert weeks == 12


def test_invalid_goal_raises():
    with pytest.raises(ValueError):
        to_engine_inputs(_payload(goal="bulk_dirty"))


def test_invalid_sex_raises():
    with pytest.raises(ValueError):
        to_engine_inputs(_payload(sex="X"))


# --- full onboarding fields (all optional; old thin-slice payloads still work) ---
def test_recovery_fields_flow_into_profile():
    profile, *_ = to_engine_inputs(_payload(sleep_hrs=6, stress=8, genetic_potential="high"))
    assert profile.sleep_hrs_per_night == 6
    assert profile.stress_level == 8
    assert profile.genetic_potential == "high"


def test_recovery_defaults_when_absent():
    profile, *_ = to_engine_inputs(_payload())
    assert profile.sleep_hrs_per_night == 7.5
    assert profile.stress_level == 5
    assert profile.genetic_potential == "average"


def test_bf_method_measured_marks_not_estimated():
    profile, *_ = to_engine_inputs(_payload(bf_method="measured"))
    assert profile.bf_estimated is False


def test_bf_method_estimated_is_default():
    profile, *_ = to_engine_inputs(_payload(bf_method="estimated"))
    assert profile.bf_estimated is True
    profile2, *_ = to_engine_inputs(_payload())  # absent -> estimated
    assert profile2.bf_estimated is True


def test_years_training_direct_overrides_experience():
    profile, *_ = to_engine_inputs(_payload(years_training=4))
    assert profile.years_training == 4
    assert profile.experience_level == "advanced"


@pytest.mark.parametrize("volume,sets", [("low", 6), ("moderate", 12), ("high", 20)])
def test_volume_level_maps_to_sets(volume, sets):
    _, _, _, training, _ = to_engine_inputs(_payload(volume=volume))
    assert training.sets_per_muscle_per_week == sets


def test_training_fields_flow():
    _, _, _, training, _ = to_engine_inputs(
        _payload(intensity="intense", days_per_week=6, cardio_days=3,
                 focus_muscle_groups="chest,back,arms"))
    assert training.intensity == "intense"
    assert training.days_per_week == 6
    assert training.cardio_days_per_week == 3
    assert training.focus_muscle_groups == ["chest", "back", "arms"]


def test_protein_level_maps_to_grams_via_bodyweight():
    # high ~2.0 g/kg, weight 192 lb = 87.1 kg -> ~174 g
    _, _, nutrition, _, _ = to_engine_inputs(_payload(protein_level="high"))
    assert nutrition.protein_g == pytest.approx(192 * KG * 2.0, rel=0.01)


def test_protein_grams_direct_overrides_level():
    _, _, nutrition, _, _ = to_engine_inputs(_payload(protein_g=180, protein_level="low"))
    assert nutrition.protein_g == 180


def test_nutrition_fields_flow():
    _, _, nutrition, _, _ = to_engine_inputs(
        _payload(daily_calories=2600, tracking_method="weighing"))
    assert nutrition.daily_calories == 2600
    assert nutrition.tracking_method == "weighing"


def test_explicit_lean_preference_wins():
    _, goal, *_ = to_engine_inputs(_payload(goal="muscle_gain", lean_preference="aggressive_bulk"))
    assert goal.lean_preference == "aggressive_bulk"


def test_invalid_genetic_potential_raises():
    with pytest.raises(ValueError):
        to_engine_inputs(_payload(genetic_potential="superhuman"))


def test_invalid_volume_raises():
    with pytest.raises(ValueError):
        to_engine_inputs(_payload(volume="insane"))
