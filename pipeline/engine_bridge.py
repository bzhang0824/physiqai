"""Bridge the physiology engine (models.governor) to a MorphSpec — the
structured set of facts the prompt builder and the user-facing report need.

This is the seam between the TRUTH layer (the validated engine) and the LOOK
layer (image generation). Keep it pure: numbers in, numbers out, no I/O.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from models.governor.predictor import predict
from models.governor.schemas import GoalSpec, NutritionSpec, TrainingSpec, UserProfile

KG = 0.453592


@dataclass
class MorphSpec:
    """Everything the image prompt + report need, in display units (lb, %, cm)."""

    direction: str  # "cut" | "gain" | "recomp" | "maintain"
    months: int

    weight_before_lb: float
    weight_after_lb: float
    weight_delta_lb: float

    bf_before: float
    bf_after: float
    bf_delta: float

    lean_delta_lb: float
    measurements_cm: Dict[str, float]

    confidence_score: float
    confidence_lo_lb: float
    confidence_hi_lb: float

    warnings: List[str] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)


def _direction(weight_delta_lb: float, bf_delta: float, lean_delta_lb: float) -> str:
    """Classify the visual transformation from the engine's numbers.

    What the image must show follows the deltas, not the stated goal: a recomp
    (lose fat *and* add muscle, weight ~flat) looks different from a pure cut
    (lose fat, muscle flat/down) even though both shed body fat.
    """
    gained_muscle = lean_delta_lb >= 0.3
    lost_fat = bf_delta <= -0.5

    if abs(weight_delta_lb) < 1.0 and abs(bf_delta) < 0.5 and abs(lean_delta_lb) < 0.3:
        return "maintain"
    if gained_muscle and weight_delta_lb >= 3.0:
        return "gain"
    if lost_fat and gained_muscle:
        return "recomp"
    if lost_fat:
        return "cut"
    if gained_muscle:
        return "gain"
    return "maintain"


def build_morph_spec(profile: UserProfile, goal: GoalSpec, nutrition: NutritionSpec,
                     training: TrainingSpec, weeks: int) -> MorphSpec:
    r = predict(profile, goal, nutrition, training, weeks)
    s, f = r.initial_state, r.final_state

    weight_delta_lb = (f.weight_kg - s.weight_kg) / KG
    bf_delta = f.bf_pct - s.bf_pct
    lean_delta_lb = (f.lean_mass_kg - s.lean_mass_kg) / KG
    lo, hi = r.confidence_range_lbs()

    return MorphSpec(
        direction=_direction(weight_delta_lb, bf_delta, lean_delta_lb),
        months=weeks // 4,
        weight_before_lb=s.weight_kg / KG,
        weight_after_lb=f.weight_kg / KG,
        weight_delta_lb=weight_delta_lb,
        bf_before=s.bf_pct,
        bf_after=f.bf_pct,
        bf_delta=bf_delta,
        lean_delta_lb=lean_delta_lb,
        measurements_cm=dict(r.measurement_deltas),
        confidence_score=r.confidence_score,
        confidence_lo_lb=min(lo, hi),
        confidence_hi_lb=max(lo, hi),
        warnings=list(r.warnings),
        insights=list(r.insights),
    )
