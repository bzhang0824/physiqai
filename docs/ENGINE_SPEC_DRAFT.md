Now I have a complete picture. Let me synthesize the full engine design.

---

# PhysiqAI GOVERNOR — Unified Physiology Engine Design

**Version:** 1.0 — May 2026
**Author:** Lead Physiology Architect (Claude Sonnet 4.6)
**Status:** Design spec, ready for TDD implementation

---

## Executive Summary (Non-Technical)

The current engine is like a speedometer that only measures flat ground — it works for simple weight loss but breaks badly for the people PhysiqAI actually serves: intermediate gym-goers doing muscle gain, lean bulks, and recomps. It predicted a real user would hit 5.1% body fat in 6 months — physiologically impossible. It adds fat to users who want to "stay lean while building." Its confidence score is made up.

This redesign fixes all three bugs, grounds every number in peer-reviewed literature, and builds a modular engine that is honest about uncertainty.

---

## 1. Unified Model Flow

The pipeline runs in this exact order. Each stage produces outputs consumed by the next.

### Stage 0: Input Normalization

```
UserProfile(age, sex, height, weight_lbs, body_fat_pct, years_training,
            sleep_hrs, stress_1_10, genetic_potential)
GoalSpec(primary_goal, secondary_preference, lean_bulk_flag)
NutritionSpec(daily_calories_input, protein_g, tracking_method)
TrainingSpec(days_per_week, intensity, sets_per_muscle_per_week)
horizon_weeks: int
```

**Actions:**
- Convert weight to kg for all internal math; display in lbs
- Derive `ExperienceLevel` from `years_training` (< 1 yr = beginner, 1-3 = intermediate, 3+ = advanced)
- Impute missing body fat from BMI + sex via Jackson-Pollock lookup table (flag as estimated)
- Validate: bf ≥ essential floor (male 3%, female 10%); if below, clamp and warn

### Stage 1: Energy Balance

**Compute TDEE:**

```
BMR = Mifflin-St-Jeor(weight_kg, height_cm, age, sex)  [keep — it's fine]
activity_factor = from_training_spec(days_per_week, intensity)
  # 1.375 (light, ≤2d), 1.46 (mod, 3-4d), 1.55 (active, 5-6d), 1.72 (very active + cardio)
TDEE = BMR * activity_factor
```

**Compute daily calorie balance:**

```
if user_provided_calories:
    daily_balance = user_calories - TDEE
else:
    daily_balance = infer_from_goal(goal, experience_level, body_fat_pct)
    # MUSCLE_GAIN: +200 to +400 kcal depending on experience (Iraki 2019, PMC6680710)
    # FAT_LOSS: -300 to -500 kcal, body-fat-stratified (NUTRITION_RESEARCH.md §6.3)
    # RECOMP / LEAN_BULK: -100 to +100 kcal (near-maintenance)
    # MAINTENANCE: 0
```

**Protein adequacy flag:**

```
protein_per_kg = protein_g / weight_kg
is_adequate = protein_per_kg >= 1.6  # Morton 2018, PMID 28698222
protein_mod = protein_adequacy_modifier(protein_per_kg)  # from PHYSIOLOGY_SOURCES §6.1
```

### Stage 2: FFMI Ceiling Calculation (run once, used as hard cap)

```
lean_mass_kg = weight_kg * (1 - bf_pct/100)
ffmi = lean_mass_kg / height_m^2
normalized_ffmi = ffmi + 6.1 * (1.8 - height_m)  # Kouri 1995, PMID 7496846

# Natural ceiling: normalized FFMI 25 (hard stop), warning at 24
ffmi_headroom_kg = max(0, (25.0 - normalized_ffmi) * height_m^2)
# This is the absolute maximum additional lean mass before hitting natural limit
```

### Stage 3: Base Gain / Loss Rate Computation

**Lean mass gain rate (surplus or recomp):**

```
# Aragon/Helms model (PHYSIOLOGY_SOURCES §1.2) — bodyweight-anchored, not flat table
base_monthly_gain_kg = weight_kg * aragon_helms_pct_per_month(experience_level, sex)
  # Beginner male:       0.0100-0.0150 → use 0.0125
  # Intermediate male:   0.0050-0.0100 → use 0.0075
  # Advanced male:       0.0025-0.0050 → use 0.0038
  # Female: multiply by 0.50 for absolute mass (Roberts et al 2020, PMID 32218059)
  # (relative % gains are equal; absolute lower because women start with less LBM)

# McDonald annual check: convert to annual, verify against McDonald table (§1.1)
# If annual projection > McDonald ceiling, cap to McDonald and note it

# Apply modifiers (all multiplicative):
age_mod      = age_muscle_gain_modifier(age)        # from §3.2
protein_mod  = protein_adequacy_modifier(protein/kg) # from §6.1
sleep_mod    = sleep_modifier(sleep_hrs)             # Lamon 2021, PMC7785053
freq_mod     = frequency_modifier(muscle_freq_per_wk)# Schoenfeld 2016, PMID 27102172
volume_mod   = volume_modifier(sets_per_muscle_wk)  # Schoenfeld 2017, PMID 27433992
p_ratio_mod  = p_ratio_modifier(bf_pct, sex)        # Forbes/Hall, limited evidence

adjusted_monthly_gain_kg = base_monthly_gain_kg * product(all_mods)
```

