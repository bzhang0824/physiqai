#!/usr/bin/env python3
"""
Sample usage of the PhysiqAI Prediction Engine.
Demonstrates various use cases with realistic workout data.
"""

import sys
sys.path.insert(0, '/home/clawd/.openclaw/workspace/projects/physiqai')

from models.predictor import (
    BodyPredictor, UserProfile, WorkoutPlan,
    Gender, WorkoutType, ExperienceLevel
)


def sample_1_new_year_resolution():
    """New Year weight loss goal - female, 30s, busy schedule"""
    print("\n" + "=" * 70)
    print("SAMPLE 1: New Year Resolution - Weight Loss")
    print("=" * 70)

    profile = UserProfile(
        age=34,
        gender=Gender.FEMALE,
        height_inches=65,  # 5'5"
        weight_lbs=175,
        body_fat_percent=38,
        years_training=0,
        sleep_quality=6,
        nutrition_quality=6,
        stress_level=7
    )

    # Realistic busy schedule plan
    workout = WorkoutPlan(
        workout_type=WorkoutType.WEIGHT_LOSS,
        days_per_week=3,
        minutes_per_session=45,
        intensity="moderate",
        cardio_days_per_week=2,
        cardio_minutes_per_session=30,
        daily_calories=1500,
        daily_protein_g=130
    )

    predictor = BodyPredictor(conservatism=0.80)
    result = predictor.predict(profile, workout, weeks=16)

    print(f"\n👤 Profile: {profile.age}yo female, {profile.weight_lbs} lbs, {profile.body_fat_percent}% BF")
    print(f"🏃 Plan: {workout.days_per_week}x weights + {workout.cardio_days_per_week}x cardio, {workout.daily_calories} cal/day")

    print(f"\n📊 16-Week Results:")
    print(f"   Weight: {result.weight_lbs:.1f} lbs ({result.weight_change_lbs:+.1f})")
    print(f"   Body Fat: {result.body_fat_percent:.1f}% ({result.body_fat_change_percent:+.1f}%)")
    print(f"   Lean Mass: {result.lean_mass_lbs:.1f} lbs ({result.lean_mass_change_lbs:+.1f})")
    print(f"   Confidence: {result.confidence_score*100:.0f}%")

    print(f"\n📈 Progression:")
    milestones = [4, 8, 12, 16]
    for week in milestones:
        print(f"   Week {week}: {result.weekly_weights[week]:.1f} lbs ({result.weekly_body_fat[week]:.1f}% BF)")

    if result.insights:
        print(f"\n💡 Insights:")
        for i in result.insights:
            print(f"   • {i}")


def sample_2_summer_shred():
    """Summer cut - male, intermediate lifter"""
    print("\n" + "=" * 70)
    print("SAMPLE 2: Summer Shred - 12 Week Cut")
    print("=" * 70)

    profile = UserProfile(
        age=26,
        gender=Gender.MALE,
        height_inches=71,  # 5'11"
        weight_lbs=195,
        body_fat_percent=22,
        years_training=3,
        sleep_quality=7,
        nutrition_quality=8,
        stress_level=5
    )

    # Aggressive but sustainable cut
    workout = WorkoutPlan(
        workout_type=WorkoutType.WEIGHT_LOSS,
        days_per_week=5,
        minutes_per_session=60,
        intensity="intense",
        cardio_days_per_week=3,
        cardio_minutes_per_session=25,
        daily_calories=2000,
        daily_protein_g=190  # High protein to preserve muscle
    )

    predictor = BodyPredictor(conservatism=0.85)
    result = predictor.predict(profile, workout, weeks=12)

    print(f"\n👤 Profile: {profile.age}yo male, {profile.weight_lbs} lbs, {profile.body_fat_percent}% BF")
    print(f"   Experience: {profile.experience_level.value}")
    print(f"🏋️ Plan: {workout.days_per_week}x lifting + {workout.cardio_days_per_week}x cardio")
    print(f"   {workout.daily_calories} cal/day, {workout.daily_protein_g}g protein")

    print(f"\n📊 12-Week Results:")
    print(f"   Weight: {result.weight_lbs:.1f} lbs ({result.weight_change_lbs:+.1f})")
    print(f"   Body Fat: {result.body_fat_percent:.1f}% ({result.body_fat_change_percent:+.1f}%)")
    print(f"   Lean Mass: {result.lean_mass_lbs:.1f} lbs ({result.lean_mass_change_lbs:+.1f})")
    print(f"   Confidence: {result.confidence_score*100:.0f}%")

    # Measurements
    measurements = predictor.predict_measurements(profile, result)
    print(f"\n📏 Measurement Changes:")
    print(f"   Chest: {measurements['chest']:+.2f}\"")
    print(f"   Waist: {measurements['waist']:+.2f}\"")
    print(f"   Arms: {measurements['arms']:+.2f}\"")


