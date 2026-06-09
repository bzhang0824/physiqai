"""Map the app's friendly request payload onto the engine's exact schemas.

The mobile app speaks imperial units and simple pickers; the engine
(models.governor) speaks metric dataclasses. This pure function is the seam, and
the only real logic in the backend — so it's unit-tested. No I/O here.

All onboarding fields beyond the core 8 are optional with sensible defaults, so
older thin-slice clients keep working.
"""
from __future__ import annotations

from typing import Optional, Tuple

from models.governor.schemas import GoalSpec, NutritionSpec, TrainingSpec, UserProfile

KG, INCH = 0.453592, 0.0254

_EXPERIENCE_YEARS = {"beginner": 0.5, "intermediate": 2.0, "advanced": 5.0}
_VALID_GOALS = {"fat_loss", "muscle_gain", "recomp", "maintenance"}
_VALID_SEX = {"M", "F"}
_VALID_GENETIC = {"low", "average", "high"}
_VALID_INTENSITY = {"light", "moderate", "intense"}
_VALID_TRACKING = {"weighing", "app", "eyeballing", "none"}
_VALID_LEAN_PREF = {"standard", "lean_bulk", "aggressive_bulk"}
_VOLUME_SETS = {"low": 6, "moderate": 12, "high": 20}
_PROTEIN_G_PER_KG = {"low": 1.0, "moderate": 1.6, "high": 2.0}


def _enum(payload, key, valid, default=None):
    if key not in payload or payload[key] in (None, ""):
        return default
    val = str(payload[key])
    if val not in valid:
        raise ValueError(f"{key} must be one of {sorted(valid)}, got {val!r}")
    return val


def _opt_float(payload, key):
    v = payload.get(key)
    return None if v in (None, "") else float(v)


def _opt_int(payload, key):
    v = payload.get(key)
    return None if v in (None, "") else int(v)


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

    experience = _enum(payload, "experience", set(_EXPERIENCE_YEARS), "intermediate")
    # years_training: use direct value if given, else derive from the experience picker
    years = _opt_float(payload, "years_training")
    if years is None:
        years = _EXPERIENCE_YEARS[experience]

    bf_method = _enum(payload, "bf_method", {"estimated", "measured"}, "estimated")
    genetic = _enum(payload, "genetic_potential", _VALID_GENETIC, "average")

    profile = UserProfile(
        age=int(payload["age"]),
        sex=sex,
        height_m=float(payload["height_in"]) * INCH,
        weight_kg=float(payload["weight_lb"]) * KG,
        bf_pct=float(payload["bf_pct"]),
        years_training=years,
        sleep_hrs_per_night=float(payload.get("sleep_hrs") or 7.5),
        stress_level=int(payload.get("stress") or 5),
        genetic_potential=genetic,
        bf_estimated=(bf_method != "measured"),
    )

    # Goal + bulk preference (explicit wins; muscle_gain defaults to a lean bulk)
    lean_pref = _enum(payload, "lean_preference", _VALID_LEAN_PREF)
    if lean_pref is None:
        lean_pref = "lean_bulk" if goal_name == "muscle_gain" else "standard"
    goal = GoalSpec(primary=goal_name, lean_preference=lean_pref)

    # Nutrition: explicit grams win, else a level maps via bodyweight, else unknown
    protein_g = _opt_float(payload, "protein_g")
    if protein_g is None:
        level = _enum(payload, "protein_level", set(_PROTEIN_G_PER_KG))
        if level is not None:
            protein_g = profile.weight_kg * _PROTEIN_G_PER_KG[level]
    nutrition = NutritionSpec(
        daily_calories=_opt_int(payload, "daily_calories"),
        protein_g=protein_g,
        tracking_method=_enum(payload, "tracking_method", _VALID_TRACKING, "none"),
    )

    # Training: volume level -> sets; intensity/cardio/days/focus
    volume = _enum(payload, "volume", set(_VOLUME_SETS))
    sets = _VOLUME_SETS[volume] if volume is not None else 12
    focus_raw = payload.get("focus_muscle_groups") or ""
    focus = [g.strip() for g in str(focus_raw).split(",") if g.strip()]
    training = TrainingSpec(
        days_per_week=int(payload.get("days_per_week") or 4),
        sets_per_muscle_per_week=sets,
        intensity=_enum(payload, "intensity", _VALID_INTENSITY, "moderate"),
        cardio_days_per_week=int(payload.get("cardio_days") or 0),
        focus_muscle_groups=focus,
    )

    return profile, goal, nutrition, training, int(payload["weeks"])