**Fat loss rate (deficit):**

```
# Theoretical: 7700 kcal deficit = 1 kg fat (not 3500 kcal/lb — that's the ONLY place
# to keep imperial, and even then 3500 kcal/lb is a rough approximation; use 7700/kg internally)
weekly_theoretical_fat_kg = (abs(daily_balance) * 7) / 7700

# Safe rate check: 0.5-0.7% BW/week preserves muscle best (Garthe 2011, PMID 21558571)
safe_weekly_kg = weight_kg * 0.007  # 0.7% BW/wk upper
aggressive_weekly_kg = weight_kg * 0.010  # 1.0% BW/wk

if weekly_theoretical_fat_kg > aggressive_weekly_kg:
    muscle_loss_fraction = 0.30   # 30% of total loss is lean (rapid loss)
elif weekly_theoretical_fat_kg > safe_weekly_kg:
    muscle_loss_fraction = 0.15   # 15% lean loss (moderate)
else:
    muscle_loss_fraction = 0.05   # 5% lean loss (slow, optimal)
```

**Recomp mode (near-maintenance, 100-200 kcal deficit):**

```
# Possible when: BF > threshold, OR beginner, OR detrained return
# Lean gain rate = 40-60% of surplus rate (NUTRITION_RESEARCH §3)
# Fat loss rate = (small deficit contribution) + (BF mobilization for fuel)
recomp_lean_gain = adjusted_monthly_gain_kg * recomp_factor(experience_level, bf_pct)
  # recomp_factor: 0.60 beginner/high-BF, 0.40 intermediate, 0.25 advanced/lean
recomp_fat_loss = small_deficit_fat_loss + bf_mobilization_estimate
```

### Stage 4: Time-Course with Diminishing Returns + Hard Floors

This is the core fix for Bug #1.

**Fat floor enforcement:**

```
# Essential fat minimums (physiological, not aesthetic):
ESSENTIAL_FAT_FLOOR = {'M': 5.0, 'F': 13.0}  # percent

# Practical floor (sustainable for most people, not extreme):
PRACTICAL_FAT_FLOOR = {'M': 7.0, 'F': 16.0}

# The floor is applied EVERY week in the time-course loop
```

**Weekly simulation loop:**

```python
def simulate_weekly(profile, rates, horizon_weeks):
    state = State(
        weight_kg=profile.weight_kg,
        fat_mass_kg=profile.weight_kg * profile.bf_pct / 100,
        lean_mass_kg=profile.lean_mass_kg,
        week=0
    )
    timeline = [state.snapshot()]

    for week in range(1, horizon_weeks + 1):
        # --- Fat loss component ---
        current_bf_pct = state.fat_mass_kg / state.weight_kg * 100

        # HARD FLOOR: Stop fat loss when we hit the essential floor
        fat_floor_kg = state.weight_kg * ESSENTIAL_FAT_FLOOR[sex] / 100
        fat_available_to_lose = max(0, state.fat_mass_kg - fat_floor_kg)

        # DECELERATION: fat loss slows as we get leaner (metabolic adaptation)
        # Rate = base_rate * deceleration_factor
        lean_penalty = compute_lean_penalty(current_bf_pct, sex)
        # lean_penalty = 1.0 at start, decays toward 0.4 as bf approaches floor
        # Uses logistic function anchored at PRACTICAL_FAT_FLOOR

        weekly_fat_loss = min(
            fat_available_to_lose,
            rates.weekly_fat_loss_kg * lean_penalty
        )
        # Also apply metabolic adaptation (15% decrease cap, from current predictor — keep this)
        metabolic_adapt_factor = max(0.85, 1.0 - (week * 0.002))  # ~2% per 10 weeks
        weekly_fat_loss *= metabolic_adapt_factor

        # Fat loss also means some lean loss (based on deficit rate)
        lean_loss_from_deficit = weekly_fat_loss * (
            muscle_loss_fraction / (1 - muscle_loss_fraction)
        )

        # --- Lean gain component ---
        # FFMI ceiling: slow down gains as we approach natural limit
        current_ffmi = compute_normalized_ffmi(state.lean_mass_kg, height_m)
        ffmi_ceiling_factor = ffmi_deceleration(current_ffmi)
        # = 1.0 if FFMI < 22, linearly decays to 0.0 at FFMI = 25

        # Monthly to weekly, with diminishing returns over time
        # Using McDonald-style annual potential as a further cap
        monthly_gain_kg = rates.adjusted_monthly_gain_kg * ffmi_ceiling_factor
        weekly_lean_gain = monthly_gain_kg / 4.33

        # In deficit: lean gain is reduced; only recomp users get both
        if mode == DEFICIT and not is_recomp:
            weekly_lean_gain = 0  # Can't build muscle on aggressive deficit
        elif mode == DEFICIT and is_recomp:
            weekly_lean_gain = weekly_lean_gain * rates.recomp_factor

        # Apply to state
        state.fat_mass_kg -= weekly_fat_loss
        state.lean_mass_kg += weekly_lean_gain - lean_loss_from_deficit
        state.lean_mass_kg = max(state.lean_mass_kg, profile.lean_mass_kg * 0.90)  # sanity floor
        state.weight_kg = state.fat_mass_kg + state.lean_mass_kg

        timeline.append(state.snapshot())

    return timeline
```

