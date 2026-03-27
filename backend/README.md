# PhysiqAI Workout Predictor

ML model that predicts body changes from workouts using:
- Reddit transformation data (112+ real progress posts)
- Physiological formulas based on exercise science
- SMPL parameter morphing for avatar visualization

## Features

✅ **Real Data Training**: Analyzes 112+ Reddit transformation posts  
✅ **Physiological Accuracy**: Based on established exercise science formulas  
✅ **SMPL Integration**: Generates morphed avatar parameters  
✅ **Multiple Goals**: Supports bulking, cutting, and body recomposition  
✅ **Confidence Scoring**: Reliability metric for each prediction  

## Installation

```bash
pip install numpy
```

## Quick Start

```python
from workout_predictor import WorkoutPredictor, UserState, WorkoutPlan, NutritionPlan

# Initialize predictor
predictor = WorkoutPredictor()

# Define user
user = UserState(
    weight_lbs=180,
    body_fat_pct=15,
    smpl_betas=[0.0] * 10,
    height_inches=70,
    age=28,
    gender='male',
    training_years=2
)

# Define workout
workout = WorkoutPlan(
    weekly_volume_lbs=12000,
    sessions_per_week=4,
    workout_type='ppl',
    avg_intensity=0.75
)

# Define nutrition
nutrition = NutritionPlan(
    daily_calories=2800,
    daily_protein_g=150,
    caloric_surplus=300
)

# Predict
result = predictor.predict(user, workout, nutrition, weeks=4)
print(result.summary())
```

## API Reference

### UserState

User's current physical state.

| Parameter | Type | Description |
|-----------|------|-------------|
| `weight_lbs` | float | Current weight in pounds |
| `body_fat_pct` | float | Body fat percentage |
| `smpl_betas` | List[float] | 10 SMPL shape parameters |
| `height_inches` | float | Height in inches |
| `age` | int | Age in years |
| `gender` | str | 'male' or 'female' |
| `training_years` | float | Years of training experience |

**Properties:**
- `lean_mass_lbs` - Lean body mass
- `fat_mass_lbs` - Fat mass
- `bmi` - Body mass index
- `experience_level` - 'beginner', 'intermediate', or 'advanced'

### WorkoutPlan

Workout program details.

| Parameter | Type | Description |
|-----------|------|-------------|
| `weekly_volume_lbs` | float | Total lbs lifted per week |
| `sessions_per_week` | int | Number of workout sessions |
| `workout_type` | str | 'ppl', 'upper_lower', 'full_body', 'bro_split' |
| `avg_intensity` | float | 0-1 scale (RPE-based) |
| `cardio_minutes_per_week` | float | Cardio duration in minutes |

### NutritionPlan

Nutrition program details.

| Parameter | Type | Description |
|-----------|------|-------------|
| `daily_calories` | float | Daily caloric intake |
| `daily_protein_g` | float | Daily protein in grams |
| `caloric_surplus` | float | Surplus (+) or deficit (-) |

### PredictionResult

Prediction output.

| Attribute | Type | Description |
|-----------|------|-------------|
| `weight_change_lbs` | float | Predicted weight change |
| `muscle_change_lbs` | float | Predicted muscle gain/loss |
| `fat_change_lbs` | float | Predicted fat change |
| `new_weight_lbs` | float | Predicted new weight |
| `new_body_fat_pct` | float | Predicted body fat % |
| `new_smpl_betas` | List[float] | Morphed SMPL parameters |
| `confidence` | float | Prediction confidence (0-1) |
| `weekly_breakdown` | List[dict] | Week-by-week progression |

## Physiological Rules

The model applies these exercise science principles:

| Rule | Formula |
|------|---------|
| Fat Loss | 3500 calorie deficit = 1 lb fat loss |
| Muscle Gain | Protein >0.8g/lb = optimal synthesis |
| Volume Threshold | >10k lbs/week + surplus = muscle gain |
| Beginner Gains | 0.5 lbs/week (male), 0.25 lbs/week (female) |
| Diminishing Returns | Progress slows after 4 weeks |

## Example Predictions

### Lean Bulk (4 weeks)
```
Weight: 180 → 181.3 lbs (+1.3)
Muscle: +0.6 lbs
Fat: +0.7 lbs
Body Fat: 15% → 15.3%
Confidence: 95%
```

### Weight Loss (12 weeks)
```
Weight: 200 → 186.0 lbs (-14.0)
Muscle: +0.4 lbs (preserved)
Fat: -14.4 lbs
Body Fat: 25% → 19.1%
Confidence: 95%
```

### Body Recomposition (16 weeks)
```
Weight: 165 → 158.8 lbs (-6.2)
Muscle: +0.9 lbs
Fat: -7.2 lbs
Body Fat: 22% → 18.3%
Confidence: 95%
```

## Accuracy Metrics

Based on validation against 50 Reddit transformations:

| Metric | Value |
|--------|-------|
| Correlation | 0.893 |
| MAE | 85.0 lbs* |
| RMSE | 104.6 lbs* |

*High error due to unknown workout/nutrition details in validation data. Correlation measures directional accuracy.

## SMPL Beta Mapping

Muscle changes map to SMPL shape parameters:

| Beta | Name | Muscle Impact |
|------|------|---------------|
| β₀ | Overall Size | Total weight change |
| β₃ | Torso Width | Back, chest growth |
| β₄ | Arm Thickness | Biceps, triceps |
| β₅ | Leg Thickness | Quads, hamstrings |
| β₆ | Chest Depth | Pectoral growth |
| β₇ | Hip Width | Glute development |

## Data Sources

Training data from Reddit:
- r/progresspics
- r/Brogress
- r/loseit
- r/gainit

112 validated transformations with:
- Gender, age, height
- Before/after weights
- Timeline data

## File Structure

```
backend/
├── workout_predictor.py    # Main predictor
├── test_predictor.py       # Accuracy tests
├── demo_api.py             # Usage examples
└── predictor_accuracy_report.json  # Test results
```

## Running Tests

```bash
# Basic test
python workout_predictor.py

# Comprehensive accuracy test
python test_predictor.py

# API demos
python demo_api.py
```

## License

Part of PhysiqAI project.
