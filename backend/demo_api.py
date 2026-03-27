"""
PhysiqAI Workout Predictor - Demo API Usage
============================================
Simple examples showing how to use the workout predictor.
"""

from workout_predictor import (
    WorkoutPredictor, UserState, WorkoutPlan, NutritionPlan
)


def demo_basic_prediction():
    """Basic prediction example"""
    print("=" * 60)
    print("DEMO: Basic Prediction")
    print("=" * 60)

    # Initialize predictor (loads Reddit data)
    predictor = WorkoutPredictor()

    # Define user state
    user = UserState(
        weight_lbs=180,
        body_fat_pct=15,
        smpl_betas=[0.0] * 10,  # 10 SMPL shape parameters
        height_inches=70,
        age=28,
        gender='male',
        training_years=2
    )

    # Define workout plan
    workout = WorkoutPlan(
        weekly_volume_lbs=12000,  # Total lbs lifted per week
        sessions_per_week=4,
        workout_type='ppl',  # Push/Pull/Legs
        avg_intensity=0.75,  # 75% intensity
        cardio_minutes_per_week=60
    )

    # Define nutrition plan
    nutrition = NutritionPlan(
        daily_calories=2800,
        daily_protein_g=150,
        caloric_surplus=300  # 300 cal surplus for bulking
    )

    # Predict 4 weeks into future
    result = predictor.predict(user, workout, nutrition, weeks=4)

    # Display results
    print(result.summary())

    return result


def demo_weight_loss():
    """Weight loss prediction example"""
    print("\n" + "=" * 60)
    print("DEMO: Weight Loss Prediction")
    print("=" * 60)

    predictor = WorkoutPredictor()

    user = UserState(
        weight_lbs=200,
        body_fat_pct=25,
        smpl_betas=[0.0] * 10,
        height_inches=68,
        age=35,
        gender='male',
        training_years=1
    )

    workout = WorkoutPlan(
        weekly_volume_lbs=8000,
        sessions_per_week=3,
        workout_type='full_body',
        avg_intensity=0.70,
        cardio_minutes_per_week=150
    )

    nutrition = NutritionPlan(
        daily_calories=2000,
        daily_protein_g=160,
        caloric_surplus=-500  # 500 cal deficit for fat loss
    )

    result = predictor.predict(user, workout, nutrition, weeks=12)
    print(result.summary())

    return result


def demo_body_recomposition():
    """Body recomposition example (lose fat, gain muscle)"""
    print("\n" + "=" * 60)
    print("DEMO: Body Recomposition")
    print("=" * 60)

    predictor = WorkoutPredictor()

    user = UserState(
        weight_lbs=165,
        body_fat_pct=22,
        smpl_betas=[0.0] * 10,
        height_inches=66,
        age=27,
        gender='female',
        training_years=0.5  # Beginner - recomp works best
    )

    workout = WorkoutPlan(
        weekly_volume_lbs=10000,
        sessions_per_week=4,
        workout_type='upper_lower',
        avg_intensity=0.72,
        cardio_minutes_per_week=90
    )

    # Slight deficit but high protein
    nutrition = NutritionPlan(
        daily_calories=1700,
        daily_protein_g=135,  # 0.82g/lb - optimal
        caloric_surplus=-200
    )

    result = predictor.predict(user, workout, nutrition, weeks=16)
    print(result.summary())

    return result


def demo_weekly_progression():
    """Show week-by-week progression"""
    print("\n" + "=" * 60)
    print("DEMO: Weekly Progression")
    print("=" * 60)

    predictor = WorkoutPredictor()

    user = UserState(
        weight_lbs=175,
        body_fat_pct=18,
        smpl_betas=[0.0] * 10,
        height_inches=69,
        age=25,
        gender='male',
        training_years=1
    )

    workout = WorkoutPlan(
        weekly_volume_lbs=14000,
        sessions_per_week=5,
        workout_type='ppl',
        avg_intensity=0.78
    )

    nutrition = NutritionPlan(
        daily_calories=2700,
        daily_protein_g=165,
        caloric_surplus=250
    )

    result = predictor.predict(user, workout, nutrition, weeks=8)

    print(f"\n📅 Week-by-Week Progress:")
    print(f"{'Week':<8} {'Weight':<12} {'Muscle':<12} {'Cumulative'}")
    print("-" * 50)

    for week_data in result.weekly_breakdown:
        week = week_data['week']
        muscle = week_data['muscle_gain']
        cumulative = week_data['cumulative_muscle']
        print(f"{week:<8} {user.weight_lbs + cumulative:.1f} lbs    "
              f"+{muscle:.2f} lbs    {cumulative:.2f} lbs")

    print(f"\nFinal Result after 8 weeks:")
    print(f"  Weight: {user.weight_lbs:.0f} → {result.new_weight_lbs:.1f} lbs")
    print(f"  Body Fat: {user.body_fat_pct:.0f}% → {result.new_body_fat_pct:.1f}%")
    print(f"  Muscle Gained: {result.muscle_change_lbs:.1f} lbs")