**Key: deceleration function for fat floor:**

```python
def compute_lean_penalty(current_bf_pct, sex):
    """
    As body fat approaches the practical floor, rate of further fat loss
    decelerates non-linearly — modeling hormonal adaptation, hunger, metabolic
    slowdown (analogous to Hall 2012 dynamic model of energy expenditure adaptation).
    """
    floor = PRACTICAL_FAT_FLOOR[sex]
    ceiling = floor + 8.0  # full-rate range starts 8 pp above floor
    if current_bf_pct >= ceiling:
        return 1.0
    elif current_bf_pct <= floor:
        return 0.0
    else:
        # Smooth logistic decay
        t = (current_bf_pct - floor) / (ceiling - floor)
        return t ** 1.5  # concave decay — slows fast near floor
```

### Stage 5: Regional Measurements

```
# Applied to final-state delta, not to per-week data (measurement noise is high)
waist_delta_cm   = fat_mass_delta_kg * 2.5   # ~2.5 cm per kg fat at waist
chest_delta_cm   = (lean_gain_upper_kg * 1.8) + (fat_delta_kg * 0.8)
arms_delta_cm    = lean_gain_upper_kg * 0.6   # calibrated to 0.25" per lb arm mass
thighs_delta_cm  = lean_gain_lower_kg * 0.8
hips_delta_cm    = fat_mass_delta_kg * 1.5 + lean_gain_lower_kg * 0.4
```

Muscle group allocation uses the training focus split from `TrainingSpec.focus_muscle_groups`. Without it, default to 40% lower / 60% upper split.

### Stage 6: Confidence Interval

