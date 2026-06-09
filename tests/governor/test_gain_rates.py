import math
from models.governor.gain_rates import compute_normalized_ffmi, ffmi_ceiling_factor

def test_normalized_ffmi_matches_kouri_formula():
    # 24M, lean ~77.51kg, height 1.8288m -> normalized FFMI ~= 23.0 (Kouri 1995)
    nffmi = compute_normalized_ffmi(lean_mass_kg=77.51, height_m=1.8288)
    assert math.isclose(nffmi, 23.0, abs_tol=0.1)

def test_ceiling_factor_full_below_22_zero_at_25():
    assert ffmi_ceiling_factor(20.0) == 1.0      # plenty of headroom
    assert ffmi_ceiling_factor(22.0) == 1.0      # boundary
    assert math.isclose(ffmi_ceiling_factor(23.0), 2/3, abs_tol=0.01)  # decaying
    assert math.isclose(ffmi_ceiling_factor(24.5), 1/6, abs_tol=0.01)  # near limit -> tiny
    assert ffmi_ceiling_factor(25.0) == 0.0      # natural ceiling: no further gain
    assert ffmi_ceiling_factor(26.0) == 0.0      # past ceiling clamps to 0


from models.governor.gain_rates import aragon_helms_monthly_kg, apply_gain_modifiers
from models.governor.schemas import UserProfile, TrainingSpec, NutritionSpec
def inch(x): return x*0.0254
def lbs(x): return x*0.453592

def test_aragon_helms_bodyweight_anchored_by_experience():
    w = 87.09  # 192 lb
    assert math.isclose(aragon_helms_monthly_kg(w, "advanced", "M"), w*0.00375, abs_tol=0.01)
    assert math.isclose(aragon_helms_monthly_kg(w, "intermediate", "M"), w*0.0075, abs_tol=0.01)
    assert math.isclose(aragon_helms_monthly_kg(w, "beginner", "M"), w*0.0125, abs_tol=0.01)

def test_female_absolute_rate_is_half_of_male():
    w = 60.0
    assert math.isclose(aragon_helms_monthly_kg(w, "intermediate", "F"),
                        aragon_helms_monthly_kg(w, "intermediate", "M") * 0.5, abs_tol=0.001)

def test_modifiers_are_bounded_and_penalize_poor_recovery():
    p_good = UserProfile(age=24, sex="M", height_m=inch(72), weight_kg=lbs(192), bf_pct=11,
                         years_training=5, sleep_hrs_per_night=8)
    p_bad = UserProfile(age=24, sex="M", height_m=inch(72), weight_kg=lbs(192), bf_pct=11,
                        years_training=5, sleep_hrs_per_night=5)
    base = 0.33
    good = apply_gain_modifiers(base, p_good, TrainingSpec(days_per_week=5), NutritionSpec(protein_g=160))
    bad  = apply_gain_modifiers(base, p_bad, TrainingSpec(days_per_week=5), NutritionSpec(protein_g=160))
    assert good >= bad            # poor sleep reduces gains
    assert 0.5*base <= bad <= base  # but stays bounded (no >2x or collapse)


from models.governor.gain_rates import surplus_fat_fraction
def test_surplus_partitioning_better_for_beginners_and_women():
    # P-ratio: less-trained & leaner partition surplus MORE to muscle (less fat)
    assert surplus_fat_fraction("beginner","M") < surplus_fat_fraction("intermediate","M") < surplus_fat_fraction("advanced","M")
    assert surplus_fat_fraction("intermediate","F") < surplus_fat_fraction("intermediate","M")
    for e in ("beginner","intermediate","advanced"):
        for s in ("M","F"):
            assert 0.1 <= surplus_fat_fraction(e,s) <= 0.7
