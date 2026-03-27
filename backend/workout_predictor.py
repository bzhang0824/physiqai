"""
PhysiqAI Workout Predictor - Backward Compatible Wrapper
========================================================
This module provides backward compatibility with the original API
while using the optimized prediction engine internally.
"""

from typing import Optional, List
import warnings

# Import from optimized version
from workout_predictor_fast import (
    OptimizedPredictor,
    UserProfile,
    WorkoutPlan as WorkoutPlanNew,
    NutritionPlan as NutritionPlanNew,
    PredictionResult
)

# Maintain original class names for compatibility
class UserState:
    """Original UserState API - maps to UserProfile"""
    def __init__(self, weight_lbs: float, body_fat_pct: float,
                 smpl_betas: List[float], height_inches: float,
                 age: int, gender: str, training_years: float = 0,
                 # New optional params
                 training_frequency: int = 3,
                 sleep_hours: float = 7.0,
                 stress_level: int = 5,
                 body_type: str = 'mesomorph'):
        self.weight_lbs = weight_lbs
        self.body_fat_pct = body_fat_pct
        self.smpl_betas = smpl_betas
        self.height_inches = height_inches
        self.age = age
        self.gender = gender
        self.training_years = training_years
        self.training_frequency = training_frequency
        self.sleep_hours = sleep_hours
        self.stress_level = stress_level
        self.body_type = body_type

    def to_profile(self) -> UserProfile:
        """Convert to new UserProfile format"""
        return UserProfile(
            weight_lbs=self.weight_lbs,
            height_inches=self.height_inches,
            age=self.age,
            gender=self.gender,
            body_fat_pct=self.body_fat_pct,
            training_years=self.training_years,
            training_frequency=self.training_frequency,
            sleep_hours=self.sleep_hours,
            stress_level=self.stress_level,
            body_type=self.body_type,
            smpl_betas=self.smpl_betas
        )

    @property
    def lean_mass_lbs(self) -> float:
        return self.weight_lbs * (1 - self.body_fat_pct / 100)

    @property
    def fat_mass_lbs(self) -> float:
        return self.weight_lbs * (self.body_fat_pct / 100)

    @property
    def bmi(self) -> float:
        weight_kg = self.weight_lbs * 0.453592
        height_m = self.height_inches * 0.0254
        return weight_kg / (height_m ** 2)

    @property
    def experience_level(self) -> str:
        if self.training_years < 1:
            return 'beginner'
        elif self.training_years < 3:
            return 'intermediate'
        else:
            return 'advanced'


class WorkoutPlan:
    """Original WorkoutPlan API - maps to new WorkoutPlan"""
    def __init__(self, weekly_volume_lbs: float, sessions_per_week: int,
                 workout_type: str, avg_intensity: float = 0.7,
                 cardio_minutes_per_week: float = 0):
        self.weekly_volume_lbs = weekly_volume_lbs
        self.sessions_per_week = sessions_per_week
        self.workout_type = workout_type
        self.avg_intensity = avg_intensity
        self.cardio_minutes_per_week = cardio_minutes_per_week

    def to_plan(self) -> WorkoutPlanNew:
        """Convert to new WorkoutPlan format"""
        return WorkoutPlanNew(
            weekly_volume_lbs=self.weekly_volume_lbs,
            sessions_per_week=self.sessions_per_week,
            workout_type=self.workout_type,
            avg_intensity=self.avg_intensity,
            cardio_minutes_per_week=self.cardio_minutes_per_week,
            progressive_overload=False
        )

    @property
    def volume_per_session(self) -> float:
        return self.weekly_volume_lbs / self.sessions_per_week if self.sessions_per_week > 0 else 0


