# PhysiqAI Validation Manifest

*Generated 2026-05-31 — drives the validation harness build*

---

## 0. Preamble: What This Manifest Is For

The PhysiqAI physiology engine makes three types of predictions:
1. **Muscle gain** — how much lean mass a user will add over N weeks
2. **Recomposition** — simultaneous lean gain + fat loss under maintenance calories
3. **Fat loss with RT** — how much fat is lost while preserving lean mass under a deficit

This manifest establishes the literature-derived ranges these predictions must fall within, the test datasets, scoring method, and pass thresholds. A prediction is "scientifically defensible" if and only if it passes every test in Section 5.

---

## 1. Consolidated RCT Ground Truth Table

### Methodology Notes
- All values reported as mean ± SD unless flagged *(SE)* or *(CI)*
- Body composition method flagged; DXA = highest confidence, BodPod = moderate, BIA/skinfold = lower
- Studies with n < 15 per group flagged LOW-N
- Duplicate entries from the raw 35-row input are merged (Longland 2016, Antonio 2015, Campbell 2018, Haun 2018 each appeared twice — merged below)

---

### 1A. MUSCLE GAIN (caloric surplus, resistance training, primary goal)

| # | Citation (PMID) | n (per arm) | Sex | Training Status | Duration (wk) | Calories | Protein (g/kg/d) | ΔLean (kg) | ΔFat (kg) | Method | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MG-1 | Garthe 2013 (PMID 23679146) | NCG=21, ALG=18 | Mixed (elite) | Trained | 10 | +500 kcal/d (NCG) vs ad lib (ALG) | High both | NCG **+1.7**, ALG **+1.2** | NCG +1.1, ALG +0.2 | DXA | MODERATE — SD not reported; kg values via Iraki 2019 review |
| MG-2 | Ribeiro 2019 (PMC6942464) | G1=6, G2=5 | Male | Trained bodybuilders | 4 | +3,500–4,000 kcal/d surplus | High both | G1 **+1.0**, G2 **+0.4** | G1 +1.2, G2 +0.1 | Skinfold + Lee eq. | LOW-MODERATE; LOW-N, no DXA, 4 wk, extreme surplus; not generalizable |
| MG-3 | Haun 2018 (PMC6141782) | GWP=11, MALTO=10 | Male | Trained (5±3 yr RT) | 6 | ~+500 kcal/d | ~2.2–2.3 | GWP **+2.93**, MALTO **+2.35** | GWP −1.00, MALTO ns | DXA | MODERATE-HIGH; extreme volume (32 sets/wk) confound; SD not recoverable |
| MG-4 | Helms 2023 (PMC10620361) | MAIN=~6, MOD=~6, HIGH=~6 | Mixed | Trained | 8 | Maintenance / +5% / +15% | Equated | Not in kg — muscle thickness (US) only; no between-group difference | Greater surplus → more skinfold increase, not more muscle | Ultrasound + skinfold | MODERATE; n=17 completers, underpowered; key insight: surplus beyond maintenance does not increase hypertrophy rate in trained |
| MG-5 | Bagheri 2024 (PMC11349518) | 12/group (4 groups) | Male | Trained (≥1 yr) | 16 | Not explicitly specified | 1.6 vs 3.2 | Upper: +1.0–1.26 kg; Lower: +0.66–1.00 kg; **combined ~+1.8–2.3 total** | Not reported by group | DXA | MODERATE-HIGH; 2×2 design, no protein dose effect on lean mass |
| MG-6 | Bell 2017 (PMID 28719669) — Phase 2 only | SUPP=25, CON=24 | Male (older, 73±1 yr) | Untrained elderly | 12 (exercise phase) | Eucaloric | Multi-ingredient supp | Phase 1 supp only: SUPP +1.2±0.3 kg vs CON −0.1±0.2 kg | Not reported with SD | DXA | MODERATE; multi-ingredient (whey+creatine+VitD+n3) — cannot isolate protein effect |

**Key muscle-gain benchmark from meta-analysis:**
- Morton 2018 meta-analysis (PMID 28698222; 49 RCTs, n=1,863): Protein supp vs control during RT → FFM difference **+0.30 kg (95% CI 0.09–0.52)** over mean 20.9 wk. **Trained subgroup: +0.75 kg (CI 0.09–1.40)** advantage for protein over control. Absolute FFM gain (both groups combined, over ~21 wk): protein arm **+2.24 kg**, control **+1.94 kg**.
- Benito 2020 meta-analysis (PMID 32079265; 111 RCTs, n=1,927 men, ~12 wk): mean FFM gain **+1.53 kg (95% CI 1.30–1.76)**; untrained **+1.54 kg** vs trained **+0.98 kg**.
- Westcott 2012 (PMID 22330016; n=1,132, 10 wk): mean lean mass gain **+1.8 kg**.

---

### 1B. RECOMPOSITION (simultaneous lean gain + fat loss, near-maintenance or slight surplus)

