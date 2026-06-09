import math
from models.governor.fat_loss import compute_lean_penalty, weekly_fat_loss_kg, muscle_loss_fraction

# --- deceleration penalty (M practical floor 7, full rate >= 15%) ---
def test_lean_penalty_full_rate_when_fat_plentiful():
    assert compute_lean_penalty(20.0, "M") == 1.0
def test_lean_penalty_zero_at_practical_floor():
    assert compute_lean_penalty(7.0, "M") == 0.0
def test_lean_penalty_decelerates_near_floor():
    # 11% -> t=(11-7)/8=0.5 -> 0.5**1.5 = 0.3536 (slows hard near the floor)
    assert math.isclose(compute_lean_penalty(11.0, "M"), 0.3536, abs_tol=0.01)
def test_lean_penalty_is_sex_specific():
    # female practical floor 16, ceiling 24; at 20% -> t=0.5 -> 0.3536
    assert math.isclose(compute_lean_penalty(20.0, "F"), 0.3536, abs_tol=0.01)

# --- weekly fat loss honors the ESSENTIAL floor (hard stop) ---
def test_weekly_fat_loss_cannot_cross_essential_floor():
    # M at 5% bf (essential floor) -> zero further loss no matter the deficit
    assert weekly_fat_loss_kg(daily_balance=-1000, current_weight_kg=87.0, current_bf_pct=5.0, sex="M") == 0.0
def test_weekly_fat_loss_capped_to_available_fat():
    # M 87kg at 5.5% -> available above 5% floor = 87*(0.055-0.05)=0.435kg; can't lose more in a week
    loss = weekly_fat_loss_kg(daily_balance=-1000, current_weight_kg=87.0, current_bf_pct=5.5, sex="M")
    assert loss <= 0.435 + 1e-9
def test_weekly_fat_loss_reasonable_when_plentiful():
    # M 87kg 20%, -500/day -> ~0.4545 kg/wk (500*7/7700), full penalty
    loss = weekly_fat_loss_kg(daily_balance=-500, current_weight_kg=87.0, current_bf_pct=20.0, sex="M")
    assert math.isclose(loss, 0.4545, abs_tol=0.02)

# --- muscle preservation depends on loss rate ---
def test_muscle_loss_fraction_tiers():
    assert muscle_loss_fraction(0.5) == 0.05   # slow = optimal
    assert muscle_loss_fraction(0.8) == 0.15   # moderate
    assert muscle_loss_fraction(1.2) == 0.30   # aggressive = muscle loss
