"""Map the app's friendly request payload onto the engine's exact schemas.

The mobile app speaks imperial units and simple pickers; the engine
(models.governor) speaks metric dataclasses. This pure function is the seam, and
the only real logic in the backend — so it's unit-tested. No I/O here.
"""
from __future__ import annotations

from typing import Tuple

from models.governor.schemas import GoalSpec, NutritionSpec, TrainingSpec, UserProfile

KG, INCH = 0.453592, 0.0254

_EXPERIENCE_YEARS = {"beginner": 0.5, "intermediate": 2.0, "advanced": 5.0}
_VALID_GOALS = {"fat_loss", "muscle_gain", "recomp", "maintenance"}
_VALID_SEX = {"M", "F"}


def to_engine_inputs(payload: dict) -> Tuple[UserProfile, GoalSpec, NutritionSpec,
                                             TrainingSpec, int]:
    """Validate + convert a /transform payload into (profile, goal, nutrition,
    training, weeks). Raises ValueError on invalid enums."""
    sex = str(payload["sex"]).upper()
    if sex not in _VALID_SEX:
        raise ValueError(f"sex must be one of {sorted(_VALID_SEX)}, got {sex!r}")

    goal_name = str(payload["goal"])
    if goal_name not in _VALID_GOALS:
        raise ValueError(f"goal must be one of {sorted(_VALID_GOALS)}, got {goal_name!r}")

    experience = str(payload.get("experience", "intermediate"))
    if experience not in _EXPERIENCE_YEARS:
        raise ValueError(f"experience must be one of {sorted(_EXPERIENCE_YEARS)}, "
                         f"got {experience!r}")

    profile = UserProfile(
        age=int(payload["age"]),
        sex=sex,
        height_m=float(payload["height_in"]) * INCH,
        weight_kg=float(payload["weight_lb"]) * KG,
        bf_pct=float(payload["bf_pct"]),
        years_training=_EXPERIENCE_YEARS[experience],
        bf_estimated=True,
    )

    lean_pref = "lean_bulk" if goal_name == "muscle_gain" else "standard"
    goal = GoalSpec(primary=goal_name, lean_preference=lean_pref)

    # Slice defaults — full onboarding will populate these from real user input.
    nutrition = NutritionSpec(tracking_method="none")
    training = TrainingSpec(days_per_week=4)

    return profile, goal, nutrition, training, int(payload["weeks"])
