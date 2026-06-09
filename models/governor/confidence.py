"""Stage 6: principled confidence + interval width. Each factor reflects a real source
of prediction error (NUTRITION_RESEARCH.md §8.2), not data completeness. Returns
(score in 0..1, ci_half_width as a fraction of the predicted change)."""
from __future__ import annotations
from .schemas import UserProfile, NutritionSpec, TrainingSpec

_TRACK = {"weighing": 1.00, "app": 0.90, "eyeballing": 0.65, "none": 0.50}
_EXP = {"beginner": 0.85, "intermediate": 0.95, "advanced": 0.90}


def compute_confidence(profile: UserProfile, nutrition: NutritionSpec,
                       training: TrainingSpec, horizon_weeks: int):
    tracking = _TRACK[nutrition.tracking_method]
    horizon = max(0.55, 1.0 - (horizon_weeks / 52) * 0.35)
    bf_quality = 1.0 if not profile.bf_estimated else 0.85
    protein = 1.0 if nutrition.protein_known else 0.80
    consistency = 0.70  # people overestimate adherence; raised once we log real workouts
    experience = _EXP[profile.experience_level]
    score = (tracking * 0.25 + horizon * 0.25 + bf_quality * 0.15
             + protein * 0.15 + consistency * 0.10 + experience * 0.10)
    ci_half_width = 0.15 + (1.0 - score) * 0.50
    return score, ci_half_width
