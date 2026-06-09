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


# --- NEW: training volume, intensity, stress, genetics modifiers --------------
# All centered so the SCHEMA DEFAULTS (sets=12, intensity=moderate, stress=5,
# genetics=average) evaluate to x1.0 -> the validated 7/7 calibration is unchanged.
_BASE = 0.33


def _prof(stress=5, genetic="average", sleep=8, age=24):
    # sleep 8 / age 24 / (protein set on nutrition) -> recovery factor == 1.0
    return UserProfile(age=age, sex="M", height_m=inch(72), weight_kg=lbs(192), bf_pct=11,
                       years_training=5, sleep_hrs_per_night=sleep,
                       stress_level=stress, genetic_potential=genetic)


def _train(sets=12, intensity="moderate"):
    return TrainingSpec(days_per_week=5, sets_per_muscle_per_week=sets, intensity=intensity)


_NUT = NutritionSpec(protein_g=160)  # 1.84 g/kg -> protein mod 1.0


def _apply(prof=None, train=None):
    return apply_gain_modifiers(_BASE, prof or _prof(), train or _train(), _NUT)


def test_schema_defaults_are_neutral_preserving_validation():
    # default training + stress=5 + average genetics + optimal recovery -> exactly base
    assert math.isclose(_apply(), _BASE, abs_tol=1e-9)


def test_volume_dose_response_and_junk_volume_plateau():
    low = _apply(train=_train(sets=4))      # < optimal -> penalized
    mid = _apply(train=_train(sets=12))     # default -> neutral
    high = _apply(train=_train(sets=20))    # productive high volume -> small bonus
    junk = _apply(train=_train(sets=30))    # junk volume -> no extra over neutral
    assert low < mid < high
    assert math.isclose(junk, mid, abs_tol=1e-9)


def test_intensity_orders_light_moderate_intense():
    light = _apply(train=_train(intensity="light"))
    moderate = _apply(train=_train(intensity="moderate"))
    intense = _apply(train=_train(intensity="intense"))
    assert light < moderate < intense
    assert math.isclose(moderate, _BASE, abs_tol=1e-9)  # moderate is the neutral baseline


def test_stress_penalizes_only_above_average():
    assert math.isclose(_apply(prof=_prof(stress=3)), _BASE, abs_tol=1e-9)  # low stress neutral
    assert math.isclose(_apply(prof=_prof(stress=5)), _BASE, abs_tol=1e-9)  # default neutral
    assert _apply(prof=_prof(stress=8)) < _BASE                              # high stress penalizes
    assert _apply(prof=_prof(stress=10)) < _apply(prof=_prof(stress=8))


def test_genetics_orders_low_average_high():
    low = _apply(prof=_prof(genetic="low"))
    avg = _apply(prof=_prof(genetic="average"))
    high = _apply(prof=_prof(genetic="high"))
    assert low < avg < high
    assert math.isclose(avg, _BASE, abs_tol=1e-9)


def test_combined_new_modifiers_are_clamped():
    worst = _apply(prof=_prof(stress=10, genetic="low"), train=_train(sets=3, intensity="light"))
    best = _apply(prof=_prof(stress=3, genetic="high"), train=_train(sets=20, intensity="intense"))
    assert math.isclose(worst, _BASE * 0.55, abs_tol=1e-6)   # product clamped at floor
    assert math.isclose(best, _BASE * 1.20, abs_tol=1e-6)    # product clamped at ceiling
