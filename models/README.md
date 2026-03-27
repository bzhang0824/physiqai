# PhysiqAI Workout-to-Body Prediction Engine

## Overview

This prediction engine converts workout and nutrition data into predicted body composition changes. It's built on analysis of Reddit progress data (r/progresspics, r/Brogress) and exercise science research.

## Core Formulas

### 1. Weight Loss from Calorie Deficit

Based on analysis of 99 weight loss cases from r/progresspics:

```
Weight Loss Rate (lbs/month):
- Aggressive: 13.4 lbs/mo (P90 - very dedicated)
- Moderate: 7.7 lbs/mo (mean - typical)
- Conservative: 3.0 lbs/mo (P25 - sustainable)

Formula:
Daily Deficit × 7 days × weeks × metabolic adaptation
------------------------------------------------------------
                    3500 calories/lb

Metabolic adaptation: -1.5% per week (min 70% effectiveness)
```

**Research Data:**
- Mean: 7.7 lbs/month
- Median: 7.1 lbs/month
- Range: 1.7 - 17.1 lbs/month
- 90% of successful cases fall between 1.7-13.4 lbs/month

### 2. Muscle Gain from Training + Protein

Based on exercise science literature:

```
Base Rates (lbs/month):
┌───────────────┬────────┬────────┐
│ Experience    │ Male   │ Female │
├───────────────┼────────┼────────┤
│ Beginner      │ 2.0    │ 1.0    │
│ Intermediate  │ 1.0    │ 0.5    │
│ Advanced      │ 0.5    │ 0.25   │
└───────────────┴────────┴────────┘

Modifiers:
- Age: -2% per year after 30 (floor 60%)
- Gender: Male = 1.0, Female = 0.7
- Genetics: Low = 0.7, Average = 1.0, High = 1.4
- Lifestyle: Sleep × Nutrition × Stress (0.3-1.0)
- Frequency: 0.5 + (days/week × 0.15), max 1.3
- Intensity: Light = 0.7, Moderate = 1.0, Intense = 1.25
- Protein: <0.5g/lb = 0.5, 0.5-0.8g/lb = 0.7-1.0, >0.8g/lb = 1.0

Diminishing Returns:
Each month, effectiveness decreases by log curve
Floor at 50% of initial rate
```

**Protein Requirements:**
- Minimum: 0.5g per lb bodyweight
- Optimal for muscle gain: 0.7-1.0g per lb bodyweight

### 3. Progress Curves (Timeline)

Real progress follows an S-curve (sigmoid):

```
Progress at week t:
                    1
    p(t) = ─────────────────
           1 + e^(-8(t-0.5))

Where t = week / total_weeks (0-1)

Characteristics:
- Weeks 1-2: Slow start (neural adaptations)
- Weeks 3-8: Rapid progress
- Weeks 9+: Diminishing returns (approaching genetic limit)
```

## Usage

### Basic Example

```python
from models.predictor import BodyPredictor, UserProfile, WorkoutPlan
from models.predictor import Gender, WorkoutType

# Create user profile
profile = UserProfile(
    age=28,
    gender=Gender.MALE,
    height_inches=70,  # 5'10"
    weight_lbs=180,
    body_fat_percent=20,
    years_training=1.5
)

# Create workout plan
workout = WorkoutPlan(
    workout_type=WorkoutType.WEIGHT_LOSS,
    days_per_week=4,
    cardio_days_per_week=3,
    daily_calories=1800,
    daily_protein_g=150
)

# Get prediction
predictor = BodyPredictor()
result = predictor.predict(profile, workout, weeks=12)

print(f"Weight: {result.weight_lbs:.1f} lbs ({result.weight_change_lbs:+.1f})")
print(f"Body Fat: {result.body_fat_percent:.1f}%")
print(f"Lean Mass: {result.lean_mass_lbs:.1f} lbs")
```

### Prediction Result

