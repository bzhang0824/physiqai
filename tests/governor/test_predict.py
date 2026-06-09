from models.governor.schemas import UserProfile, GoalSpec, NutritionSpec, TrainingSpec
from models.governor.predictor import predict
def inch(x): return x*0.0254
def lbs(x): return x*0.453592

def brian():
    return UserProfile(age=24, sex="M", height_m=inch(72), weight_kg=lbs(192), bf_pct=11, years_training=5)

def test_predict_returns_complete_result():
    r = predict(brian(), GoalSpec(primary="fat_loss"), NutritionSpec(), TrainingSpec(days_per_week=5), 26)
    assert r.mode == "fat_loss"
    assert 7.5 <= r.final_state.bf_pct <= 9.5
    assert len(r.weekly_timeline) == 27
    assert 0.0 < r.confidence_score < 1.0
    assert r.measurement_deltas["waist_cm"] < 0          # cut shrinks waist
    # honest range brackets the point estimate
    lo, hi = r.confidence_range_lbs()
    assert lo < r.weight_change_lbs() < hi or hi < r.weight_change_lbs() < lo

def test_near_ffmi_ceiling_triggers_softened_warning():
    # 5'8" 175lb 9% advanced -> normalized FFMI ~24.7 (near natural cap)
    p = UserProfile(age=30, sex="M", height_m=inch(68), weight_kg=lbs(175), bf_pct=9, years_training=8)
    r = predict(p, GoalSpec(primary="muscle_gain", lean_preference="lean_bulk"),
                NutritionSpec(protein_g=180), TrainingSpec(days_per_week=5), 26)
    joined = " ".join(r.warnings).lower()
    assert "muscle" in joined and "limit" in joined        # surfaced
    assert "hit your limit" not in joined                   # softened, not blunt (Brian Q4)

def test_approaching_fat_floor_warns():
    # very lean male cutting -> should warn about sustainable floor
    p = UserProfile(age=24, sex="M", height_m=inch(72), weight_kg=lbs(170), bf_pct=8, years_training=5)
    r = predict(p, GoalSpec(primary="fat_loss"), NutritionSpec(), TrainingSpec(days_per_week=5), 26)
    assert any("floor" in w.lower() or "leaner" in w.lower() for w in r.warnings)
