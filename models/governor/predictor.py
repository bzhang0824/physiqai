"""Orchestrator: one call -> a complete, honest GovernorResult.
Composes simulator + confidence + measurements and surfaces warnings
(softened near-FFMI-ceiling + body-fat-floor messaging per product decisions)."""
from __future__ import annotations
from .schemas import (UserProfile, GoalSpec, NutritionSpec, TrainingSpec, GovernorResult)
from . import simulator, confidence, measurements, constants


def predict(profile: UserProfile, goal: GoalSpec, nutrition: NutritionSpec,
            training: TrainingSpec, horizon_weeks: int) -> GovernorResult:
    tl = simulator.simulate_weekly(profile, goal, nutrition, training, horizon_weeks)
    start, final = tl[0], tl[-1]
    score, ci = confidence.compute_confidence(profile, nutrition, training, horizon_weeks)
    deltas = measurements.compute_measurement_deltas(
        fat_change_kg=final.fat_mass_kg - start.fat_mass_kg,
        lean_change_kg=final.lean_mass_kg - start.lean_mass_kg,
        focus_groups=training.focus_muscle_groups)

    warnings, insights = [], []
    # Softened near-natural-limit message (Brian Q4: reframe, don't lead with "you've hit your limit")
    if final.normalized_ffmi >= constants.FFMI_WARN:
        warnings.append("You're near your natural muscle limit — further size gains will be gradual. "
                        "Focus on recomposition, strength, and conditioning to keep progressing.")
    # Approaching sustainable body-fat floor
    floor = constants.PRACTICAL_FAT_FLOOR[profile.sex]
    if final.bf_pct <= floor + 1.0:
        warnings.append(f"You're approaching your sustainable body-fat floor (~{floor:.0f}%); "
                        f"getting leaner than this is hard to maintain.")
    lean_change = (final.lean_mass_kg - start.lean_mass_kg) / 0.453592
    if goal.primary == "fat_loss" and lean_change > -1.0:
        insights.append("Muscle largely preserved through the cut.")

    return GovernorResult(initial_state=start, final_state=final, weekly_timeline=tl,
                          mode=goal.primary, confidence_score=score, ci_half_width=ci,
                          measurement_deltas=deltas, warnings=warnings, insights=insights)