```python
PredictionResult(
    weight_lbs=165.2,              # Final predicted weight
    body_fat_percent=15.8,         # Final body fat %
    lean_mass_lbs=139.1,           # Final lean mass
    weight_change_lbs=-14.8,       # Total weight change
    body_fat_change_percent=-4.2,  # Body fat change
    lean_mass_change_lbs=+1.2,     # Lean mass change
    weekly_weights=[...],          # Week-by-week progression
    weekly_body_fat=[...],
    weekly_lean_mass=[...],
    confidence_score=0.85,         # 0-1 confidence
    insights=[...],                # Personalized insights
    warnings=[...]                 # Any warnings
)
```

### Workout Types

1. **WEIGHT_LOSS**: Calorie deficit, prioritizes fat loss
   - Expect: 1-3 lbs/week initially, slowing over time
   - Some muscle loss inevitable (10-20% of weight lost)

2. **MUSCLE_GAIN**: Calorie surplus, prioritizes hypertrophy
   - Expect: 0.5-2 lbs lean mass/month (beginner), 0.25-1 lbs (advanced)
   - Some fat gain inevitable (20-30% of weight gained)

3. **BODY_RECOMP**: Slight deficit, simultaneous loss + gain
   - Expect: Slower progress in both directions
   - Best for: beginners, returning trainees, or those with 15-25% body fat

4. **MAINTENANCE**: No net weight change
   - Expect: Minimal muscle gain, body composition improvements

## Data Sources

### Reddit Analysis
- **r/progresspics**: 7142 posts analyzed
- Weight loss rate: 7.7 lbs/month average
- Extracted patterns for realistic expectations

### Exercise Science
- Muscle gain rates from peer-reviewed literature
- Protein synthesis research
- Metabolic adaptation studies

### Body Composition
- NHANES dataset integration
- Kaggle body fat prediction datasets
- Body measurement correlations

## Key Insights from Data

### Weight Loss
- **Realistic expectation**: 1-2 lbs/week for most people
- **Aggressive is possible**: Up to 4-5 lbs/week for very overweight
- **Slows over time**: Metabolic adaptation reduces effectiveness
- **Muscle preservation**: Higher protein + resistance training reduces muscle loss

### Muscle Gain
- **Beginner advantage**: Can gain 2 lbs/month in first year
- **Diminishing returns**: Rate halves every 1-2 years of training
- **Genetics matter**: Up to 2x difference between individuals
- **Protein is critical**: Below 0.5g/lb severely limits gains

### Body Recomposition
- **Possible but slow**: 60% the rate of dedicated bulk/cut
- **Best for**: Beginners, returning after break, or 15-25% body fat
- **Requires precision**: Small deficit (200-300 cal) + high protein

## Confidence Scoring

Predictions include a confidence score (0-1):

- **0.7**: Basic info only (age, gender, weight)
- **0.8**: + Body fat % known
- **0.9**: + Training history + nutrition data
- **0.95**: Complete profile with detailed plan

## Limitations

1. **Individual variation**: Genetics can cause 2x difference in results
2. **Adherence matters**: Assumes 85%+ compliance with plan
3. **Plateaus**: Model accounts for diminishing returns but not full plateaus
4. **Health conditions**: Not adjusted for medical conditions
5. **Prediction horizon**: Confidence decreases beyond 6 months

## Integration with SMPL Avatar

The predictor can output SMPL body model parameters:

```python
from experimental.smpl_predictor import WorkoutPredictor

# Convert body changes to SMPL parameters
smpl_predictor = WorkoutPredictor()
smpl_result = smpl_predictor.predict(profile, workout, weeks=12)

# Apply to avatar
avatar.apply_shape_changes(smpl_result.smpl_changes.beta_delta)
```

## Testing

Run built-in tests:

```bash
cd projects/physiqai
python3 models/predictor.py
```

This runs 3 test cases:
1. Female weight loss (16 weeks)
2. Male muscle gain (12 weeks)
3. Body recomposition (20 weeks)

## Future Improvements

- [ ] Add more Reddit data sources (r/gainit, r/fitness)
- [ ] Machine learning model for pattern recognition
- [ ] Integration with wearable data
- [ ] Personalized adjustment based on actual results
- [ ] Age/sex-specific curve fitting