| # | Citation (PMID) | n (per arm) | Sex | Training Status | Duration (wk) | Calories | Protein (g/kg/d) | ΔLean (kg) | ΔFat (kg) | Method | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RC-1 | Antonio 2014 (PMC4022420) | HP=20, CON=10 | Mixed | Trained (~7–9 yr) | 8 | HP surplus (~+793 kcal); CON slight deficit | HP 4.4, CON ad lib | HP **+1.9±2.4**, CON +1.3±2.0 (ns difference) | HP **−0.2±2.2**, CON +0.3±4.7 | BodPod | MODERATE; uncontrolled training; large SD on fat |
| RC-2 | Antonio 2015 (PMC4617900) | HP=31, NP=17 | Mixed | Trained (~5 yr) | 8 | HP +495 kcal surplus | HP 3.4, NP 2.3 | HP +1.5±2.2, NP +1.5±1.8 (ns) | HP **−1.7±2.3**, NP −0.3±2.2 *(HP significantly greater, p<0.05)* | BodPod | MODERATE; HP group more experienced (confound) |
| RC-3 | Schoenfeld 2017 (PMC5214805) | PRE=9, POST=12 | Male | Trained | 10 | Maintenance | ~1.8 | PRE +0.3, POST +0.4 (ns) | PRE −1.3, POST −1.0 | DXA | MODERATE; small n; clear fat loss at maintenance in trained men |
| RC-4 | Vargas-Molina 2020 (PMC7146906) — NKD arm | NKD=11 | Female | Trained | 8 | Slight surplus (~+45 kcal/kg-FFM) | 1.7 | NKD **+0.7±1.1** | NKD +0.3±0.8 | DXA | MODERATE; recomp occurred in NKD arm with slight surplus + high protein |
| RC-5 | Campbell 2018 (PMID 29405780) — HP arm | HP=8 | Female | Trained | 8 | Slight surplus | HP 2.5 | HP **+2.1** (47.1±4.5→49.2±5.4) | HP **−1.1** (14.1±3.6→13.0±3.3) | A-mode ultrasound | MODERATE; LOW-N (n=8); true recomp in surplus with high protein |
| RC-6 | Cribb 2006 (PMID 17240782) — WI arm | WI=~7 | Male | Recreational (2 yr) | 10 | Not specified | ~2.1 total | WI **+5.0±0.3 kg** (DXA) | WI **−1.5±0.5 kg** | DXA | MODERATE-LOW; ±SD suspiciously tight — possibly SE not SD; LOW-N; verify |
| RC-7 | Rauch 2018 (PMC6316804) | OTL=7-8, PVBT=7-8 | Female | Trained collegiate | 7 | Not specified | ~1.6 | Both: **+2.7 kg** (CI 1.4–4.3) | Both: **−2.1 to −2.7 kg** (CI range) | DXA | MODERATE; LOW-N; high baseline BF (~29%) + detraining context drives large recomp signal |
| RC-8 | Haun 2018 (PMC6141782) — GWP arm | GWP=11 | Male | Trained | 6 | ~+500 kcal/d surplus | 2.2–2.3 + graded whey | **+2.93 kg** | **−1.00 kg** *(p<0.05)* | DXA | MODERATE-HIGH; recomp in caloric surplus with extreme RT volume; unusual |

**Key recomp context:**
- Barakat 2020 (DOI 10.1519/SSC.0000000000000584): identifies three conditions favoring recomp — (1) untrained or detrained beginners, (2) high BF% (more substrate for oxidation), (3) high protein intake (≥2.4 g/kg/d) with RT. Rates of simultaneous ΔLean and ΔFat are smaller in trained lean individuals.
- Cribb RC-6 and Rauch RC-7 values are outliers and should be treated as upper bounds, not expected means.

---

### 1C. FAT LOSS WITH RT (caloric deficit, lean mass preservation or modest gain)

| # | Citation (PMID) | n (per arm) | Sex | Training Status | Duration (wk) | Deficit | Protein (g/kg/d) | ΔLean (kg) | ΔFat (kg) | Method | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| FL-1 | Longland 2016 (PMC open PDF) | HP=20, LP=20 | Male | Untrained/recreationally active | 4 | ~40% | HP 2.4, LP 1.2 | HP **+1.2±1.0**, LP **+0.1±1.0** | HP **−4.8±1.6**, LP **−3.5±1.4** | 4-compartment *(gold standard)* | HIGH; extreme deficit + HIIT + RT 6d/wk limits generalizability |
| FL-2 | Mettler 2010 (PMID 19927027) | HP=10, CP=10 | Mixed (trained athletes) | Trained | 2 | 40% | HP 2.3, CP 1.0 | HP **−0.3±0.3**, CP **−1.6±0.3** *(p=0.006)* | Ns difference (both small) | DXA | MODERATE-HIGH; very short (2 wk); high protein preserves LBM under deficit |
| FL-3 | Garthe 2011 (PMID 21558571) | SR=13, FR=11 | Mixed (elite athletes) | Trained/elite | 8.5 | SR −469 kcal/d (~19%), FR −791 kcal/d (~30%) | SR 1.6, FR 1.4 | SR **+1.0±0.2** *(SE)*, FR **−0.3±0.4** *(SE)* | SR **−4.9±0.7** *(SE)*, FR **−3.2±0.5** *(SE)* | DEXA | HIGH; ±SE not SD; slow rate of loss preserves/builds LBM; fast rate loses LBM |
| FL-4 | Josse 2011 (PMC3159052) | HPHD=30, APMD=30, APLD=30 | Female (overweight, untrained) | Untrained | 16 | ~500 kcal/d + aerobic | HPHD ~1.33, APLD ~0.72 | HPHD **+0.7±0.3** *(SE)*, APLD **−0.7±0.3** *(SE)* | All significant fat loss; HPHD ~−5.3 kg | DXA | MODERATE-HIGH; aerobic + RT confounded; overweight untrained women |
| FL-5 | Thalacker-Mercer 2010 (PMC4299870) | RT=8, SED=8 | Female (postmeno, untrained) | Untrained | 13 | 500 kcal/d | Standard | RT **−0.3±0.4**, SED **−1.6±0.4** *(RT preserved LBM, p<0.05)* | RT −4.7±0.5, SED −4.1±0.9 | 3-compartment | HIGH methodology; postmenopausal, small n; RT prevents LBM loss under deficit |
| FL-6 | Hulmi 2017 (PMC open) | COMP=27 | Female (competitive physique) | Trained/advanced | ~20 | ~23% | ~3.1–3.2 | COMP **~+0.6±1.6** *(DXA FFM unchanged statistically)* | COMP **−7.5±2.6** | DXA + MFBIA | MODERATE; observational not RCT; ~20 wk contest prep; DXA shows LBM preservation |
| FL-7 | Vargas-Molina 2020 (PMC7146906) — KD arm | KD=10 | Female | Trained | 8 | Slight deficit (≈−5 kcal/kg-FFM) | 1.7 | KD **−0.7±1.7** | KD **−1.1±1.5** *(p=0.042)* | DXA | MODERATE; KD arm comparison only; moderate confidence |
| FL-8 | Miller 2018 (PMID 28871849) — RT arm only | RT=10 | Female | Untrained | 16 | Deficit | 3.1 | Significant increase (kg not extractable; qualitative only) | Significant decrease | DXA | LOW — paywalled; qualitative direction only |

