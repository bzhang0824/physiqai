# PhysiqAI Workout Predictor - Integration Guide

**Version:** 2.0  
**Last Updated:** 2026-02-27

---

## Overview

This guide explains how to integrate the optimized workout predictor with the avatar morphing system.

---

## Quick Start

### 1. Import the Predictor

```python
from workout_predictor_fast import OptimizedPredictor, UserProfile, WorkoutPlan, NutritionPlan

# Initialize predictor (auto-trains on synthetic data)
predictor = OptimizedPredictor(cache_size=128)
```

### 2. Create User Profile

```python
user = UserProfile(
    weight_lbs=180,
    height_inches=70,
    age=28,
    gender='male',
    body_fat_pct=15,
    training_years=2,
    training_frequency=4,
    sleep_hours=7.5,
    stress_level=4,
    body_type='mesomorph',
    smpl_betas=[0.0] * 10  # Current avatar betas
)
```

### 3. Create Workout Plan

```python
workout = WorkoutPlan(
    weekly_volume_lbs=15000,
    sessions_per_week=4,
    workout_type='ppl',  # 'ppl', 'upper_lower', 'full_body', 'bro_split', 'phat'
    avg_intensity=0.75,
    cardio_minutes_per_week=60,
    progressive_overload=True
)
```

### 4. Create Nutrition Plan

```python
nutrition = NutritionPlan(
    daily_calories=2800,
    daily_protein_g=180,
    caloric_surplus=300,
    protein_timing='optimal'  # 'poor', 'average', 'optimal'
)
```

### 5. Make Prediction

```python
result = predictor.predict(user, workout, nutrition, weeks=12)

print(result.summary())
print(f"New betas: {result.new_smpl_betas}")
```

---

## Avatar Morphing Integration

### Basic Integration

```python
from avatar.morphing.body_mapper import BodyToSMPLMapper
from workout_predictor_fast import OptimizedPredictor

class AvatarPredictionPipeline:
    def __init__(self):
        self.predictor = OptimizedPredictor()
        self.body_mapper = BodyToSMPLMapper(gender='male')
    
    def predict_and_morph(self, user, workout, nutrition, weeks):
        # Get prediction
        result = self.predictor.predict(user, workout, nutrition, weeks)
        
        # New betas are in result.new_smpl_betas
        new_betas = result.new_smpl_betas
        
        return {
            'predicted_betas': new_betas,
            'weight_change': result.weight_change_lbs,
            'muscle_change': result.muscle_change_lbs,
            'fat_change': result.fat_change_lbs,
            'confidence': result.confidence,
            'weekly_breakdown': result.weekly_breakdown
        }
```

### Advanced Integration with Timeline

```python
import numpy as np
from datetime import datetime, timedelta

class TimelineMorphController:
    """Generate smooth avatar morphs over time"""
    
    def __init__(self):
        self.predictor = OptimizedPredictor()
    
    def generate_weekly_morphs(self, user, workout, nutrition, weeks):
        """Generate avatar state for each week"""
        result = self.predictor.predict(user, workout, nutrition, weeks)
        
        morphs = []
        base_betas = user.smpl_betas or [0.0] * 10
        
        for week_data in result.weekly_breakdown:
            week = week_data['week']
            progress = week / weeks
            
            # Interpolate betas
            target_betas = result.new_smpl_betas
            current_betas = [
                base + (target - base) * progress
                for base, target in zip(base_betas, target_betas)
            ]
            
            morphs.append({
                'week': week,
                'betas': current_betas,
                'weight': user.weight_lbs + week_data['cumulative_weight'],
                'confidence': result.confidence * (1 - progress * 0.3)  # Decreases over time
            })
        
        return morphs
```

---

## API Integration

### Flask/FastAPI Endpoint Example

```python
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()
predictor = OptimizedPredictor()

class UserInput(BaseModel):
    weight_lbs: float
    height_inches: float
    age: int
    gender: str
    body_fat_pct: float
    training_years: float = 0
    training_frequency: int = 3
    sleep_hours: float = 7.0
    stress_level: int = 5
    body_type: str = 'mesomorph'
    smpl_betas: Optional[List[float]] = None

class WorkoutInput(BaseModel):
    weekly_volume_lbs: float
    sessions_per_week: int
    workout_type: str
    avg_intensity: float = 0.7
    cardio_minutes_per_week: float = 0
    progressive_overload: bool = False

class NutritionInput(BaseModel):
    daily_calories: float
    daily_protein_g: float
    caloric_surplus: float = 0
    protein_timing: str = 'average'

class PredictionRequest(BaseModel):
    user: UserInput
    workout: WorkoutInput
    nutrition: NutritionInput
    weeks: int = 12

@app.post("/api/v1/predict")
def predict_physique(request: PredictionRequest):
    # Convert to internal types
    user = UserProfile(**request.user.dict())
    workout = WorkoutPlan(**request.workout.dict())
    nutrition = NutritionPlan(**request.nutrition.dict())
    
    # Predict
    result = predictor.predict(user, workout, nutrition, request.weeks)
    
    return {
        'weight_change_lbs': result.weight_change_lbs,
        'muscle_change_lbs': result.muscle_change_lbs,
        'fat_change_lbs': result.fat_change_lbs,
        'new_weight_lbs': result.new_weight_lbs,
        'new_body_fat_pct': result.new_body_fat_pct,
        'new_smpl_betas': result.new_smpl_betas,
        'confidence': result.confidence,
        'confidence_interval': result.confidence_interval,
        'weekly_breakdown': result.weekly_breakdown,
        'key_factors': result.key_factors
    }
```