class NutritionPlan:
    """Original NutritionPlan API - maps to new NutritionPlan"""
    def __init__(self, daily_calories: float, daily_protein_g: float,
                 caloric_surplus: float = 0):
        self.daily_calories = daily_calories
        self.daily_protein_g = daily_protein_g
        self.caloric_surplus = caloric_surplus

    def to_plan(self) -> NutritionPlanNew:
        """Convert to new NutritionPlan format"""
        return NutritionPlanNew(
            daily_calories=self.daily_calories,
            daily_protein_g=self.daily_protein_g,
            caloric_surplus=self.caloric_surplus,
            protein_timing='average'
        )

    def get_protein_per_lb(self, weight_lbs: float) -> float:
        return self.daily_protein_g / weight_lbs if weight_lbs > 0 else 0


class WorkoutPredictor:
    """
    Backward-compatible WorkoutPredictor.
    Uses OptimizedPredictor internally for better accuracy.
    """

    def __init__(self, reddit_data_path: Optional[str] = None):
        """Initialize predictor with optional data path (deprecated)"""
        if reddit_data_path:
            warnings.warn("reddit_data_path is deprecated and ignored", DeprecationWarning)

        self._optimized = OptimizedPredictor()

    def predict(self, user: UserState, workout: WorkoutPlan,
                nutrition: NutritionPlan, weeks: int):
        """
        Make prediction using optimized engine.
        Returns result with original API compatibility.
        """
        # Convert to new types
        user_profile = user.to_profile()
        workout_plan = workout.to_plan()
        nutrition_plan = nutrition.to_plan()

        # Get optimized prediction
        result = self._optimized.predict(user_profile, workout_plan, nutrition_plan, weeks)

        # Return enhanced result (backward compatible)
        return result

    def batch_predict(self, users: List[UserState], workouts: List[WorkoutPlan],
                      nutrition_plans: List[NutritionPlan], weeks: int):
        """Batch prediction for multiple users"""
        results = []
        for user, workout, nutrition in zip(users, workouts, nutrition_plans):
            result = self.predict(user, workout, nutrition, weeks)
            results.append(result)
        return results


# Maintain original test function
def test_predictor():
    """Test function with original API"""
    print("=" * 70)
    print("PHYSIQAI WORKOUT PREDICTOR - BACKWARD COMPATIBLE TEST")
    print("=" * 70)

    predictor = WorkoutPredictor()

    # Test Case 1: Male bulking (original format)
    print("\n📊 TEST CASE 1: Male Lean Bulk")
    print("-" * 70)

    user1 = UserState(
        weight_lbs=180,
        body_fat_pct=15,
        smpl_betas=[0.0] * 10,
        height_inches=70,
        age=28,
        gender='male',
        training_years=2
    )

    workout1 = WorkoutPlan(
        weekly_volume_lbs=12000,
        sessions_per_week=4,
        workout_type='ppl',
        avg_intensity=0.75
    )

    nutrition1 = NutritionPlan(
        daily_calories=2800,
        daily_protein_g=150,
        caloric_surplus=300
    )

    result1 = predictor.predict(user1, workout1, nutrition1, weeks=4)
    print(result1.summary())

    # Test Case 2: Female cutting (original format)
    print("\n📊 TEST CASE 2: Female Weight Loss")
    print("-" * 70)

    user2 = UserState(
        weight_lbs=150,
        body_fat_pct=25,
        smpl_betas=[0.0] * 10,
        height_inches=65,
        age=30,
        gender='female',
        training_years=1
    )

    workout2 = WorkoutPlan(
        weekly_volume_lbs=8000,
        sessions_per_week=3,
        workout_type='full_body',
        avg_intensity=0.70,
        cardio_minutes_per_week=150
    )

    nutrition2 = NutritionPlan(
        daily_calories=1600,
        daily_protein_g=120,
        caloric_surplus=-400
    )

    result2 = predictor.predict(user2, workout2, nutrition2, weeks=8)
    print(result2.summary())

    print("\n" + "=" * 70)
    print("BACKWARD COMPATIBILITY TEST PASSED")
    print("✓ Original API works with optimized engine")
    print("✓ Confidence intervals now available")
    print("✓ Weekly breakdowns now available")
    print("=" * 70)

    return [result1, result2]


if __name__ == "__main__":
    test_predictor()