---

### 1D. BASELINE / TRAINING MAINTENANCE (eucaloric, strength training, mixed populations)

| # | Citation (PMID) | n | Sex | Training Status | Duration (wk) | ΔLean (kg) | ΔFat (kg) | Method | Confidence |
|---|---|---|---|---|---|---|---|---|---|
| BL-1 | Morton 2016 (PMC4967245) | 49 (both groups) | Male | Trained (≥2 yr) | 12 | Both groups combined: **+1.2 kg** (64.6→65.8) | Not primary outcome | DXA | MODERATE; no protein-dose placebo control |
| BL-2 | Plotkin 2022 (PMC9528903) | LOAD=21, REPS=17 | Mixed | Trained | 8 | Leg lean: LOAD +0.3±0.4, REPS +0.3±0.3 | BF%: −0.5 to −0.8% | BIA (InBody 770) | MODERATE; lower-body only; BIA not DXA |
| BL-3 | Kuehne 2024 (PMC11140948) | 22 | Female | Recreational | 8 | **+0.84±1.12 kg** (combined) | BF% −0.3 to −0.8% | DXA | MODERATE; LOW-N, 8 wk, 2x/wk only |
| BL-4 | Sherwood 2025 (PMC12196337) | CON=12, PRO=15 | Female | Untrained | 12 | CON **+0.84±0.80**, PRO **+0.56±1.40** | CON −0.46±1.2, PRO −0.48±1.9 | DXA | MODERATE; RT+HIIT combined |
| BL-5 | Volek 2010 (PMC2845587) | RT=8 | Female | Untrained | 10 | **+1.6±1.8 kg** | −0.6±0.8 kg | DXA | MODERATE; LOW-N, borderline significance |
| BL-6 | Timbergen 2021 (PMC7853242) — Placebo arm | PLAC=16 | Female (postmeno) | Untrained | 12 | **+1.3 kg** (41.6→42.9) | Not reported | DXA + MRI | HIGH methodology; SD of change not reported; placebo arm = unmedicated reference |

---

## 2. Engine Calibration Targets (Literature-Derived Prediction Ranges)

These are the ranges the engine's `predict()` must fall within for predictions to be considered "scientifically defensible." Values represent expected mean outcomes ± expected interindividual SD from the above evidence base.

### 2A. MUSCLE_GAIN Mode

**Scenario: Trained male, 70–85 kg, <15% BF, caloric surplus +200–500 kcal/d, ~1.6–2.2 g/kg/d protein, RT 3–5x/wk**

| Horizon | Expected ΔLean Mean | Expected ΔLean Range (Mean ± 1 SD) | Expected ΔFat | Basis |
|---|---|---|---|---|
| 4 weeks | +0.4–0.6 kg | −0.2 to +1.0 kg | +0.2 to +0.6 kg | Haun ÷ 6wk × 4; Garthe × 4/10 |
| 8 weeks | +0.8–1.2 kg | 0 to +2.0 kg | +0.3 to +1.0 kg | Garthe ALG 1.2/10×8, Helms shows no surplus advantage |
| 12 weeks | +1.0–1.5 kg | +0.1 to +2.5 kg | +0.5 to +1.5 kg | Morton 2018 meta; Benito 2020 trained subgroup ~0.98/12wk |
| 24 weeks | +1.5–2.5 kg | +0.2 to +4.0 kg | +0.8 to +2.5 kg | Extrapolated with diminishing returns; no direct RCT at 24 wk |

**Scenario: Untrained male, entering first 12 weeks**