def sample_3_bulk_season():
    """Winter bulk - beginner male trying to gain size"""
    print("\n" + "=" * 70)
    print("SAMPLE 3: Bulk Season - First Proper Bulk")
    print("=" * 70)

    profile = UserProfile(
        age=22,
        gender=Gender.MALE,
        height_inches=69,  # 5'9"
        weight_lbs=155,
        body_fat_percent=15,
        years_training=0.5,
        sleep_quality=8,
        nutrition_quality=7,
        stress_level=4,
        genetic_potential="average"
    )

    # Clean bulk plan
    workout = WorkoutPlan(
        workout_type=WorkoutType.MUSCLE_GAIN,
        days_per_week=4,
        minutes_per_session=75,
        intensity="moderate",
        cardio_days_per_week=1,
        daily_calories=2800,
        daily_protein_g=160,
        focus_muscle_groups=["chest", "back", "shoulders"]
    )

    predictor = BodyPredictor(conservatism=0.85)
    result = predictor.predict(profile, workout, weeks=20)

    print(f"\n👤 Profile: {profile.age}yo male beginner, {profile.weight_lbs} lbs, {profile.body_fat_percent}% BF")
    print(f"🏋️ Plan: {workout.days_per_week}x/week, {workout.daily_calories} cal/day bulk")

    print(f"\n📊 20-Week Results:")
    print(f"   Weight: {result.weight_lbs:.1f} lbs ({result.weight_change_lbs:+.1f})")
    print(f"   Body Fat: {result.body_fat_percent:.1f}% ({result.body_fat_change_percent:+.1f}%)")
    print(f"   Lean Mass: {result.lean_mass_lbs:.1f} lbs ({result.lean_mass_change_lbs:+.1f})")

    # Calculate muscle vs fat ratio
    fat_gained = (result.weight_change_lbs - result.lean_mass_change_lbs)
    muscle_ratio = result.lean_mass_change_lbs / result.weight_change_lbs * 100

    print(f"\n📊 Composition of Weight Gain:")
    print(f"   Muscle: {result.lean_mass_change_lbs:.1f} lbs ({muscle_ratio:.0f}%)")
    print(f"   Fat: {fat_gained:.1f} lbs ({100-muscle_ratio:.0f}%)")


def sample_4_recomp():
    """Body recomposition - skinny fat beginner"""
    print("\n" + "=" * 70)
    print("SAMPLE 4: Body Recomposition - Skinny Fat Fix")
    print("=" * 70)

    profile = UserProfile(
        age=25,
        gender=Gender.MALE,
        height_inches=70,  # 5'10"
        weight_lbs=170,
        body_fat_percent=25,  # Skinny fat - normal weight but higher bf%
        years_training=0.2,
        sleep_quality=7,
        nutrition_quality=6,
        stress_level=6
    )

    # Recomp plan - slight deficit with high protein
    workout = WorkoutPlan(
        workout_type=WorkoutType.BODY_RECOMP,
        days_per_week=3,
        minutes_per_session=60,
        intensity="moderate",
        daily_calories=2100,  # Slight deficit
        daily_protein_g=170   # High protein
    )

    predictor = BodyPredictor(conservatism=0.85)
    result = predictor.predict(profile, workout, weeks=24)

    print(f"\n👤 Profile: {profile.age}yo male, {profile.weight_lbs} lbs, {profile.body_fat_percent}% BF")
    print(f"   Starting point: 'Skinny fat' - normal weight but soft")
    print(f"🔄 Plan: Recomp - {workout.daily_calories} cal, {workout.daily_protein_g}g protein")

    print(f"\n📊 24-Week Results:")
    print(f"   Weight: {result.weight_lbs:.1f} lbs ({result.weight_change_lbs:+.1f})")
    print(f"   Body Fat: {result.body_fat_percent:.1f}% ({result.body_fat_change_percent:+.1f}%)")
    print(f"   Lean Mass: {result.lean_mass_lbs:.1f} lbs ({result.lean_mass_change_lbs:+.1f})")

    print(f"\n📈 Progression:")
    for week in [6, 12, 18, 24]:
        print(f"   Week {week}: {result.weekly_weights[week]:.1f} lbs, {result.weekly_body_fat[week]:.1f}% BF")


