import math
from models.governor.schemas import UserProfile, GoalSpec, NutritionSpec, TrainingSpec
from models.governor.simulator import simulate_weekly
def inch(x): return x*0.0254
def lbs(x): return x*0.453592

def brian():
    return UserProfile(age=24, sex="M", height_m=inch(72), weight_kg=lbs(192), bf_pct=11,
                       years_training=5, sleep_hrs_per_night=7.5)

def test_THE_headline_fix_lean_cut_lands_realistic_not_5pct():
    # Brian's exact case that the OLD engine botched (predicted 5.1%). New engine must land ~8-9%.
    tl = simulate_weekly(brian(), GoalSpec(primary="fat_loss"), NutritionSpec(),
                         TrainingSpec(days_per_week=5), horizon_weeks=26)
    assert len(tl) == 27                      # week 0..26
    final = tl[-1]
    assert 7.5 <= final.bf_pct <= 9.5, f"got {final.bf_pct:.1f}% (old engine said 5.1%)"
    assert final.weight_kg < brian().weight_kg          # lost weight
    assert all(s.bf_pct >= 7.0 - 1e-6 for s in tl)      # never crosses practical floor

def test_essential_floor_holds_even_with_absurd_deficit():
    # 1500 kcal/day deficit for a year still cannot push below the essential floor (5% M)
    tl = simulate_weekly(brian(), GoalSpec(primary="fat_loss"),
                         NutritionSpec(daily_calories=1400), TrainingSpec(days_per_week=6),
                         horizon_weeks=52)
    assert min(s.bf_pct for s in tl) >= 5.0 - 1e-6

def test_lean_bulk_gains_modest_muscle_and_respects_ceiling():
    tl = simulate_weekly(brian(), GoalSpec(primary="muscle_gain", lean_preference="lean_bulk"),
                         NutritionSpec(protein_g=170), TrainingSpec(days_per_week=5), horizon_weeks=26)
    final, start = tl[-1], tl[0]
    lean_gain = final.lean_mass_kg - start.lean_mass_kg
    assert 0.3 <= lean_gain <= 4.0          # realistic 6-mo lean gain for an advanced lifter
    assert final.normalized_ffmi <= 25.0    # never exceeds the natural ceiling