| Horizon | Expected ΔLean Mean | Expected ΔLean Range | Expected ΔFat | Basis |
|---|---|---|---|---|
| 12 weeks | +1.5–2.5 kg | +0.5 to +4.0 kg | −0.5 to +1.0 kg | Benito 2020 untrained +1.54 kg; Westcott +1.8 kg/10wk; Morton 2016 +1.2/12wk |

**Scenario: Trained female, surplus, RT 3–4x/wk**

| Horizon | Expected ΔLean Mean | Expected ΔLean Range | Expected ΔFat | Basis |
|---|---|---|---|---|
| 8 weeks | +0.6–1.5 kg | −0.5 to +2.5 kg | −0.5 to +0.3 kg | Campbell 2018 LP +0.6, HP +2.1; Vargas NKD +0.7 |

**Hard ceilings (flag if exceeded):**
- Male FFMI > 25 kg/m²: almost certainly outside natural range (Kouri 1995 natural bodybuilder cohort)
- Male FFMI > 23 kg/m²: above 95th percentile in NHANES adult population
- Female FFMI > 21 kg/m²: above 95th percentile in NHANES adult population
- Lean gain rate > 0.5 kg/week sustained beyond 4 weeks: flag as implausible
- Lean gain rate > 1.0 kg/week at any point: reject

---

### 2B. RECOMP Mode

**Scenario: Trained individual, maintenance calories, high protein ≥2.2 g/kg/d, RT 3–5x/wk**

| Population | Horizon | Expected ΔLean | Expected ΔFat | Basis |
|---|---|---|---|---|
| Trained male, <15% BF | 8–12 wk | −0.2 to +0.6 kg | −0.5 to −1.5 kg | Schoenfeld 2017: +0.4 lean, −1.0 fat; Antonio 2014: +1.9 lean but BodPod ±2.4 kg SD |
| Trained female, 20–30% BF | 8 wk | +0.5 to +1.5 kg | −0.5 to −1.5 kg | Campbell 2018 HP: +2.1/−1.1; Vargas NKD: +0.7/+0.3 |
| Trained female, HIGH BF (>28%) | 7–8 wk | +2.0 to +3.0 kg | −2.0 to −3.0 kg | Rauch 2018 (collegiate athletes, detraining → retraining context — treat as UPPER BOUND) |
| Untrained, any sex | 12–16 wk | +0.8 to +1.8 kg | −1.0 to −3.0 kg | Benito meta; Josse 2011 HPHD; Sherwood 2025 |

**Recomp plausibility rule:** ΔLean and ΔFat must both be in the favorable direction simultaneously, but their sum rate (|ΔLean| + |ΔFat| per week) must not exceed 0.5 kg/week for trained individuals at maintenance. Exceeding this rate flags as implausible.

**Honest limitation:** Recomp is the noisiest mode. BodPod and ultrasound studies show SD of ±2–2.5 kg on lean change over 8 weeks in trained individuals. The engine's predicted point estimate will often be within measurement noise of the ground truth — test for direction correctness and plausibility bounds, not exact match.

---

### 2C. FAT_LOSS Mode (with RT, caloric deficit)

**Scenario: ~500 kcal/d deficit, RT 3x/wk, protein ≥1.6 g/kg/d**

| Population | Horizon | Expected ΔLean | Expected ΔFat | LBM Preservation Rate | Basis |
|---|---|---|---|---|---|
| Trained male/female | 8 wk | −0.5 to +0.5 kg | −2.0 to −4.0 kg | ≥85% of weight loss as fat | Garthe 2011 SR arm; Mettler 2010 |
| Untrained female (overweight) | 16 wk | −0.5 to +0.8 kg | −3.5 to −5.5 kg | ≥80% of weight loss as fat | Josse 2011; Thalacker-Mercer 2010 |
| Competitive physique (trained female) | 20 wk | −0.5 to +0.5 kg | −6.0 to −9.0 kg | ≥90% | Hulmi 2017 |
| Extreme deficit (>30%) | 4 wk | −0.5 to +1.5 kg | −3.0 to −5.5 kg | ~75–90% | Longland 2016 (not generalizable) |

**Key constraint for fat-loss mode:**
- If predicted ΔLean < −1.5 kg over 8 weeks at any protein level ≥1.6 g/kg/d → flag as implausible (engine underestimates LBM preservation)
- If predicted fat loss > 1.5 kg/week sustained → flag (physiologically impossible beyond brief initial water weight phase)
- Lean mass loss floor: even in severe deficit, trained individuals with adequate protein lose ≤0.15 kg lean/week

**Validation against 473 Reddit fat-loss outcomes:**
- These are obese-skewed, female-skewed, scale-weight only (no body composition) — they validate total weight change, not lean/fat split
- Expected weight loss rate from these outcomes: ~0.5–1.0 kg/week in initial phase; use as sanity check on total body weight predictions only
- Do not use Reddit outcomes to validate lean/fat ratio predictions — no body composition data available

---

## 3. Prioritized Datasets to Pull

### Priority 1 — NHANES DXA 2011–2018 (BASELINE DISTRIBUTION VALIDATION)
**Why:** 12,000–15,000 DXA-measured adults; validates starting state plausibility and FFMI ceiling bounds. Does NOT validate change rates.