def sample_5_advanced_athlete():
    """Advanced athlete maintaining during competition prep"""
    print("\n" + "=" * 70)
    print("SAMPLE 5: Advanced Athlete - Maintenance Phase")
    print("=" * 70)

    profile = UserProfile(
        age=29,
        gender=Gender.FEMALE,
        height_inches=67,  # 5'7"
        weight_lbs=145,
        body_fat_percent=18,
        years_training=5,
        sleep_quality=8,
        nutrition_quality=9,
        stress_level=4,
        genetic_potential="high"
    )

    # Maintenance with slight improvements
    workout = WorkoutPlan(
        workout_type=WorkoutType.MAINTENANCE,
        days_per_week=5,
        minutes_per_session=75,
        intensity="intense",
        daily_calories=2250,  # Around maintenance
        daily_protein_g=145
    )

    predictor = BodyPredictor(conservatism=0.85)
    result = predictor.predict(profile, workout, weeks=12)

    print(f"\n👤 Profile: {profile.age}yo female athlete, {profile.years_training} years training")
    print(f"   Current: {profile.weight_lbs} lbs, {profile.body_fat_percent}% BF")
    print(f"⚖️ Plan: Maintenance at {workout.daily_calories} cal/day")

    print(f"\n📊 12-Week Results:")
    print(f"   Weight: {result.weight_lbs:.1f} lbs ({result.weight_change_lbs:+.1f})")
    print(f"   Body Fat: {result.body_fat_percent:.1f}%")
    print(f"   Lean Mass: {result.lean_mass_lbs:.1f} lbs ({result.lean_mass_change_lbs:+.1f})")

    if result.insights:
        print(f"\n💡 Insights:")
        for i in result.insights:
            print(f"   • {i}")


def compare_conservatism():
    """Show how conservatism setting affects predictions"""
    print("\n" + "=" * 70)
    print("COMPARISON: Prediction Optimism Levels")
    print("=" * 70)

    profile = UserProfile(
        age=28,
        gender=Gender.MALE,
        height_inches=70,
        weight_lbs=180,
        body_fat_percent=22,
        years_training=1,
        sleep_quality=7,
        nutrition_quality=7,
        stress_level=5
    )

    workout = WorkoutPlan(
        workout_type=WorkoutType.MUSCLE_GAIN,
        days_per_week=4,
        intensity="moderate",
        daily_calories=2700,
        daily_protein_g=160
    )

    print(f"\n👤 Same profile & workout, different optimism settings:")
    print(f"   28yo male, 4x/week, 12 weeks")

    for conservatism in [0.70, 0.85, 0.95]:
        predictor = BodyPredictor(conservatism=conservatism)
        result = predictor.predict(profile, workout, weeks=12)

        label = {0.70: "Very Conservative", 0.85: "Realistic", 0.95: "Optimistic"}[conservatism]
        print(f"\n{label} ({conservatism*100:.0f}%):")
        print(f"   Weight: {result.weight_lbs:.1f} lbs ({result.weight_change_lbs:+.1f})")
        print(f"   Lean Mass: +{result.lean_mass_change_lbs:.1f} lbs")


if __name__ == "__main__":
    print("=" * 70)
    print("PHYSIQAI PREDICTION ENGINE - SAMPLE USE CASES")
    print("=" * 70)

    sample_1_new_year_resolution()
    sample_2_summer_shred()
    sample_3_bulk_season()
    sample_4_recomp()
    sample_5_advanced_athlete()
    compare_conservatism()

    print("\n" + "=" * 70)
    print("ALL SAMPLES COMPLETED")
    print("=" * 70)
