from models.governor.measurements import compute_measurement_deltas

def test_fat_loss_shrinks_waist():
    d = compute_measurement_deltas(fat_change_kg=-3.0, lean_change_kg=0.0)
    assert d["waist_cm"] < 0
    assert abs(d["waist_cm"] - (-7.5)) < 1e-6   # 3kg fat * 2.5 cm/kg

def test_muscle_gain_grows_arms_and_chest():
    d = compute_measurement_deltas(fat_change_kg=0.0, lean_change_kg=3.0)
    assert d["arms_cm"] > 0 and d["chest_cm"] > 0
    # upper lean = 3*0.6=1.8kg; arms=1.8*0.6=1.08; chest=1.8*1.8=3.24
    assert abs(d["arms_cm"] - 1.08) < 1e-6
    assert abs(d["chest_cm"] - 3.24) < 1e-6

def test_returns_all_regions():
    d = compute_measurement_deltas(-2.0, 1.0)
    assert set(d) == {"waist_cm","chest_cm","arms_cm","thighs_cm","hips_cm"}