```bash
mkdir -p /Users/brianzhang/Projects/PhysiqAI/validation/nhanes_raw
cd /Users/brianzhang/Projects/PhysiqAI/validation/nhanes_raw

BASE=https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public

# DXA whole-body
wget -nc ${BASE}/2011/DataFiles/DXX_G.xpt
wget -nc ${BASE}/2013/DataFiles/DXX_H.xpt
wget -nc ${BASE}/2015/DataFiles/DXX_I.xpt
wget -nc ${BASE}/2017/DataFiles/DXX_J.xpt

# Body measures
wget -nc ${BASE}/2011/DataFiles/BMX_G.xpt
wget -nc ${BASE}/2013/DataFiles/BMX_H.xpt
wget -nc ${BASE}/2015/DataFiles/BMX_I.xpt
wget -nc ${BASE}/2017/DataFiles/BMX_J.xpt

# Demographics
wget -nc ${BASE}/2011/DataFiles/DEMO_G.xpt
wget -nc ${BASE}/2013/DataFiles/DEMO_H.xpt
wget -nc ${BASE}/2015/DataFiles/DEMO_I.xpt
wget -nc ${BASE}/2017/DataFiles/DEMO_J.xpt
```

**Processing:** Run the nhanes_dxa_merge.py script from the dataset recipe above. Output: `nhanes_dxa_18_55.csv` (~12,000–15,000 rows). Compute FFMI percentile tables by sex × 5-year age bin. Fit sex-stratified regression: `bf_pct ~ bmi + age + ethnicity` to replace the Deurenberg formula in the physiology engine.

**What this validates:** Starting state plausibility; FFMI ceiling; bf% imputation from BMI.

---

### Priority 2 — Morton 2018 Meta-Analysis Extracted Data Table (RATE VALIDATION)
**Why:** 49 RCTs, n=1,863, resistance training with protein, DXA/hydrodensitometry outcomes. This is the highest signal single source for expected lean mass gain rates.

**Fetch approach:** The full supplementary data table is available in the PMC free full text.
```
PMC URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC5867436/
Supplementary Table 1: All 49 included studies with mean ± SD lean mass change, duration, training status, protein dose
```
**Action:** Manually extract Supplementary Table 1 to `validation/morton_2018_studies.csv`. Columns: study_id, n, sex, training_status, duration_wk, protein_supp_g_d, delta_ffm_kg, delta_ffm_sd, body_comp_method.

This produces ~49 data points covering the full range of training durations (4–52 weeks), sexes, and training backgrounds. Use these 49 points as the primary validation set for muscle_gain mode.

---

### Priority 3 — 473 Reddit Fat-Loss Outcomes (WEIGHT CHANGE VALIDATION — ALREADY HAVE)
**Path:** `/Users/brianzhang/Projects/PhysiqAI/spike/output/real_outcomes.json`

**What this validates:** Total body weight change predictions only. Cannot validate lean/fat split.

**Preprocessing needed:** Parse to extract: initial_weight_kg, final_weight_kg, duration_weeks, sex (where available), goal (all fat loss). Compute: actual_weight_delta_kg, actual_rate_kg_per_week. Compare against engine's predicted weight delta for same input parameters.

---

### Priority 4 — Individual IPD Studies (REQUEST-BASED, FUTURE)
The Frontiers/Physiology 2025 study (DOI 10.3389/fphys.2025.1681719, PMID 41405307) provides individual participant data (IPD) for 119 subjects (62M/57F), 10–12 weeks supervised whole-body RT, DXA pre/post appendicular lean tissue. IPD available on author request: **mdr0024@auburn.edu**. This is the single highest-value data acquisition to pursue — IPD allows distributional validation (not just mean comparison) and covers both sexes in a modern cohort.

**Action:** Email author requesting data sharing agreement and CSV. Subject: "IPD request for PhysiqAI validation — Frontiers Physiology 2025 PMID 41405307."

---

### Priority 5 — HERITAGE Family Study (LONGITUDINAL EXERCISE RESPONSE, dbGaP)
**Accession:** phs000093 at dbGaP (https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id=phs000093)
**Contents:** Aerobic training (not RT), DXA body composition, both sexes, families → genetic variance data
**Limitation:** Aerobic training response, not resistance training. Lower priority than Morton 2018 IPD.
**Access:** Requires dbGaP application (2–4 week turnaround). Pursue only after Frontiers 2025 IPD.

---

## 4. Coverage Assessment and Gaps

### What We Have (Covered)

| Dimension | Status | Source |
|---|---|---|
| Fat loss + RT, trained males | COVERED | Garthe 2011, Mettler 2010, Longland 2016 |
| Fat loss + RT, untrained females | COVERED | Josse 2011, Thalacker-Mercer 2010, Sherwood 2025 |
| Fat loss, advanced female athletes | COVERED | Hulmi 2017 |
| Muscle gain, trained males, 6–10 wk | COVERED (moderate confidence) | Haun 2018, Morton 2016, Garthe 2013 |
| Muscle gain, pooled meta-estimate | COVERED (high confidence) | Morton 2018 meta, Benito 2020 meta |
| Recomp, trained females | PARTIAL | Campbell 2018, Vargas 2020, Rauch 2018 |
| Recomp, trained males | PARTIAL — small studies only | Schoenfeld 2017, Antonio 2014 |
| Baseline FFMI distribution | WILL BE COVERED after Priority 1 pull | NHANES |
| Total weight loss, obese-skewed population | COVERED | 473 Reddit outcomes |

### Critical Gaps Remaining

