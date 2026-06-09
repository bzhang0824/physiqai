import math
from models.governor.schemas import UserProfile, NutritionSpec, TrainingSpec
from models.governor.confidence import compute_confidence
def inch(x): return x*0.0254
def lbs(x): return x*0.453592

def _p(yrs=2, bf_est=True):
    return UserProfile(age=24, sex="M", height_m=inch(72), weight_kg=lbs(192), bf_pct=11,
                       years_training=yrs, bf_estimated=bf_est)

def test_confidence_known_intermediate_case():
    # app-tracking, estimated bf, protein known, 12wk, intermediate -> raw ~0.897, ci ~0.201
    score, ci = compute_confidence(_p(yrs=2), NutritionSpec(protein_g=160, tracking_method="app"),
                                   TrainingSpec(), horizon_weeks=12)
    assert math.isclose(score, 0.897, abs_tol=0.01)
    assert math.isclose(ci, 0.201, abs_tol=0.01)

def test_better_inputs_raise_score_and_narrow_range():
    good_s, good_ci = compute_confidence(_p(bf_est=False), NutritionSpec(protein_g=160, tracking_method="weighing"),
                                         TrainingSpec(), horizon_weeks=12)
    poor_s, poor_ci = compute_confidence(_p(bf_est=True), NutritionSpec(tracking_method="none"),
                                         TrainingSpec(), horizon_weeks=52)
    assert good_s > poor_s
    assert good_ci < poor_ci

def test_bounds_score_0_1_and_ci_min_15pct():
    for trk in ("weighing","app","eyeballing","none"):
        for wk in (4, 26, 52):
            s, ci = compute_confidence(_p(), NutritionSpec(tracking_method=trk), TrainingSpec(), wk)
            assert 0.0 <= s <= 1.0
            assert ci >= 0.15 - 1e-9