---

## Caching Strategy

The predictor includes built-in LRU caching:

```python
# Initialize with cache size (default 128)
predictor = OptimizedPredictor(cache_size=256)

# First call - computes and caches
result1 = predictor.predict(user, workout, nutrition, 12)

# Second call with same parameters - returns cached result instantly
result2 = predictor.predict(user, workout, nutrition, 12)
```

**Cache Key:** Hash of (weight, body_fat, training_years, volume, surplus, weeks)

---

## Error Handling

```python
from workout_predictor_fast import OptimizedPredictor, UserProfile, WorkoutPlan, NutritionPlan

def safe_predict(predictor, user_data, workout_data, nutrition_data, weeks):
    try:
        # Validate inputs
        if user_data['weight_lbs'] < 80 or user_data['weight_lbs'] > 500:
            raise ValueError("Weight out of realistic range")
        
        if weeks < 1 or weeks > 52:
            raise ValueError("Weeks must be between 1 and 52")
        
        # Create objects
        user = UserProfile(**user_data)
        workout = WorkoutPlan(**workout_data)
        nutrition = NutritionPlan(**nutrition_data)
        
        # Predict
        result = predictor.predict(user, workout, nutrition, weeks)
        
        # Validate output
        if abs(result.weight_change_lbs) > weeks * 3:
            return {'error': 'Prediction exceeds realistic bounds', 'confidence': 0}
        
        return {'success': True, 'result': result}
        
    except Exception as e:
        return {'error': str(e), 'confidence': 0}
```

---

## Performance Optimization

### Inference Speed
- Cached predictions: ~0.1ms
- New predictions: ~5-10ms
- Model training (one-time): ~2-5 seconds

### Memory Usage
- Model size: ~500KB
- Cache (128 entries): ~100KB
- Total footprint: <2MB

### Batch Predictions
```python
def batch_predict(predictor, cases):
    """Predict for multiple users efficiently"""
    results = []
    for user, workout, nutrition, weeks in cases:
        result = predictor.predict(user, workout, nutrition, weeks)
        results.append(result)
    return results
```

---

## Testing

### Unit Tests
```python
def test_predictor():
    predictor = OptimizedPredictor()
    
    # Test case: Beginner bulk
    user = UserProfile(
        weight_lbs=160, height_inches=70, age=25,
        gender='male', body_fat_pct=12, training_years=0.5
    )
    workout = WorkoutPlan(
        weekly_volume_lbs=15000, sessions_per_week=4, workout_type='ppl'
    )
    nutrition = NutritionPlan(
        daily_calories=3000, daily_protein_g=180, caloric_surplus=500
    )
    
    result = predictor.predict(user, workout, nutrition, weeks=12)
    
    # Assertions
    assert result.weight_change_lbs > 0, "Bulk should gain weight"
    assert result.muscle_change_lbs > 0, "Bulk should gain muscle"
    assert result.confidence > 0.7, "Confidence should be reasonable"
    assert len(result.new_smpl_betas) == 10, "Should return 10 betas"
```

---

## Troubleshooting

### Issue: Predictions seem unrealistic
**Solution:** Check physiological constraints are being applied:
```python
# Verify constraint values
predictor.MIN_BODY_FAT_MALE = 8.0
predictor.MAX_MUSCLE_GAIN_MALE = 0.5
```

### Issue: Slow predictions
**Solution:** Increase cache size or check for repeated calculations:
```python
# Use larger cache
predictor = OptimizedPredictor(cache_size=512)

# Check cache hit rate (add logging to _get_cache_key)
```

### Issue: SMPL betas out of range
**Solution:** Clamp betas to valid range:
```python
new_betas = [max(-3.0, min(3.0, b)) for b in result.new_smpl_betas]
```

---

## Migration from Old Model

### Old API
```python
from workout_predictor import WorkoutPredictor, UserState, WorkoutPlan, NutritionPlan

predictor = WorkoutPredictor()
user = UserState(...)
result = predictor.predict(user, workout, nutrition, weeks)
```

### New API
```python
from workout_predictor_fast import OptimizedPredictor, UserProfile, WorkoutPlan, NutritionPlan

predictor = OptimizedPredictor()
user = UserProfile(...)  # Note: UserState -> UserProfile
result = predictor.predict(user, workout, nutrition, weeks)
```

**Key Changes:**
- `UserState` → `UserProfile`
- Added confidence intervals
- Added key_factors
- Added weekly_breakdown
- SMPL betas now properly integrated

---

## Support

For issues or questions:
1. Check accuracy_report.md for expected behavior
2. Review test cases in workout_predictor_fast.py
3. Verify input ranges are within realistic bounds

---

*Integration guide for PhysiqAI Workout Predictor v2.0*
