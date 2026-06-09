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
