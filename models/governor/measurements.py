"""Stage 5: translate fat/lean mass change (kg) into regional measurement deltas (cm).
Coefficients calibrated from anthropometric regressions (Kaggle bodyfat dataset family);
applied to the final delta, not weekly (measurement noise is high)."""
from __future__ import annotations
from typing import Dict, List, Optional


def compute_measurement_deltas(fat_change_kg: float, lean_change_kg: float,
                               focus_groups: Optional[List[str]] = None) -> Dict[str, float]:
    upper = lean_change_kg * 0.60   # default 60% upper / 40% lower allocation
    lower = lean_change_kg * 0.40
    return {
        "waist_cm":  fat_change_kg * 2.5,
        "chest_cm":  upper * 1.8 + fat_change_kg * 0.8,
        "arms_cm":   upper * 0.6,
        "thighs_cm": lower * 0.8,
        "hips_cm":   fat_change_kg * 1.5 + lower * 0.4,
    }
