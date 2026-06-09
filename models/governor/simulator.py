"""Stage 4: the core weekly-state simulator. Integrates energy balance, gain rates,
the FFMI ceiling, and the fat-loss floor/deceleration into an explicit week-by-week
rollout (replaces the old global S-curve). Independent re-evaluation each week is what
makes the body-fat floor enforce correctly."""
from __future__ import annotations
from typing import List
from .schemas import UserProfile, GoalSpec, NutritionSpec, TrainingSpec, WeeklyState
from . import energy_balance, gain_rates, fat_loss

# Condition-stratified recomp lean-gain factor (fraction of surplus rate).
_RECOMP_FACTOR = {"beginner": 0.60, "intermediate": 0.40, "advanced": 0.20}


def _state(week, weight, fat, lean, height_m):
    return WeeklyState(week=week, weight_kg=weight, fat_mass_kg=fat, lean_mass_kg=lean,
                       bf_pct=fat / weight * 100.0,
                       normalized_ffmi=gain_rates.compute_normalized_ffmi(lean, height_m))


def simulate_weekly(profile: UserProfile, goal: GoalSpec, nutrition: NutritionSpec,
                    training: TrainingSpec, horizon_weeks: int) -> List[WeeklyState]:
    tdee = energy_balance.compute_tdee(profile, training)
    balance = energy_balance.compute_daily_balance(goal, nutrition, tdee, profile)
    is_recomp = goal.primary == "recomp"
    in_deficit = balance < 0

    weight = profile.weight_kg
    fat = profile.weight_kg * profile.bf_pct / 100.0
    lean = profile.weight_kg - fat
    lean_floor = lean * 0.90  # sanity: never lose >10% LBM
    h = profile.height_m

    timeline = [_state(0, weight, fat, lean, h)]
    for week in range(1, horizon_weeks + 1):
        bf_pct = fat / weight * 100.0

        # --- fat change ---
        weekly_fat_loss = fat_loss.weekly_fat_loss_kg(balance, weight, bf_pct, profile.sex) if in_deficit else 0.0
        # surplus -> modest fat gain proportional to surplus (partitioning; leaner+trained store less)
        weekly_fat_gain = (balance * 7 / 7700.0) * gain_rates.surplus_fat_fraction(profile.experience_level, profile.sex) if balance > 0 else 0.0

        # --- lean change ---
        nffmi = gain_rates.compute_normalized_ffmi(lean, h)
        ceiling = gain_rates.ffmi_ceiling_factor(nffmi)
        base_monthly = gain_rates.aragon_helms_monthly_kg(weight, profile.experience_level, profile.sex)
        weekly_gain_potential = gain_rates.apply_gain_modifiers(base_monthly, profile, training, nutrition) * ceiling / 4.33

        weekly_lean = 0.0
        if balance > 0:                      # surplus: build muscle
            weekly_lean = weekly_gain_potential
        elif is_recomp:                      # near-maintenance: partial gain
            weekly_lean = weekly_gain_potential * _RECOMP_FACTOR[profile.experience_level]
        if in_deficit and not is_recomp:     # deficit: some lean lost with fat
            loss_pct_bw = (weekly_fat_loss / weight) * 100.0
            frac = fat_loss.muscle_loss_fraction(loss_pct_bw)
            weekly_lean = -weekly_fat_loss * (frac / (1 - frac))

        fat = max(0.0, fat - weekly_fat_loss + weekly_fat_gain)
        lean = max(lean_floor, lean + weekly_lean)
        weight = fat + lean
        timeline.append(_state(week, weight, fat, lean, h))

    return timeline
