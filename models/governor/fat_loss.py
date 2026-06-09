"""Stage 3/4: fat-loss dynamics with a hard essential-fat floor and deceleration
near the practical floor (fixes the '5.1% in 6 months' bug). Garthe 2011 (PMID 21558571)
informs the muscle-preservation tiers."""
from __future__ import annotations
from . import constants


def compute_lean_penalty(current_bf_pct: float, sex: str) -> float:
    """Fat loss decelerates as body fat approaches the practical floor.
    1.0 when fat is plentiful (>= floor+8 pp), concave decay to 0.0 at the floor."""
    floor = constants.PRACTICAL_FAT_FLOOR[sex]
    ceiling = floor + 8.0
    if current_bf_pct >= ceiling:
        return 1.0
    if current_bf_pct <= floor:
        return 0.0
    t = (current_bf_pct - floor) / (ceiling - floor)
    return t ** 1.5


def weekly_fat_loss_kg(daily_balance: float, current_weight_kg: float,
                       current_bf_pct: float, sex: str) -> float:
    """Fat mass lost this week (kg). Theoretical thermodynamic loss, scaled by the
    deceleration penalty, hard-capped so body fat never crosses the essential floor."""
    if daily_balance >= 0:
        return 0.0
    theoretical = (abs(daily_balance) * 7) / constants.KCAL_PER_KG_FAT
    penalty = compute_lean_penalty(current_bf_pct, sex)
    desired = theoretical * penalty
    fat_mass_kg = current_weight_kg * current_bf_pct / 100.0
    essential_floor_mass = current_weight_kg * constants.ESSENTIAL_FAT_FLOOR[sex] / 100.0
    available = max(0.0, fat_mass_kg - essential_floor_mass)
    return min(desired, available)


def muscle_loss_fraction(weekly_loss_as_pct_bw: float) -> float:
    """Fraction of weekly loss that is lean tissue, by speed of loss (Garthe 2011)."""
    if weekly_loss_as_pct_bw > 1.0:
        return 0.30
    if weekly_loss_as_pct_bw > 0.7:
        return 0.15
    return 0.05