See Section 3 (Fix #3) and Section below.

### Stage 7: Output

```python
@dataclass
class GovernorResult:
    # Point estimates (end of horizon)
    final_weight_kg: float
    final_bf_pct: float
    final_lean_mass_kg: float
    final_ffmi_normalized: float

    # Changes
    weight_change_kg: float
    fat_mass_change_kg: float
    lean_mass_change_kg: float
    bf_pct_change: float

    # Weekly time series
    weekly_states: List[WeeklyState]  # weight_kg, fat_kg, lean_kg, bf_pct

    # Confidence interval (principled — see §3)
    confidence_low: float    # lower bound on total change
    confidence_mid: float    # point estimate
    confidence_high: float   # upper bound
    confidence_score: float  # 0-1, displayed to user as certainty

    # Measurements (deltas, cm)
    measurement_deltas: Dict[str, float]

    # Flags / warnings
    warnings: List[str]      # e.g. "approaching natural fat floor", "near FFMI ceiling"
    insights: List[str]
    mode: str                # "fat_loss", "muscle_gain", "recomp", "lean_bulk", "maintenance"
```

---

## 2. Conflicts and Resolutions

### Conflict A: Female gender modifier — 0.5 vs 0.7

**Current engine uses 0.7.** PHYSIOLOGY_SOURCES §2.1 (Roberts et al. 2020, PMID 32218059) says **relative % gains are equal, absolute gains differ because women start with ~60-70% of male LBM.** The Aragon/Helms model in PHYSIOLOGY_SOURCES §2.2 explicitly gives females 50% of male absolute rate.

**Resolution: Use 0.50 absolute modifier when using absolute kg rates (Aragon/Helms). The 0.7 in the current engine is incorrect and should be retired.** Since we anchor to bodyweight percentage (Aragon/Helms), the 0.5 multiplier is already baked in via the female-specific percentage tables. Do not stack a separate 0.7 modifier on top.

### Conflict B: Calories per lb fat — 3500 vs reality

**Current engine:** `CALORIES_PER_LB_FAT = 3500`. This is a rough folk rule. More accurate: **7700 kcal/kg fat** (Forbes model; also implies ~3,500 kcal/lb, which is close but ignores that real weight loss includes ~25% water/glycogen, especially early).

**Resolution:** Keep 3500 kcal/lb for the UI/explanation layer (users understand it). Use 7700 kcal/kg internally, and acknowledge a 15-25% "real-world correction factor" from water weight, glycogen, and metabolic adaptation in the weekly time series. This explains why actual weight loss in week 1-2 is faster than thermodynamic prediction and slows later.

### Conflict C: Muscle gain rates — flat table vs bodyweight-anchored

**Current engine:** flat lbs/month table (2.0, 1.0, 0.5 for B/I/A males). **PHYSIOLOGY_SOURCES §1.2:** Aragon/Helms use % of bodyweight (1.0-1.5% / 0.5-1.0% / 0.25-0.5%).

For a 150 lb beginner male: 1.25% = 1.875 lbs/month. Current engine says 2.0. Close enough for beginner.
For a 200 lb beginner male: 1.25% = 2.5 lbs/month. Current engine says 2.0. Underestimates a heavy person.
For a 130 lb intermediate female: 0.625% * 0.5 (absolute) = 0.39 lbs/month. Current engine says 0.5. Overestimates.

**Resolution:** Use the Aragon/Helms bodyweight-anchored model (PHYSIOLOGY_SOURCES §1.2) — it's more principled. Apply to kg at start of each month, with the FFMI ceiling as the absolute cap.

### Conflict D: P-ratio modifier — how strong is the body-fat effect?

**Current engine:** implicit (no real p-ratio model). **PHYSIOLOGY_SOURCES §7.1** includes it but adds a caveat that "evidence is LIMITED for trained individuals." **NUTRITION_RESEARCH §6.1** from Stronger By Science explicitly says "the relationship is much weaker than traditionally believed" for lifters.

**Resolution:** Include a weak p-ratio modifier (±5-10% on partitioning efficiency), but do not make it a primary driver. The modifier range is ≤ 0.90-1.05, not ±30%. Flag it in confidence, not in the core rate calculation.

### Conflict E: Recomp muscle gain rate — 60% vs 40% vs conditions-based

**Current engine:** 60% of normal rate for recomp. **NUTRITION_RESEARCH §7.1** suggests 40% for trained, 60% for beginner/high-BF. **Murphy & Koehler 2021 (PMID 34623696):** deficits >500 kcal significantly impair gain.

**Resolution:** Use a condition-stratified recomp factor:
- Beginner + BF > 20% (M) or 28% (F): 0.60 of base rate
- Intermediate + BF in moderate range: 0.40
- Advanced / lean: 0.20 (barely possible)
- Deficit > 500 kcal: override to 0 lean gain regardless

---

## 3. The Three Bug Fixes

### Bug Fix #1: Body Fat Floor / Diminishing Returns

**Root cause in current engine (line 288-293):** `min_healthy_bf = 5 if starting_bf < 15 else 10` — gendered thresholds are wrong, and there is NO deceleration as BF approaches the floor. The engine will keep subtracting fat mass linearly down to 5%, which is sub-essential-fat for any human.

**Fix in new engine:**
1. Hard floor: `ESSENTIAL_FAT_FLOOR = {'M': 5.0, 'F': 13.0}`. Weekly fat loss is capped to `fat_mass - floor_mass`. Once this difference is zero, fat loss stops completely.
2. Practical deceleration: `compute_lean_penalty()` (see Stage 4) applies a logistic deceleration starting 8 percentage points above the floor, reaching near-zero at the floor. This models hormonal adaptation, metabolic slowdown, and the well-documented difficulty of getting to very low body fat.
3. Every week's computation is independent — the deceleration is re-evaluated against the current state, not extrapolated from the start.

**Verification on the known broken case:** 24M, 192 lbs (~87 kg), 11% BF, 6-month prediction:
- Fat mass at start: ~9.6 kg. Essential floor (5%): ~4.4 kg floor
- Available fat: 9.6 - (87 * 0.05) = 9.6 - 4.35 = 5.25 kg max fat loss
- Even with 500 kcal/day deficit and near-perfect conditions, 500*180/7700 = 11.7 kg theoretically
- After floor cap: real loss ≤ 5.25 kg → minimum final BF = 5% by hard stop
- With deceleration penalty kicking in at (5+8)=13% → it starts slowing at 13%, which is 2 pp above current. **At 11% starting BF the penalty is already 0.38** of normal rate. The prediction would slow dramatically and realistically land around 8-9%, not 5.1%.

### Bug Fix #2: Goal-to-Mode Mapping

**Root cause:** `WorkoutType.MUSCLE_GAIN` automatically assumes a caloric surplus (`tdee + 300`), then calculates fat gain from surplus calories. A user who says "muscle gain" but wants to "stay lean / lean bulk" gets a fat-gain prediction they didn't sign up for.

**Fix:**

Replace the 4-enum `WorkoutType` with a 2-axis goal spec:

```python
@dataclass
class GoalSpec:
    primary: Literal["fat_loss", "muscle_gain", "recomp", "maintenance"]
    lean_preference: Literal["standard", "lean_bulk", "aggressive_bulk"]  # default "standard"
    acceptable_fat_gain_lbs_per_month: float = 1.0  # user sets this ceiling
```

Calorie assignment logic:

```python
def assign_calories(goal, experience, weight_kg, lean_preference):
    SURPLUS_BY_EXPERIENCE = {
        "beginner":     {"standard": 400, "lean_bulk": 200, "aggressive_bulk": 600},
        "intermediate": {"standard": 300, "lean_bulk": 150, "aggressive_bulk": 500},
        "advanced":     {"standard": 200, "lean_bulk": 100, "aggressive_bulk": 350},
    }
    if goal.primary == "muscle_gain":
        return TDEE + SURPLUS_BY_EXPERIENCE[experience][goal.lean_preference]
    elif goal.primary == "fat_loss":
        return TDEE - deficit_by_bf(weight_kg, bf_pct)
    elif goal.primary == "recomp":
        return TDEE - 100  # small deficit for recomp
    else:
        return TDEE
```

A user saying "lean bulk" routes to `lean_preference="lean_bulk"`, gets +150-200 kcal, which yields maybe 0.3-0.5 lbs of fat/month rather than the 1.5-2 lbs the current engine produces. This is the scientifically correct "lean bulk" outcome.

### Bug Fix #3: Principled Confidence Score

**Root cause (lines 570-577):** Confidence is additive booleans (0.7 + 0.1 + 0.1 + 0.1). This is pseudo-random-seeded in spirit — it doesn't vary meaningfully between users.

**New confidence model:** Multiplicative weighted composite based on uncertainty sources (from NUTRITION_RESEARCH §8.2):

```python
def compute_confidence(profile, nutrition, training, horizon_weeks):
    """
    Principled confidence score. Each factor is grounded in a source of
    prediction error, not in data completeness.
    """
    # 1. Nutrition tracking accuracy (30-50% intake error if not tracking)
    tracking_factor = {
        "weighing": 1.00,
        "app": 0.90,
        "eyeballing": 0.65,
        "none": 0.50
    }[nutrition.tracking_method]

    # 2. Time horizon (longer = more uncertain; individual variation compounds)
    # Based on: 12-week RCT typical SD is ~30%, 52-week ~50%
    horizon_factor = max(0.55, 1.0 - (horizon_weeks / 52) * 0.35)

    # 3. Body fat estimate quality (if user estimated, not DEXA)
    bf_quality_factor = 0.85 if profile.bf_estimated else 1.0

    # 4. Protein certainty
    protein_factor = 1.0 if nutrition.protein_known else 0.80

    # 5. Training consistency (self-reported days/week vs actual adherence gap)
    consistency_factor = 0.70  # conservative: people overestimate adherence by ~30%
    # Can be raised to 1.0 if user has logged workouts in the app

    # 6. Experience level (beginner outcomes more variable than advanced)
    experience_factor = {
        "beginner": 0.85,      # High individual variance
        "intermediate": 0.95,  # More predictable
        "advanced": 0.90,      # Predictable but near-ceiling effects add noise
    }[profile.experience_level]

    # Weighted composite
    raw_score = (
        tracking_factor   * 0.25 +
        horizon_factor    * 0.25 +
        bf_quality_factor * 0.15 +
        protein_factor    * 0.15 +
        consistency_factor* 0.10 +
        experience_factor * 0.10
    )

    # Convert to confidence interval width:
    # Score 1.0 -> ±15% range around point estimate
    # Score 0.5 -> ±40% range around point estimate
    ci_half_width = 0.15 + (1.0 - raw_score) * 0.50
    return raw_score, ci_half_width
```

The confidence range is then applied to the predicted changes:

```python
low  = change * (1 - ci_half_width)
mid  = change
high = change * (1 + ci_half_width)
```

This gives the user a range (e.g., "8-14 lbs fat loss in 12 weeks") rather than a single number with a false-precision confidence score.

---

## 4. Proposed predictor.py Architecture

### What to Keep from Current File

- `Mifflin-St-Jeor BMR` — correct, keep
- `activity_multipliers` dict — keep, rename to match new spec
- `progress_curve` sigmoid — keep as a utility, but it's no longer used for weekly rollout (replaced by explicit weekly loop)
- `UserProfile` dataclass shell — refactor, keep structure
- `PredictionResult` dataclass — expand, keep as `GovernorResult`
- `predict_measurements()` — keep with updated coefficients

### New Module Structure

```
models/
├── predictor.py           # THIN orchestrator — calls other modules, returns GovernorResult
├── energy_balance.py      # Stage 1: BMR, TDEE, calorie balance
├── gain_rates.py          # Stage 3: Aragon/Helms, McDonald cap, FFMI ceiling
├── fat_loss.py            # Stage 3: weekly fat loss, floor, deceleration
├── simulator.py           # Stage 4: weekly loop — the core engine
├── measurements.py        # Stage 5: regional measurement deltas
├── confidence.py          # Stage 6: principled confidence + CI
├── constants.py           # All science-grounded constants with citations inline
└── schemas.py             # UserProfile, GoalSpec, NutritionSpec, TrainingSpec, GovernorResult
```

### Key Dataclasses (updated)

```python
# schemas.py

@dataclass
class UserProfile:
    age: int
    sex: Literal["M", "F"]
    height_m: float             # internal; UI accepts feet/inches
    weight_kg: float            # internal; UI accepts lbs
    bf_pct: float               # 3-60; validated
    years_training: float
    sleep_hrs_per_night: float = 7.5
    stress_level: int = 5       # 1-10
    genetic_potential: Literal["low", "average", "high"] = "average"
    bf_estimated: bool = True   # True if user guessed, False if DEXA/caliper

    @property
    def experience_level(self) -> str: ...  # derived from years_training
    @property
    def lean_mass_kg(self) -> float: ...
    @property
    def bmr(self) -> float: ...             # Mifflin-St-Jeor


@dataclass
class GoalSpec:
    primary: Literal["fat_loss", "muscle_gain", "recomp", "maintenance"]
    lean_preference: Literal["standard", "lean_bulk", "aggressive_bulk"] = "standard"
    acceptable_fat_gain_kg_per_month: float = 0.5


@dataclass
class NutritionSpec:
    daily_calories: Optional[int] = None   # None = infer
    protein_g: Optional[float] = None      # None = assume adequate
    tracking_method: Literal["weighing", "app", "eyeballing", "none"] = "none"

    @property
    def protein_known(self) -> bool: ...


@dataclass
class TrainingSpec:
    days_per_week: int = 4
    sets_per_muscle_per_week: int = 12   # assumed if not specified
    intensity: Literal["light", "moderate", "intense"] = "moderate"
    focus_muscle_groups: List[str] = field(default_factory=list)


@dataclass
class WeeklyState:
    week: int
    weight_kg: float
    fat_mass_kg: float
    lean_mass_kg: float
    bf_pct: float
    normalized_ffmi: float


@dataclass
class GovernorResult:
    final_state: WeeklyState
    initial_state: WeeklyState
    weekly_timeline: List[WeeklyState]
    mode: str
    confidence_score: float
    confidence_low_pct: float    # lower bound as % change
    confidence_high_pct: float   # upper bound as % change
    measurement_deltas: Dict[str, float]  # cm
    warnings: List[str]
    insights: List[str]
```

### Function Signatures (TDD targets)

```python
# energy_balance.py
def compute_tdee(profile: UserProfile, training: TrainingSpec) -> float: ...
def compute_daily_balance(goal: GoalSpec, nutrition: NutritionSpec, tdee: float,
                          experience: str, bf_pct: float) -> float: ...

# gain_rates.py
def aragon_helms_monthly_kg(weight_kg: float, experience: str, sex: str) -> float: ...
def apply_gain_modifiers(base_kg: float, profile: UserProfile,
                          training: TrainingSpec, nutrition: NutritionSpec) -> float: ...
def ffmi_ceiling_factor(normalized_ffmi: float) -> float: ...
def compute_normalized_ffmi(lean_mass_kg: float, height_m: float) -> float: ...

# fat_loss.py
def weekly_fat_loss_kg(daily_balance: float, current_weight_kg: float,
                        current_bf_pct: float, sex: str) -> float: ...
def compute_lean_penalty(current_bf_pct: float, sex: str) -> float: ...
def muscle_loss_fraction(weekly_loss_as_pct_bw: float) -> float: ...

# simulator.py
def simulate_weekly(profile: UserProfile, goal: GoalSpec, nutrition: NutritionSpec,
                     training: TrainingSpec, horizon_weeks: int) -> List[WeeklyState]: ...

# confidence.py
def compute_confidence(profile: UserProfile, nutrition: NutritionSpec,
                        training: TrainingSpec, horizon_weeks: int) -> Tuple[float, float]: ...
    # returns (score_0_to_1, ci_half_width)

# predictor.py (orchestrator)
def predict(profile: UserProfile, goal: GoalSpec, nutrition: NutritionSpec,
             training: TrainingSpec, horizon_weeks: int) -> GovernorResult: ...
```

---

## 5. Validation Plan

### 5.1 What the real_outcomes.json dataset actually is

473 records from r/progresspics and r/Brogress. Key stats:
- **57% started obese (>220 lbs) — this is the primary use case of the dataset, not PhysiqAI's target user**
- 65% female
- Median starting weight 235 lbs, median loss 75 lbs
- No body fat % labels — only scale weight
- 65 records show weight gain (muscle builders, eating disorder recovery — not weight loss)
- Duration median 17 months, P90 = 60 months
- No nutrition data, no training data

**This dataset validates fat loss at scale for obese individuals. It will NOT validate muscle gain, recomp, or lean intermediate users — PhysiqAI's actual target.**

### 5.2 Validation Protocol

**Step 1: Extract the "target population" subset from real_outcomes.json**

```python
# Filter to records closer to intermediate gym-goers
target_subset = [
    d for d in data
    if d['w_before'] <= 220          # not obese
    and abs(d['w_after'] - d['w_before']) <= 40  # not extreme transformation
    and d['months'] <= 12            # <= 1 year
    and d['months'] >= 2             # not suspiciously fast
]
# Expected: ~40-60 records
```

These are the only records where our engine is actually being tested on comparable users.

**Step 2: For each record, estimate starting BF using validated lookup**

Since no BF labels exist, impute using sex + BMI:
```
estimated_bf = bmi_sex_to_bf_lookup(bmi, sex)  # Deurenberg 1991 formula
```
Flag estimated BF as uncertain (±5pp), propagate to confidence.

**Step 3: Run the new Governor with conservative defaults**

```python
# For each record:
profile = UserProfile(age=d['age'], sex=d['sex'], height_m=..., weight_kg=...,
                      bf_pct=estimated_bf, years_training=1.0,  # unknown → intermediate
                      bf_estimated=True)
goal = GoalSpec(primary="fat_loss")
nutrition = NutritionSpec(tracking_method="none")  # unknown → worst case
result = predict(profile, goal, nutrition, training_default, horizon_weeks=d['months']*4)
```

**Step 4: Error metric**

Primary metric: **Mean Absolute Error (MAE) on total weight change (lbs)**

```
MAE = mean(|predicted_weight_change - actual_weight_change|)
```

Secondary: **Coverage rate** — what fraction of actual outcomes fall within the predicted confidence interval. A well-calibrated model should have 70-80% coverage for a 70% CI.

**Step 5: What "defensible" looks like numerically**

For the target subset (non-obese, ≤12 months):
- MAE ≤ 8 lbs on weight change is defensible (±1 lb/month, consistent with RCT variability)
- Coverage rate ≥ 65% for the 70% CI band
- Zero predictions below BF essential floor — this is a hard pass/fail

For the full dataset (obese, multi-year):
- We should explicitly NOT optimize for this — it's out-of-distribution. But the engine should not predict extreme outcomes (BF < 5% M / 13% F) for any record. This is the gut-check test.

**Step 6: Stratified analysis by known bias**

```
Subset by: sex, starting BMI (<25, 25-30, 30-35, 35+), duration (<6mo, 6-12mo, 12+mo)
Report MAE per cell to understand where the engine systematically over/underestimates
```

Expected finding: the engine will over-predict fat loss for obese, long-duration cases (because we model the floor). That's correct behavior — the dataset is out-of-distribution.

### 5.3 Muscle Gain Validation (separate test, no public dataset yet)

The real_outcomes.json cannot validate muscle gain. For the intermediate recomp/muscle-gain users, validation requires:
- Before/after with body fat % labeled (DEXA or calipers), not just scale weight
- Controlled nutrition data
- Training program known

The best available proxy is published RCTs. Pull 5-10 published 12-week progressive overload RCTs (beginner-intermediate males, 3-5 days/week) and check that the engine's predicted FFM gain is within 1 SD of the study means.

---

## 6. Data to Pull First (from Scouting Reports)

Based on the validation gaps identified above, priority order:

**Priority 1: NHANES body composition database (publicly available, free)**
- Why: Contains weight + body fat % + height + age + sex for thousands of US adults. Lets us build a better BF imputation model than BMI lookup, and gives us a population baseline to check our "final state" predictions against realistic human ranges.
- Access: https://www.cdc.gov/nchs/nhanes/ — download body composition examination files (BPX, BMX). No signup required.
- What to pull: Dual-energy X-ray absorptiometry (DXA) subset (~10K records with FFMI, BF%, lean mass). Filter to ages 18-55.

**Priority 2: DEXA-labeled before/after dataset (OpenBarbell / MacroFactor research cohort)**
- Why: This is the only path to validating the muscle gain and recomp predictions. Scale weight alone is insufficient for our target user.
- Access: MacroFactor's blog has published aggregated research data. Greg Nuckols at Stronger By Science has shared research cohort data. Start by emailing strongerbyscience.com research partnership — they have body comp data and have collaborated before.
- Alternative: search for published 12-24 week RCTs on PubMed with downloadable supplementary data tables (many are freely available).

**Priority 3: Published RCT data tables for intermediate lifters**
- Why: Quantifies the actual muscle gain distribution (mean + SD) for our core user, which calibrates the Aragon/Helms midpoints.
- Access: PubMed free full-text. Key searches: "resistance training body composition 12 weeks intermediate" — filter to PMC free full-text. Target studies: Schoenfeld 2015 (PMID 26285474), Morton 2018 (PMID 28698222), Barakat 2020 (PMID 33002134). Many have table 2 / table 3 with mean ± SD FFM change.

**Priority 4: r/Fitness / MyFitnessPal community posts with DEXA labels**
- Why: Closer to real-world intermediate users. Some r/loseit and r/gainit users post DEXA results before/after.
- Access: Reddit search via Pushshift API (or direct Reddit API). Filter to posts with "DEXA" or "body fat percentage" + before/after + specific months. Manual validation needed. Estimate 30-50 usable records.

**Priority 5: The Body Project datasets (if accessible)**
- Why: Large-scale body image / transformation dataset that may have body comp + outcomes.
- Access: Check https://osf.io/ and PsyArXiv for preregistered studies; some research groups post data publicly.

**Skip for now:** Commercial fitness app datasets (Fitbod, Hevy, etc.) — access requires partnership, long lead time.

---

## 7. Open Questions for Brian

These are decisions only you can make. Each has a recommendation, but the call is yours.

**Q1. What's the body fat input UX?**
The engine uses body fat % as a core input. But most users don't know their BF% accurately. Do we:
- (A) Ask for BF% and display a visual guide to help users estimate — easy to implement, introduces ±5pp error but user feels informed
- (B) Estimate from the photo upload using the Gemini analysis and never ask — better UX, but AI BF estimation from photos has ~3-5% error and could cause lawsuits if taken seriously
- (C) Show a "body type" picker (6-pack visible → ~8-12%, some definition → ~14-17%, etc.) — lowest friction, ~±4% error, probably the right MVP choice

**Recommendation: (C) for MVP.** Flag as estimated in the confidence model.

**Q2. Do we expose the confidence interval to users, or just the point estimate?**
Showing "you'll lose 8-14 lbs in 12 weeks" is more honest than "you'll lose 11 lbs." But it may feel wishy-washy to users who want a number to aim for.

**Recommendation:** Show the midpoint prominently, show the range in a secondary tooltip/footnote ("Based on typical variation, most people in your situation lose 8-14 lbs"). This is what MacroFactor does and users respond well to it.

**Q3. Lean bulk vs standard bulk — should the user explicitly choose, or infer from calories?**
Current design proposes `lean_preference` in `GoalSpec`. Alternative: just ask the user "how much fat gain are you comfortable with per month?" (0 / a little / don't care).

**Recommendation:** The simpler question ("how much fat gain is OK?") maps directly to `acceptable_fat_gain_kg_per_month` and avoids jargon. Use it.

**Q4. How should we handle users who are already near their FFMI ceiling?**
A 5'10" male at 185 lbs and 10% BF has normalized FFMI ~22 — still has headroom. But at 205 lbs and 8% BF, normalized FFMI ≈ 24.5 — very close to natural limit. The engine will show near-zero lean gain. This is honest but may feel demotivating.

**Recommendation:** When FFMI ≥ 24, surface an explicit message: "You're near your natural muscle limit — further gains will be very slow. Focus on strength, performance, and body fat optimization." Let Brian decide if this is a feature or a problem.

**Q5. Is the `years_training` input sufficiently granular, or do we need training-quality questions?**
Two people with "3 years training" could have wildly different outcomes if one trained consistently and progressively and one just showed up. The volume/frequency questions in `TrainingSpec` help, but we're still trusting self-report.

**Recommendation:** For MVP, keep years_training + days/week + sets/muscle as the inputs. For v2, consider a "training quality" self-assessment (1-5 scale: just going through motions → progressive overload every session). This is one of the highest-variance factors in intermediate predictions.

**Q6. Should we validate the engine against the real_outcomes.json before launch, or after?**
Validation requires building the test harness (2-3 days of engineering work) on top of building the engine itself. That test will reveal calibration issues that require engine tuning.

**Recommendation:** Build the engine first, ship to internal testing, run the validation in parallel. Do not block the visual demo on validation — but do not claim the predictions are "science-backed" in marketing until the MAE number is known and acceptable. The validation is a legal and reputational protection as much as an engineering one.

---

## Locked Decisions (Brian, 2026-05-29)

- **Q1 Inputs:** Collect a COMPREHENSIVE onboarding profile — body-type picker AND optional BF% AND
  training/diet/sleep/stress + standard fitness-app baseline questions — to calibrate the morph as
  deterministically as possible (never 100%, but maximize signal). See `docs/ONBOARDING_SPEC.md`.
- **Q2 Output:** Show midpoint prominently + honest range as secondary ("most people like you: 8-14 lb").
- **Q3 Bulk preference:** Explicit `lean / standard / aggressive` bulk picker (maps to `lean_preference`).
- **Q4 Near FFMI ceiling:** Soften/reframe — emphasize recomposition, strength, aesthetics; don't lead with "you've hit your limit," but stay honest.
- **Q5 training granularity:** keep years_training + days/week + sets/muscle for MVP (per rec).
- **Q6 validation timing:** build engine first, validate in parallel; do NOT market "science-backed" until MAE is known & acceptable (per rec).

## Appendix: Current Engine Critique Summary

| Issue | Location | Severity | Status |
|-------|----------|----------|--------|
| BF floor bug (5.1% in 6 mo) | `calculate_weight_loss_from_deficit()` lines 289-293 | Critical | Fixed by Stage 4 floor + deceleration |
| MUSCLE_GAIN always assumes surplus | `predict()` lines 492-503 | High | Fixed by GoalSpec.lean_preference |
| Female modifier wrong (0.7 vs 0.5) | `MUSCLE_GAIN_RATES` line 209 | Medium | Fixed by Aragon/Helms bodyweight anchor |
| Confidence score is additive booleans | lines 570-577 | Medium | Replaced with principled weighted composite |
| Flat gain-rate table (not BW-anchored) | `MUSCLE_GAIN_RATES` lines 209-213 | Medium | Replaced with Aragon/Helms % model |
| No FFMI ceiling | entire file | Medium | Added in Stage 2 + Stage 4 |
| 3500 kcal/lb (correct ballpark, no adaptation) | line 216 | Low | Kept with explicit metabolic adaptation factor |
| S-curve applied to weekly rollout (not physiological) | `progress_curve()` lines 373-388 | Low | Replaced with explicit weekly state loop |
| Confidence decreases linearly over time in workout_engine | workout_engine.py line 459 | Low | Replaced with structured score |