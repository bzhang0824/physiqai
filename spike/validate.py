#!/usr/bin/env python3
"""Score the physiology engine against literature-derived target ranges
(docs/VALIDATION_MANIFEST.md §2) and the 473 real Reddit fat-loss outcomes.
Produces a defensibility scorecard. Run: spike/.venv/bin/python spike/validate.py
"""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from models.governor.schemas import UserProfile, GoalSpec, NutritionSpec, TrainingSpec
from models.governor.predictor import predict
KG, INCH = 0.453592, 0.0254


def prof(weight_lb, bf, years, sex="M", age=28, height_in=70, sleep=7.5):
    return UserProfile(age=age, sex=sex, height_m=height_in * INCH, weight_kg=weight_lb * KG,
                       bf_pct=bf, years_training=years, sleep_hrs_per_night=sleep)


# (label, profile, goal, lean_pref, weeks, exp_lean_kg(lo,hi), exp_fat_kg(lo,hi))
SCENARIOS = [
    ("MG trained male 12wk", prof(172, 12, 3), "muscle_gain", "standard", 12, (0.1, 2.5), (0.5, 1.5)),
    ("MG trained male 24wk", prof(172, 12, 3), "muscle_gain", "standard", 24, (0.2, 4.0), (0.8, 2.5)),
    ("MG untrained male 12wk", prof(172, 18, 0.3), "muscle_gain", "standard", 12, (0.5, 4.0), (-0.5, 1.0)),
    ("MG trained female 8wk", prof(137, 24, 2, sex="F", height_in=65), "muscle_gain", "standard", 8, (-0.5, 2.5), (-0.5, 0.3)),
    ("Recomp trained male 12wk", prof(176, 13, 3), "recomp", "standard", 12, (-0.2, 0.6), (-1.5, -0.3)),
    ("Recomp trained female 8wk", prof(143, 26, 2, sex="F", height_in=65), "recomp", "standard", 8, (0.5, 1.5), (-1.5, -0.3)),
    ("FatLoss trained male 8wk", prof(187, 15, 3), "fat_loss", "standard", 8, (-0.5, 0.5), (-4.0, -2.0)),
]


def in_range(v, lo, hi, tol=0.4):
    if lo - tol <= v <= hi + tol:
        return "PASS" if lo <= v <= hi else "NEAR"
    return "FAIL"


def hard_rules(r, weeks, protein_ok):
    """Return list of violated plausibility rules (manifest §2)."""
    bad = []
    tl = r.weekly_timeline
    lean = [(tl[i].lean_mass_kg - tl[i-1].lean_mass_kg) for i in range(1, len(tl))]
    fat = [(tl[i].fat_mass_kg - tl[i-1].fat_mass_kg) for i in range(1, len(tl))]
    if any(l > 1.0 for l in lean): bad.append("lean gain >1.0 kg/wk (reject)")
    if weeks > 4 and all(l > 0.5 for l in lean[4:]): bad.append("lean >0.5 kg/wk sustained")
    if any(f < -1.5 for f in fat): bad.append("fat loss >1.5 kg/wk (impossible)")
    if r.final_state.normalized_ffmi > 25.0: bad.append("FFMI >25 (non-natural)")
    if protein_ok and r.mode == "fat_loss":
        lean_change = r.final_state.lean_mass_kg - r.initial_state.lean_mass_kg
        if weeks <= 8 and lean_change < -1.5: bad.append("lean loss >1.5kg/8wk despite protein")
    return bad


def run_literature():
    print("=" * 88)
    print("  LITERATURE CALIBRATION  (engine vs RCT ranges, manifest §2)")
    print("=" * 88)
    print(f"  {'scenario':<28}{'ΔLean kg (exp)':<22}{'ΔFat kg (exp)':<22}{'rules'}")
    npass = nfail = 0
    for label, p, goal, pref, weeks, el, ef in SCENARIOS:
        nut = NutritionSpec(protein_g=p.weight_kg * 1.8)  # adequate protein like the RCTs
        r = predict(p, GoalSpec(primary=goal, lean_preference=pref), nut, TrainingSpec(days_per_week=4), weeks)
        dlean = r.final_state.lean_mass_kg - r.initial_state.lean_mass_kg
        dfat = r.final_state.fat_mass_kg - r.initial_state.fat_mass_kg
        ls, fs = in_range(dlean, *el), in_range(dfat, *ef)
        viol = hard_rules(r, weeks, protein_ok=True)
        ok = ls != "FAIL" and fs != "FAIL" and not viol
        npass += ok; nfail += (not ok)
        mark = "✓" if ok else "✗"
        print(f"  {mark} {label:<26}{dlean:+5.2f} [{el[0]:+.1f},{el[1]:+.1f}] {ls:<5}"
              f"{dfat:+6.2f} [{ef[0]:+.1f},{ef[1]:+.1f}] {fs:<5}{('; '.join(viol)) or 'ok'}")
    print(f"\n  literature scenarios: {npass}/{npass+nfail} defensible")
    return npass, nfail


def run_reddit():
    print("\n" + "=" * 88)
    print("  REAL-OUTCOME WEIGHT-CHANGE  (473 Reddit, comparable subset: ≤220lb, ≤40lb Δ, 2-12mo)")
    print("=" * 88)
    data = json.load(open("spike/output/real_outcomes.json"))
    sub = [d for d in data if d.get("w_before") and d.get("w_after") and d.get("months")
           and d["w_before"] <= 220 and abs(d["w_before"] - d["w_after"]) <= 40
           and 2 <= d["months"] <= 12 and d.get("sex") in ("M", "F") and d.get("height_in")]
    errs = []
    for d in sub:
        bmi = d["w_before"] / (d["height_in"] ** 2) * 703
        est_bf = 1.20 * bmi + 0.23 * (d.get("age") or 30) - (16.2 if d["sex"] == "M" else 5.4)  # Deurenberg
        est_bf = max(8, min(45, est_bf))
        p = prof(d["w_before"], est_bf, 1.0, sex=d["sex"], age=d.get("age") or 30, height_in=d["height_in"])
        r = predict(p, GoalSpec(primary="fat_loss"), NutritionSpec(tracking_method="none"),
                    TrainingSpec(days_per_week=3), int(d["months"] * 4.33))
        pred = -r.weight_change_lbs()              # predicted lbs lost
        actual = d["w_before"] - d["w_after"]
        errs.append(abs(pred - actual))
    if errs:
        mae = sum(errs) / len(errs)
        print(f"  n = {len(sub)} comparable outcomes")
        print(f"  MAE on total weight change: {mae:.1f} lb   (target: ≤ 8 lb)   {'✓ PASS' if mae <= 8 else '✗ over'}")
        within = sum(1 for e in errs if e <= 10) / len(errs)
        print(f"  within 10 lb: {within*100:.0f}%")
    return errs


if __name__ == "__main__":
    run_literature()
    run_reddit()
    print("\n" + "=" * 88)