**GAP 1 — No trained male muscle gain RCT >12 weeks with full DXA data and SD**
Best available is Bagheri 2024 (16 wk, DXA, trained males) but fat mass change not reported. Morton 2018 meta covers 20.9 wk mean but is a pooled estimate. Need: a clean 16–24 week trained male muscle gain study with DXA ΔLean ± SD and ΔFat ± SD. *Action: Request Morton 2018 supplementary data; check if any individual included studies (e.g., Cribb, Willoughby) have longer durations with full data.*

**GAP 2 — No trained female muscle gain RCT >12 weeks**
All trained female lean gain data is 7–10 weeks (Campbell, Rauch, Vargas). The Ribeiro 2022 study (24 wk) covers older untrained women only. *Action: Pursue Frontiers 2025 IPD (Priority 4 above).*

**GAP 3 — No RCT ground truth for intermediate training age (2–5 years), both sexes**
Most "trained" studies are either novice/recreational (<2 yr) or elite athletes. The sweet spot PhysiqAI users occupy (2–5 yr training, intermediate) has thin coverage. *Action: Hubal 2005 (PMID 15947721, n=585) covers individual variance — get full text.*

**GAP 4 — No body-composition validation for recomp, maintenance calories, trained lean males**
The Schoenfeld 2017 study (PRE vs POST protein timing) is the closest, but n=21 and the intervention was protein timing not a recomp protocol. *Action: Meta-analysis Barakat 2020 (DOI 10.1519/SSC.0000000000000584) covers this qualitatively — extract quantitative ranges from Table 2.*

**GAP 5 — No age-stratified muscle gain data for 35–55 year olds**
All current RCTs are predominantly college-aged (20–30) or elderly (65+). Middle age (35–55) is a critical PhysiqAI user segment with no specific ground truth. *Expected attenuation: ~20–30% reduction in muscle gain rate vs young adults per decade after 40 (Degens 2018 review). This is an assumption, not validated — flag in engine.*

**GAP 6 — No non-Western ethnicity body composition norms**
NHANES includes ethnicity (RIDRETH3) but the RCT evidence base is predominantly White/European samples. FFMI percentiles from NHANES can be stratified by ethnicity, but gain rates may differ. Flag as uncertainty.

**GAP 7 — Reddit outcomes lack body composition split**
473 fat-loss outcomes validate weight but not lean/fat ratio. Cannot validate LBM preservation rate predictions from this dataset alone. *Partial mitigation: Hulmi 2017 (n=27 competitive females, ~20 wk) provides the best real-world fat loss + LBM preservation data.*

---

## 5. Validation Test Plan

### Architecture

The validation harness lives at `/Users/brianzhang/Projects/PhysiqAI/validation/`. It consists of:
- `harness.py` — main runner; calls `engine.predict()`, scores against literature ranges
- `benchmarks.json` — machine-readable version of the ranges in Section 2
- `test_cases.json` — the specific input scenarios below
- `nhanes_dxa_18_55.csv` — after Priority 1 pull
- `morton_2018_studies.csv` — after Priority 2 extraction
- `reddit_outcomes_parsed.json` — parsed from existing 473-row file

---

### Test Suite Definition

#### Suite A: Muscle Gain Mode — 12 Scenarios

Each scenario: call `engine.predict(goal="muscle_gain", sex, age, height_cm, weight_kg, bf_pct, training_years, protein_g_kg, kcal_surplus, rt_sessions_wk, duration_weeks)` → compare predicted `delta_lean_kg` and `delta_fat_kg` against the range from Section 2A.

| Scenario ID | Description | Duration | Pass Criterion |
|---|---|---|---|
| MG-A01 | Untrained male, 25y, 180cm, 80kg, 18% BF, protein 1.8, surplus +300 kcal, 3x/wk | 12 wk | delta_lean ∈ [0.5, 4.0] kg; delta_fat ∈ [−1.0, +1.5] kg |
| MG-A02 | Trained male (3 yr), 28y, 178cm, 78kg, 14% BF, protein 2.0, surplus +300 kcal, 4x/wk | 12 wk | delta_lean ∈ [0.1, 2.5] kg; delta_fat ∈ [−0.5, +1.5] kg |
| MG-A03 | Trained male (5 yr), 30y, 175cm, 82kg, 12% BF, protein 2.2, surplus +400 kcal, 5x/wk | 24 wk | delta_lean ∈ [0.2, 4.0] kg; delta_fat ∈ [0.0, +2.5] kg |
| MG-A04 | Untrained female, 24y, 165cm, 62kg, 26% BF, protein 1.6, surplus +200 kcal, 3x/wk | 12 wk | delta_lean ∈ [0.3, 3.5] kg; delta_fat ∈ [−1.0, +1.5] kg |
| MG-A05 | Trained female (2 yr), 27y, 163cm, 60kg, 22% BF, protein 2.2, surplus +200 kcal, 4x/wk | 8 wk | delta_lean ∈ [−0.5, 2.5] kg; delta_fat ∈ [−1.5, +0.5] kg |
| MG-A06 | Implausibility check: trained male claiming +10 kg lean in 12 wk | 12 wk | **MUST REJECT or CLAMP** to <4.0 kg |
| MG-A07 | FFMI ceiling check: male, 180cm, 80kg, 5 yr training; predict to year 10 endpoint | 5 yr extrapolated | Predicted FFMI endpoint ≤ 25 kg/m² |
| MG-A08 | Older male (42y), trained 8 yr, 175cm, 85kg, 18% BF, protein 2.0 | 12 wk | delta_lean ∈ [0.0, 2.0] kg (age-attenuated) |
| MG-A09 | Meta-analysis benchmark: mean "trained male" (Morton 2018 subgroup) | ~21 wk | delta_lean ∈ [0.5, 1.8] kg (matches +0.75 kg protein advantage + ~1.0 control = net ~1.0–1.8) |
| MG-A10 | Novice responder (high expected gains): untrained male, 20y, 182cm, 75kg | 12 wk | delta_lean ∈ [1.0, 4.5] kg (Westcott +1.8; allows high-responder distribution tail) |
| MG-A11 | Trained female (5 yr), surplus, 16 wk | 16 wk | delta_lean ∈ [0.2, 3.0] kg; FFMI at end ≤ 22 kg/m² |
| MG-A12 | Protein adequacy test: same person, protein 0.8 g/kg vs 2.2 g/kg | 12 wk | delta_lean at 2.2 g/kg must be ≥ delta_lean at 0.8 g/kg + 0.3 kg (Morton 2018: +0.30 kg protein effect) |

