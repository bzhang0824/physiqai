import math
from models.governor.schemas import UserProfile
from models.governor.energy_balance import compute_bmr

def lbs(x): return x * 0.453592
def inch(x): return x * 0.0254

def test_bmr_mifflin_st_jeor_male_known_value():
    # 24M, 192 lb, 72 in -> Mifflin-St Jeor = 10*87.09 + 6.25*182.88 - 5*24 + 5 = 1898.9
    p = UserProfile(age=24, sex="M", height_m=inch(72), weight_kg=lbs(192), bf_pct=11, years_training=5)
    assert math.isclose(compute_bmr(p), 1898.9, abs_tol=1.0)

def test_bmr_female_uses_minus_161_constant():
    # Same body, female: -161 instead of +5 -> 1898.9 - 166 = 1732.9
    p = UserProfile(age=24, sex="F", height_m=inch(72), weight_kg=lbs(192), bf_pct=20, years_training=5)
    assert math.isclose(compute_bmr(p), 1732.9, abs_tol=1.0)


from models.governor.schemas import GoalSpec, NutritionSpec, TrainingSpec
from models.governor.energy_balance import compute_tdee, compute_daily_balance

def _p(sex="M", bf=11, yrs=5):
    return UserProfile(age=24, sex=sex, height_m=inch(72), weight_kg=lbs(192), bf_pct=bf, years_training=yrs)

def test_tdee_5_days_uses_active_factor_1_55():
    # BMR 1898.9 * 1.55 (5 lifting days, no cardio) = 2943.3
    assert math.isclose(compute_tdee(_p(), TrainingSpec(days_per_week=5)), 2943.3, abs_tol=2.0)

def test_lean_bulk_advanced_is_small_surplus_not_aggressive():
    # Bug #2 fix: advanced lean_bulk = +100 kcal, NOT a fat-piling +300/+400
    bal = compute_daily_balance(GoalSpec(primary="muscle_gain", lean_preference="lean_bulk"),
                                NutritionSpec(), tdee=2943.3, profile=_p())
    assert math.isclose(bal, 100.0, abs_tol=1.0)

def test_aggressive_bulk_beginner_is_large_surplus():
    bal = compute_daily_balance(GoalSpec(primary="muscle_gain", lean_preference="aggressive_bulk"),
                                NutritionSpec(), tdee=2943.3, profile=_p(yrs=0.5))
    assert math.isclose(bal, 600.0, abs_tol=1.0)

def test_fat_loss_is_a_deficit_scaled_by_bodyfat():
    # lean male (11%) -> conservative 300 deficit; obese male would be 500
    lean = compute_daily_balance(GoalSpec(primary="fat_loss"), NutritionSpec(), tdee=2943.3, profile=_p(bf=11))
    obese = compute_daily_balance(GoalSpec(primary="fat_loss"), NutritionSpec(), tdee=2943.3, profile=_p(bf=30))
    assert lean == -300.0
    assert obese == -500.0

def test_recomp_is_small_deficit_and_maintenance_is_zero():
    assert compute_daily_balance(GoalSpec(primary="recomp"), NutritionSpec(), tdee=2943.3, profile=_p()) == -100.0
    assert compute_daily_balance(GoalSpec(primary="maintenance"), NutritionSpec(), tdee=2943.3, profile=_p()) == 0.0

def test_user_provided_calories_override_inference():
    bal = compute_daily_balance(GoalSpec(primary="muscle_gain"), NutritionSpec(daily_calories=3200),
                                tdee=2943.3, profile=_p())
    assert math.isclose(bal, 3200 - 2943.3, abs_tol=0.1)