def demo_compare_workout_types():
    """Compare different workout programs"""
    print("\n" + "=" * 60)
    print("DEMO: Compare Workout Programs")
    print("=" * 60)

    predictor = WorkoutPredictor()

    user = UserState(
        weight_lbs=170,
        body_fat_pct=16,
        smpl_betas=[0.0] * 10,
        height_inches=69,
        age=28,
        gender='male',
        training_years=2
    )

    nutrition = NutritionPlan(
        daily_calories=2600,
        daily_protein_g=155,
        caloric_surplus=200
    )

    workout_types = [
        ('PPL (6-day)', 'ppl', 6, 15000),
        ('Upper/Lower', 'upper_lower', 4, 10000),
        ('Full Body', 'full_body', 3, 8000),
        ('Bro Split', 'bro_split', 5, 12000),
    ]

    print(f"\nComparing workout programs (8 weeks, +200 cal surplus):\n")
    print(f"{'Program':<20} {'Days/Wk':<10} {'Muscle':<12} {'Fat':<12} {'Weight'}")
    print("-" * 65)

    for name, wtype, days, volume in workout_types:
        workout = WorkoutPlan(
            weekly_volume_lbs=volume,
            sessions_per_week=days,
            workout_type=wtype,
            avg_intensity=0.75
        )

        result = predictor.predict(user, workout, nutrition, weeks=8)

        print(f"{name:<20} {days:<10} {result.muscle_change_lbs:+.1f} lbs    "
              f"{result.fat_change_lbs:+.1f} lbs    {result.weight_change_lbs:+.1f} lbs")


def demo_api_response():
    """Show API-style JSON response"""
    print("\n" + "=" * 60)
    print("DEMO: API JSON Response")
    print("=" * 60)

    predictor = WorkoutPredictor()

    user = UserState(
        weight_lbs=180,
        body_fat_pct=15,
        smpl_betas=[0.1, 0.05, 0.0, 0.02, 0.01, 0.03, 0.02, 0.01, 0.0, 0.0],
        height_inches=70,
        age=28,
        gender='male',
        training_years=2
    )

    workout = WorkoutPlan(
        weekly_volume_lbs=12000,
        sessions_per_week=4,
        workout_type='ppl',
        avg_intensity=0.75
    )

    nutrition = NutritionPlan(
        daily_calories=2800,
        daily_protein_g=150,
        caloric_surplus=300
    )

    result = predictor.predict(user, workout, nutrition, weeks=4)

    # Format as API response
    api_response = {
        "prediction": {
            "user_id": "demo_user_123",
            "timeline_weeks": 4,
            "starting_state": {
                "weight_lbs": user.weight_lbs,
                "body_fat_pct": user.body_fat_pct,
                "smpl_betas": user.smpl_betas
            },
            "predicted_changes": {
                "weight_change_lbs": round(result.weight_change_lbs, 2),
                "muscle_change_lbs": round(result.muscle_change_lbs, 2),
                "fat_change_lbs": round(result.fat_change_lbs, 2),
                "new_weight_lbs": round(result.new_weight_lbs, 2),
                "new_body_fat_pct": round(result.new_body_fat_pct, 2),
                "new_smpl_betas": [round(b, 4) for b in result.new_smpl_betas]
            },
            "confidence": round(result.confidence, 2),
            "weekly_breakdown": [
                {
                    "week": w['week'],
                    "muscle_gain": round(w['muscle_gain'], 3),
                    "cumulative_muscle": round(w['cumulative_muscle'], 3)
                }
                for w in result.weekly_breakdown
            ]
        }
    }

    import json
    print(json.dumps(api_response, indent=2))


if __name__ == "__main__":
    # Run all demos
    demo_basic_prediction()
    demo_weight_loss()
    demo_body_recomposition()
    demo_weekly_progression()
    demo_compare_workout_types()
    demo_api_response()

    print("\n" + "=" * 60)
    print("All demos completed!")
    print("=" * 60)