---

#### Suite B: Recomp Mode — 8 Scenarios

| Scenario ID | Description | Duration | Pass Criterion |
|---|---|---|---|
| RC-B01 | Trained male, maintenance, 22% BF, protein 2.4, 4x/wk | 12 wk | delta_lean ∈ [−0.5, +1.0] kg AND delta_fat ∈ [−2.0, 0] kg (both conditions required) |
| RC-B02 | Trained female, 28% BF (elevated), protein 2.4, 4x/wk | 8 wk | delta_lean ∈ [+0.3, +2.5] kg AND delta_fat ∈ [−2.5, −0.3] kg |
| RC-B03 | Trained lean male (<12% BF), maintenance, protein 2.0 | 12 wk | delta_lean ∈ [−0.5, +0.5] kg AND delta_fat ∈ [−1.0, 0] kg (recomp rate attenuated at low BF) |
| RC-B04 | Untrained female, 30% BF, maintenance, protein 1.8 | 12 wk | delta_lean ∈ [+0.5, +2.0] kg AND delta_fat ∈ [−2.0, −0.5] kg |
| RC-B05 | Rate sanity: (|delta_lean| + |delta_fat|) / duration_weeks | Any | Must be ≤ 0.5 kg/week for trained at maintenance |
| RC-B06 | Detraining context (returned after 3 mo break): 30% BF female, protein 2.0, 8 wk | 8 wk | delta_lean ∈ [+1.0, +3.5] kg AND delta_fat ∈ [−2.5, −0.5] kg (muscle memory effect) |
| RC-B07 | Direction check: recomp prediction must show opposite signs for delta_lean and delta_fat | Any | Sign(delta_lean) > 0 AND Sign(delta_fat) < 0 (or both near zero ±0.2 kg) |
| RC-B08 | Implausibility check: recomp prediction showing +5 kg lean + −5 kg fat in 12 wk | 12 wk | **MUST REJECT** — exceeds any RCT outcome by >3× |

---

#### Suite C: Fat Loss Mode — 10 Scenarios

| Scenario ID | Description | Duration | Pass Criterion |
|---|---|---|---|
| FL-C01 | Trained female, 500 kcal deficit, protein 2.0, RT 3x/wk | 12 wk | delta_lean ∈ [−0.8, +0.5] kg; delta_fat ∈ [−4.0, −1.5] kg |
| FL-C02 | Untrained female (overweight, 35% BF), 500 kcal deficit, protein 1.6 | 16 wk | delta_lean ∈ [−1.0, +1.0] kg; delta_fat ∈ [−5.5, −2.0] kg |
| FL-C03 | Competitive physique female, 23% deficit, protein 3.1, 5x/wk | 20 wk | delta_lean ∈ [−1.5, +1.5] kg; delta_fat ∈ [−9.0, −4.0] kg |
| FL-C04 | Elite male athlete, slow deficit (−469 kcal/d ~19%), protein 1.6 | 8.5 wk | delta_lean ∈ [+0.2, +1.8] kg *(SE)* delta_fat ∈ [−6.5, −3.5] kg |
| FL-C05 | Fast deficit (−791 kcal/d ~30%), same athlete | 5–8 wk | delta_lean ∈ [−1.5, +0.5] kg; delta_fat ∈ [−5.0, −1.5] kg; LBM preservation lower than slow deficit |
| FL-C06 | LBM preservation ordering: slow deficit vs fast deficit | Paired | delta_lean (slow) MUST be > delta_lean (fast) given same duration |
| FL-C07 | Protein effect on LBM: 1.0 g/kg vs 2.3 g/kg, same deficit | 2–8 wk | delta_lean at 2.3 g/kg ≥ delta_lean at 1.0 g/kg + 0.5 kg |
| FL-C08 | Reddit validation: sample 50 cases from 473-row dataset | Varies | Mean |predicted_weight_delta − actual_weight_delta| < 2.0 kg per case |
| FL-C09 | Reddit validation: RMSE across all 473 cases | Varies | RMSE of predicted vs actual weight change < 3.5 kg |
| FL-C10 | Zero-lean-loss floor: trained individual, mild deficit (−250 kcal/d), protein 2.0 | 8 wk | delta_lean > −1.5 kg (RT + adequate protein prevents significant lean loss at mild deficit) |

