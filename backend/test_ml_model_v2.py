#!/usr/bin/env python3
"""
ML Model Validation and Testing Script
Validates the improved model against 50 Reddit transformations
and runs test scenarios.
"""

import json
import sys
import random
import re
from pathlib import Path
from datetime import datetime
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from ml_model_v2 import ImprovedPredictionEngine, UserProfile, NutritionPlan


def load_reddit_transformations(n_samples=50):
    """Load Reddit transformation data for validation."""
    data_dir = Path('/home/clawd/.openclaw/workspace/data/raw_reddit')
    all_data = []

    json_files = list(data_dir.glob('*.json'))
    print(f"Found {len(json_files)} data files")

    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_data.extend(data)
                elif isinstance(data, dict) and 'transformations' in data:
                    all_data.extend(data['transformations'])
        except Exception as e:
            continue

    print(f"Loaded {len(all_data)} total records")

    # Parse transformations
    transformations = []
    for post in all_data:
        try:
            weight_before = post.get('weight_before_lbs')
            weight_after = post.get('weight_after_lbs')
            gender = post.get('gender', '').lower()
            title = post.get('title', '')

            # Extract from title if needed
            if not weight_before or not weight_after:
                weight_pattern = r'\[(\d+)\s*lbs?\s*[>→]\s*(\d+)\s*lbs?\s*=\s*(\d+)\s*lbs?\]'
                match = re.search(weight_pattern, title, re.IGNORECASE)
                if match:
                    weight_before = float(match.group(1))
                    weight_after = float(match.group(2))

            if not weight_before or not weight_after:
                continue
            if weight_before < 80 or weight_after < 80:
                continue
            if weight_before > 600 or weight_after > 600:
                continue

            # Extract timeline
            timeline_days = 180  # Default
            time_patterns = [
                r'(\d+)\s*(months?|weeks?|years?)',
                r'\((\d+)\s*(months?|weeks?|years?)\)',
            ]
            for pattern in time_patterns:
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    num = int(match.group(1))
                    unit = match.group(2).lower()
                    if 'year' in unit:
                        timeline_days = num * 365
                    elif 'month' in unit:
                        timeline_days = num * 30
                    elif 'week' in unit:
                        timeline_days = num * 7
                    break

            weight_change = weight_after - weight_before

            # Estimate body fat
            if gender == 'female':
                body_fat = 28 if weight_before < 160 else 35
            else:
                body_fat = 18 if weight_before < 180 else 25

            transformations.append({
                'id': post.get('id'),
                'title': title[:80],
                'gender': gender if gender in ['male', 'female'] else 'male',
                'weight_before': float(weight_before),
                'weight_after': float(weight_after),
                'weight_change': float(weight_change),
                'timeline_days': timeline_days,
                'body_fat': body_fat,
                'subreddit': post.get('subreddit', 'unknown')
            })
        except Exception as e:
            continue

    print(f"Parsed {len(transformations)} valid transformations")

    # Sample n with stratification
    if len(transformations) > n_samples:
        loss_cases = [t for t in transformations if t['weight_change'] < 0]
        gain_cases = [t for t in transformations if t['weight_change'] >= 0]

        n_loss = min(n_samples // 2, len(loss_cases))
        n_gain = min(n_samples - n_loss, len(gain_cases))

        random.seed(42)
        sampled = random.sample(loss_cases, n_loss) + random.sample(gain_cases, n_gain)
        return sampled

    return transformations


def validate_model(n_samples=50):
    """Validate model against Reddit transformations."""
    print("\n" + "="*80)
    print("VALIDATING MODEL AGAINST REDDIT TRANSFORMATIONS")
    print("="*80)

    engine = ImprovedPredictionEngine()
    transformations = load_reddit_transformations(n_samples)

    errors = []
    failure_cases = []
    edge_cases = []

    for i, t in enumerate(transformations[:n_samples]):
        # Create user profile
        user = UserProfile(
            weight_lbs=t['weight_before'],
            body_fat_pct=t['body_fat'],
            height_inches=70,
            age=30,
            gender=t['gender'],
            training_years=1,
            training_frequency=3,
            sleep_hours=7,
            stress_level=5
        )

        # Create nutrition plan based on goal
        weeks = min(int(t['timeline_days'] / 7), 52)
        if t['weight_change'] < 0:
            nutrition = NutritionPlan(daily_calories=2000, daily_protein_g=150, caloric_surplus=-400)
        else:
            nutrition = NutritionPlan(daily_calories=2800, daily_protein_g=160, caloric_surplus=300)

        # Predict
        prediction = engine.predict(user, nutrition, weeks)

        actual = t['weight_change']
        predicted = prediction.weight_change_lbs
        error = abs(actual - predicted)
        pct_error = error / abs(actual) * 100 if actual != 0 else 0

        errors.append({
            'actual': actual,
            'predicted': predicted,
            'error': error,
            'pct_error': pct_error
        })

        if pct_error > 30:
            failure_cases.append({
                'title': t['title'][:50],
                'actual': actual,
                'predicted': round(predicted, 1),
                'error_pct': round(pct_error, 1)
            })

        if abs(actual) > 50 or weeks > 52:
            edge_cases.append({
                'title': t['title'][:50],
                'weight_change': actual,
                'weeks': weeks
            })

    # Calculate metrics
    actual_values = [e['actual'] for e in errors]
    predicted_values = [e['predicted'] for e in errors]
    error_values = [e['error'] for e in errors]
    pct_errors = [e['pct_error'] for e in errors]

    mae = np.mean(error_values)
    rmse = np.sqrt(np.mean([e**2 for e in error_values]))
    mape = np.mean(pct_errors)

    if len(actual_values) > 1:
        correlation = np.corrcoef(actual_values, predicted_values)[0, 1]
    else:
        correlation = 0

    within_10 = sum(1 for e in pct_errors if e <= 10) / len(pct_errors) * 100
    within_20 = sum(1 for e in pct_errors if e <= 20) / len(pct_errors) * 100

    print(f"\nValidation Results ({len(errors)} samples):")
    print(f"  MAE: {mae:.2f} lbs")
    print(f"  RMSE: {rmse:.2f} lbs")
    print(f"  MAPE: {mape:.2f}%")
    print(f"  Correlation: {correlation:.3f}")
    print(f"  Accuracy within 10%: {within_10:.1f}%")
    print(f"  Accuracy within 20%: {within_20:.1f}%")

    print(f"\nFailure cases (>30% error): {len(failure_cases)}")
    for f in failure_cases[:5]:
        print(f"  - {f['title']}")
        print(f"    Actual: {f['actual']:.1f}, Predicted: {f['predicted']:.1f}, Error: {f['error_pct']:.1f}%")

    return {
        'mae': mae,
        'rmse': rmse,
        'mape': mape,
        'correlation': correlation,
        'accuracy_within_10pct': within_10,
        'accuracy_within_20pct': within_20,
        'sample_size': len(errors),
        'failure_cases': failure_cases,
        'edge_cases': edge_cases
    }


def run_test_scenarios():
    """Run the three test scenarios."""
    print("\n" + "="*80)
    print("TEST SCENARIOS")
    print("="*80)

    engine = ImprovedPredictionEngine()
    results = {}

    # Scenario A: Beginner male cutting
    print("\n" + "-"*80)
    print("SCENARIO A: 200 lbs, 30% fat, beginner, 3x/week")
    print("-"*80)

    user_a = UserProfile(
        weight_lbs=200,
        body_fat_pct=30,
        height_inches=70,
        age=28,
        gender='male',
        training_years=0.5,
        training_frequency=3,
        sleep_hours=6.5,
        stress_level=7,
        body_type='endomorph'
    )
    nutrition_a = NutritionPlan(daily_calories=2200, daily_protein_g=160, caloric_surplus=-300)
    result_a = engine.predict(user_a, nutrition_a, weeks=12)

    print(f"Predicted weight change: {result_a.weight_change_lbs:+.1f} lbs")
    print(f"Muscle gain: {result_a.muscle_change_lbs:+.1f} lbs")
    print(f"Fat loss: {result_a.fat_change_lbs:+.1f} lbs")
    print(f"New body fat: {result_a.new_body_fat_pct:.1f}%")
    print(f"Confidence: {result_a.confidence_score*100:.0f}%")
    print(f"Range: {result_a.weight_change_range[0]:.1f} to {result_a.weight_change_range[1]:.1f} lbs")
    print(f"Key factors: {', '.join(result_a.key_factors)}")

    results['scenario_a'] = result_a.to_dict()

    # Scenario B: Advanced male bulking
    print("\n" + "-"*80)
    print("SCENARIO B: 160 lbs, 12% fat, advanced, 6x/week")
    print("-"*80)

    user_b = UserProfile(
        weight_lbs=160,
        body_fat_pct=12,
        height_inches=70,
        age=30,
        gender='male',
        training_years=5,
        training_frequency=6,
        sleep_hours=8,
        stress_level=4,
        body_type='mesomorph',
        protein_timing='optimal',
        progressive_overload=True
    )
    nutrition_b = NutritionPlan(daily_calories=3200, daily_protein_g=200, caloric_surplus=400)
    result_b = engine.predict(user_b, nutrition_b, weeks=12)

    print(f"Predicted weight change: {result_b.weight_change_lbs:+.1f} lbs")
    print(f"Muscle gain: {result_b.muscle_change_lbs:+.1f} lbs")
    print(f"Fat gain: {result_b.fat_change_lbs:+.1f} lbs")
    print(f"New body fat: {result_b.new_body_fat_pct:.1f}%")
    print(f"Confidence: {result_b.confidence_score*100:.0f}%")
    print(f"Range: {result_b.weight_change_range[0]:.1f} to {result_b.weight_change_range[1]:.1f} lbs")
    print(f"Key factors: {', '.join(result_b.key_factors)}")

    results['scenario_b'] = result_b.to_dict()

    # Scenario C: Intermediate with diet change
    print("\n" + "-"*80)
    print("SCENARIO C: 180 lbs, 20% fat, intermediate, diet change")
    print("-"*80)

    user_c = UserProfile(
        weight_lbs=180,
        body_fat_pct=20,
        height_inches=69,
        age=32,
        gender='male',
        training_years=2,
        training_frequency=4,
        sleep_hours=7,
        stress_level=6,
        body_type='mesomorph'
    )
    nutrition_c = NutritionPlan(daily_calories=2400, daily_protein_g=180, caloric_surplus=-200)
    result_c = engine.predict(user_c, nutrition_c, weeks=12)

    print(f"Predicted weight change: {result_c.weight_change_lbs:+.1f} lbs")
    print(f"Muscle gain: {result_c.muscle_change_lbs:+.1f} lbs")
    print(f"Fat loss: {result_c.fat_change_lbs:+.1f} lbs")
    print(f"New body fat: {result_c.new_body_fat_pct:.1f}%")
    print(f"Confidence: {result_c.confidence_score*100:.0f}%")
    print(f"Range: {result_c.weight_change_range[0]:.1f} to {result_c.weight_change_range[1]:.1f} lbs")
    print(f"Key factors: {', '.join(result_c.key_factors)}")

    results['scenario_c'] = result_c.to_dict()

    return results


def generate_report(validation_results, scenario_results):
    """Generate comprehensive report."""
    report = {
        'timestamp': datetime.now().isoformat(),
        'model_version': '2.0',
        'validation': validation_results,
        'scenarios': scenario_results,
        'improvements': [
            'Added sleep quality factor (7-9 hours optimal)',
            'Added stress level factor (cortisol impact)',
            'Added protein timing factor (post-workout)',
            'Added progressive overload tracking',
            'Added body type (somatotype) adjustments',
            'Added age-specific modifiers',
            'Improved confidence scoring with uncertainty',
            'Added prediction ranges (best/worst case)',
            'Added similar user comparisons'
        ]
    }

    output_path = Path('/home/clawd/.openclaw/workspace/projects/physiqai/backend/ml_model_v2_report.json')
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\nReport saved to: {output_path}")
    return report


if __name__ == "__main__":
    # Run validation
    validation = validate_model(n_samples=50)

    # Run test scenarios
    scenarios = run_test_scenarios()

    # Generate report
    report = generate_report(validation, scenarios)

    print("\n" + "="*80)
    print("VALIDATION COMPLETE")
    print("="*80)
