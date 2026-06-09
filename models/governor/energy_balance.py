"""Stage 1: energy balance. BMR (Mifflin-St Jeor), TDEE, daily calorie balance."""
from __future__ import annotations
from .schemas import UserProfile


def compute_bmr(profile: UserProfile) -> float:
    """Basal Metabolic Rate via Mifflin-St Jeor (1990). kcal/day.
    BMR = 10*kg + 6.25*cm - 5*age + (5 male / -161 female)."""
    weight_kg = profile.weight_kg
    height_cm = profile.height_m * 100
    bmr = 10 * weight_kg + 6.25 * height_cm - 5 * profile.age
    bmr += 5 if profile.sex == "M" else -161
    return bmr


from .schemas import GoalSpec, NutritionSpec, TrainingSpec
from . import constants


def compute_tdee(profile: UserProfile, training: TrainingSpec) -> float:
    """Total Daily Energy Expenditure = BMR * activity factor (from weekly sessions)."""
    sessions = training.days_per_week + training.cardio_days_per_week
    if sessions <= 2:
        factor = 1.375
    elif sessions <= 4:
        factor = 1.46
    elif sessions <= 6:
        factor = 1.55
    else:
        factor = 1.72
    return compute_bmr(profile) * factor


def _deficit_by_bf(bf_pct: float, sex: str) -> float:
    """Body-fat-stratified deficit: leaner -> smaller deficit (preserve muscle)."""
    high = 20.0 if sex == "M" else 28.0
    if bf_pct >= high:
        return 500.0
    if bf_pct >= high - 8.0:
        return 400.0
    return 300.0


def compute_daily_balance(goal: GoalSpec, nutrition: NutritionSpec, tdee: float,
                          profile: UserProfile) -> float:
    """Daily calorie balance (kcal above/below TDEE). User-provided calories win."""
    if nutrition.daily_calories is not None:
        return nutrition.daily_calories - tdee
    if goal.primary == "muscle_gain":
        return float(constants.SURPLUS_BY_EXPERIENCE[profile.experience_level][goal.lean_preference])
    if goal.primary == "fat_loss":
        return -_deficit_by_bf(profile.bf_pct, profile.sex)
    if goal.primary == "recomp":
        return -100.0
    return 0.0