---

#### Suite D: Baseline Plausibility (NHANES-Derived) — 6 Checks

Run after NHANES data pull. These check starting state outputs, not change predictions.

| Check ID | Description | Pass Criterion |
|---|---|---|
| BP-D01 | Predicted starting lean_kg for "25yo male, 175cm, 75kg, 18% BF" | Within NHANES 25th–75th percentile for M 20–30yr (expected ~55–65 kg lean) |
| BP-D02 | Predicted starting FFMI for same subject | Within NHANES 25th–75th percentile for M 20–30yr (expected ~18–22 kg/m²) |
| BP-D03 | Predicted starting bf_pct from BMI for "28yo female, 165cm, 65kg, BMI 23.9" | Within NHANES regression 95% CI for F 25–30yr, BMI 23–25 (expected ~25–33%) |
| BP-D04 | FFMI ceiling enforcement: any prediction ending >25 kg/m² for male | Engine MUST flag with warning; value should be clamped or explicitly marked implausible |
| BP-D05 | FFMI ceiling for female: any prediction ending >21 kg/m² | Engine MUST flag |
| BP-D06 | Distribution sanity: 1000 random inputs → 95% of predicted starting states within NHANES 2.5–97.5th percentile | Automated population sweep pass rate ≥ 95% |

---

### Scoring Method

**Per test case score:**
```
PASS  = prediction within defined range for all outcomes
WARN  = prediction within 1.5× the range boundary (borderline)
FAIL  = prediction outside 1.5× range boundary
FATAL = prediction violates a hard constraint (implausibility check, FFMI ceiling)
```

**Overall engine score (per mode):**
```
Muscle Gain Score  = (PASS + 0.5×WARN) / total_MG_tests
Recomp Score       = (PASS + 0.5×WARN) / total_RC_tests
Fat Loss Score     = (PASS + 0.5×WARN) / total_FL_tests
Baseline Score     = (PASS + 0.5×WARN) / total_BP_tests
```

**Pass thresholds:**

| Mode | Minimum to Ship | Target |
|---|---|---|
| Muscle Gain | 0.70 | 0.85 |
| Recomp | 0.65 | 0.80 |
| Fat Loss | 0.75 (includes Reddit RMSE) | 0.85 |
| Baseline Plausibility | 0.90 (NHANES floor) | 0.95 |
| FATAL violations | 0 (zero tolerance) | 0 |

**FATAL failures (any FATAL = block release):**
- Any prediction with FFMI > 26 kg/m² male or > 22 kg/m² female
- Any prediction with lean gain rate > 1.0 kg/week sustained >2 weeks
- Any prediction showing fat loss > 1.5 kg/week sustained >4 weeks
- Reddit RMSE > 5.0 kg (engine is wildly wrong on weight)
- Recomp prediction showing simultaneous ΔLean < −2 kg AND ΔFat > +2 kg (impossible physiology)

---

### Implementation Sequence

1. **Week 1:** Pull NHANES data (Priority 1 fetch commands above). Run `nhanes_dxa_merge.py`. Generate FFMI percentile tables. Implement Suite D baseline checks. These can run immediately.

2. **Week 1:** Parse `spike/output/real_outcomes.json` into `reddit_outcomes_parsed.json`. Implement FL-C08 and FL-C09 (Reddit weight RMSE). These require no new data.

3. **Week 2:** Manually extract Morton 2018 Supplementary Table 1 to `morton_2018_studies.csv`. Implement Suite A meta-analysis benchmark (MG-A09). Implement the 49-study distributional comparison.

4. **Week 2:** Implement the full test harness `harness.py` with all Suite A–D test cases, scoring logic, and HTML/JSON report output. Use the benchmarks.json lookup for range comparisons.

5. **Week 3:** Email Frontiers 2025 author for IPD. While waiting, run full harness against current engine. Identify which tests fail and what those failures indicate about engine calibration errors.

6. **Ongoing:** Every engine parameter change requires full harness re-run before merge. Harness is a pre-commit gate, not a post-deployment check.

---

## 6. Honest Assessment of What This Manifest Does Not Solve

**The fundamental limitation:** Every RCT in this manifest recruited motivated volunteers who enrolled in controlled studies, received supervised training, and had their diet controlled or heavily guided. PhysiqAI users are self-reporting their intended protocol (not their actual adherence). Adherence variance in free-living conditions is 2–3× larger than RCT variance. The engine's predictions will therefore be correct for a motivated, adherent user and systematically optimistic for an average user.

**Recommended mitigation:** Add an adherence confidence interval to every prediction output ("under full adherence: X kg; under typical real-world adherence (70%): Y kg"). The 473 Reddit outcomes are a useful calibration for the "typical adherence" case — those are real people reporting real outcomes, not RCT subjects.

**What we cannot validate without new data collection:**
- Individual physiology (genetics-driven responder vs non-responder variance — Hubal 2005 shows 0 to >10 cm² CSA change variance in the same protocol)
- Prediction accuracy beyond 24 weeks (no RCT runs long enough for the training durations PhysiqAI users care about — 1 to 5 years)
- The specific visual/photo transformation output (image quality cannot be validated against these benchmarks — requires separate human-evaluation study)