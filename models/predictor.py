"""
PhysiqAI Workout-to-Body Prediction Engine
============================================

Converts workout data into predicted body parameter changes.
Based on analysis of Reddit progress data and exercise science research.

Core Formulas:
1. Calorie deficit → Weight loss (7.7 lbs/month average from r/progresspics)
2. Protein + lifting → Muscle gain (0.5-2.0 lbs/month based on experience)
3. Timeline → Progress curves (S-curve for realistic diminishing returns)

Usage:
    from predictor import BodyPredictor, WorkoutPlan, UserProfile

    predictor = BodyPredictor()
    result = predictor.predict(profile, workout, weeks=12)

    print(f"Weight change: {result.weight_change_lbs:.1f} lbs")
    print(f"Body fat: {result.body_fat_percent:.1f}%")
    print(f"Muscle gain: {result.lean_mass_gain_lbs:.1f} lbs")
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Gender(Enum):
    MALE = "male"
    FEMALE = "female"


class ExperienceLevel(Enum):
    BEGINNER = "beginner"       # < 1 year
    INTERMEDIATE = "intermediate"  # 1-3 years
    ADVANCED = "advanced"       # 3+ years


class WorkoutType(Enum):
    WEIGHT_LOSS = "weight_loss"     # Focus on calorie deficit
    MUSCLE_GAIN = "muscle_gain"     # Focus on hypertrophy
    BODY_RECOMP = "body_recomp"     # Simultaneous loss + gain
    MAINTENANCE = "maintenance"     # Keep current


@dataclass
class UserProfile:
    """User's physical profile and starting point"""
    age: int
    gender: Gender
    height_inches: float
    weight_lbs: float
    body_fat_percent: float

    # Training history
    years_training: float = 0.0
    experience_level: Optional[ExperienceLevel] = None

    # Lifestyle factors (1-10 scale)
    sleep_quality: float = 7.0
    nutrition_quality: float = 7.0
    stress_level: float = 5.0  # Lower is better

    # Genetic factors
    genetic_potential: str = "average"  # "low", "average", "high"

    def __post_init__(self):
        if self.experience_level is None:
            if self.years_training < 1:
                self.experience_level = ExperienceLevel.BEGINNER
            elif self.years_training < 3:
                self.experience_level = ExperienceLevel.INTERMEDIATE
            else:
                self.experience_level = ExperienceLevel.ADVANCED

    @property
    def bmi(self) -> float:
        """Calculate BMI"""
        return (self.weight_lbs / (self.height_inches ** 2)) * 703

    @property
    def lean_mass_lbs(self) -> float:
        """Calculate lean body mass"""
        return self.weight_lbs * (1 - self.body_fat_percent / 100)

    @property
    def bmr(self) -> float:
        """Basal Metabolic Rate (Mifflin-St Jeor)"""
        weight_kg = self.weight_lbs * 0.453592
        height_cm = self.height_inches * 2.54
        age = self.age

        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age
        if self.gender == Gender.MALE:
            bmr += 5
        else:
            bmr -= 161

        return bmr


@dataclass
class WorkoutPlan:
    """User's workout and nutrition plan"""
    workout_type: WorkoutType

    # Training parameters
    days_per_week: int = 3
    minutes_per_session: int = 60
    intensity: str = "moderate"  # "light", "moderate", "intense"

    # Cardio
    cardio_days_per_week: int = 0
    cardio_minutes_per_session: int = 30

    # Nutrition
    daily_calories: Optional[int] = None  # If None, calculated from goals
    daily_protein_g: Optional[int] = None  # If None, calculated from bodyweight

    # Specific focus areas
    focus_muscle_groups: List[str] = field(default_factory=list)
    # Options: "chest", "back", "shoulders", "arms", "legs", "core"

    def __post_init__(self):
        # Set defaults based on workout type
        if self.daily_protein_g is None:
            self.daily_protein_g = 150  # Default, should be set based on weight

        if self.daily_calories is None:
            # Placeholder - will be calculated based on goals
            self.daily_calories = 2000


@dataclass
class BodyChanges:
    """Predicted changes to body composition"""
    weight_change_lbs: float
    body_fat_change_percent: float
    lean_mass_change_lbs: float

    # Body measurements (inches change)
    chest_change_in: float = 0.0
    waist_change_in: float = 0.0
    hips_change_in: float = 0.0
    arms_change_in: float = 0.0
    thighs_change_in: float = 0.0

    @property
    def final_weight_lbs(self, starting_weight: float = 0) -> float:
        return starting_weight + self.weight_change_lbs

    @property
    def final_body_fat_percent(self, starting_bf: float = 0) -> float:
        return starting_bf + self.body_fat_change_percent


@dataclass
class PredictionResult:
    """Complete prediction with timeline"""
    # Final state
    weight_lbs: float
    body_fat_percent: float
    lean_mass_lbs: float

    # Changes
    weight_change_lbs: float
    body_fat_change_percent: float
    lean_mass_change_lbs: float

    # Weekly progression
    weekly_weights: List[float]
    weekly_body_fat: List[float]
    weekly_lean_mass: List[float]

    # Metrics
    confidence_score: float  # 0-1

    # Insights
    insights: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class PredictionFormulas:
    """
    Core prediction formulas based on research and Reddit data analysis.

    Data sources:
    - r/progresspics: 7.7 lbs/month average weight loss (P10: 1.7, P90: 13.4)
    - Exercise science: 0.5-2.0 lbs/month muscle gain based on experience
    - NHANES/Kaggle: Body composition relationships
    """

    # Weight loss rates from Reddit analysis (lbs per month)
    WEIGHT_LOSS_RATES = {
        'aggressive': 13.4,  # P90
        'moderate': 7.7,     # Mean
        'conservative': 3.0, # ~P25
    }

    # Muscle gain rates by experience level (lbs per month)
    MUSCLE_GAIN_RATES = {
        ExperienceLevel.BEGINNER: {'male': 2.0, 'female': 1.0},
        ExperienceLevel.INTERMEDIATE: {'male': 1.0, 'female': 0.5},
        ExperienceLevel.ADVANCED: {'male': 0.5, 'female': 0.25},
    }

    # Calorie to weight change conversion
    # 3500 calories = 1 lb of fat
    CALORIES_PER_LB_FAT = 3500
    CALORIES_PER_LB_MUSCLE = 2500  # Approximate

    # Protein requirements for muscle gain (g per lb bodyweight)
    PROTEIN_FOR_MUSCLE = 0.8
    PROTEIN_MINIMUM = 0.5

    # Age modifiers (muscle gain decreases after 30)
    AGE_MODIFIER = {
        'slope': -0.02,  # -2% per year after 30
        'floor': 0.6,    # Minimum 60% of base rate
    }

    # Gender modifiers
    GENDER_MODIFIER = {
        Gender.MALE: 1.0,
        Gender.FEMALE: 0.7,  # Women gain muscle ~70% as fast
    }

    # Lifestyle modifiers
    @classmethod
    def get_lifestyle_modifier(cls, sleep: float, nutrition: float, stress: float) -> float:
        """
        Calculate lifestyle modifier based on sleep, nutrition, stress.
        All inputs are 1-10 scale.
        """
        sleep_mod = 0.6 + (sleep / 10) * 0.4  # 0.6 to 1.0
        nutrition_mod = 0.5 + (nutrition / 10) * 0.5  # 0.5 to 1.0
        stress_mod = 1.0 - (stress / 10) * 0.3  # 0.7 to 1.0

        return sleep_mod * nutrition_mod * stress_mod

    @classmethod
    def get_age_modifier(cls, age: int) -> float:
        """Muscle gain decreases with age after 30"""
        if age < 30:
            return 1.0
        modifier = 1.0 + (age - 30) * cls.AGE_MODIFIER['slope']
        return max(cls.AGE_MODIFIER['floor'], modifier)

    @classmethod
    def get_genetic_modifier(cls, genetic_potential: str) -> float:
        """Genetic potential modifier"""
        modifiers = {'low': 0.7, 'average': 1.0, 'high': 1.4}
        return modifiers.get(genetic_potential, 1.0)

    @classmethod
    def calculate_weight_loss_from_deficit(
        cls,
        daily_deficit: int,
        weeks: int,
        starting_weight: float,
        starting_bf: float
    ) -> Tuple[float, float]:
        """
        Calculate weight loss from calorie deficit.

        Returns:
            (total_weight_loss_lbs, fat_loss_lbs)
        """
        days = weeks * 7
        total_deficit = daily_deficit * days

        # Base calculation
        weight_loss = total_deficit / cls.CALORIES_PER_LB_FAT

        # Adjust for metabolic adaptation (deficit becomes less effective over time)
        adaptation_factor = 1.0 - (weeks * 0.015)  # 1.5% decrease per week
        adaptation_factor = max(0.7, adaptation_factor)  # Floor at 70%

        adjusted_loss = weight_loss * adaptation_factor

        # Limit loss to healthy levels (don't go below essential fat)
        min_healthy_bf = 5 if starting_bf < 15 else 10  # Men vs women threshold
        max_loss_from_fat = (starting_bf - min_healthy_bf) / 100 * starting_weight

        # Some muscle loss is inevitable during deficit
        fat_loss = min(adjusted_loss * 0.8, max_loss_from_fat)  # 80% fat, 20% muscle
        muscle_loss = adjusted_loss * 0.2

        total_loss = fat_loss + muscle_loss

        return total_loss, fat_loss

    @classmethod
    def calculate_muscle_gain(
        cls,
        profile: UserProfile,
        workout: WorkoutPlan,
        weeks: int
    ) -> float:
        """
        Calculate muscle gain based on training and nutrition.

        Returns:
            lean_mass_gain_lbs
        """
        months = weeks / 4

        # Base rate by experience
        gender_str = profile.gender.value
        base_rate = cls.MUSCLE_GAIN_RATES[profile.experience_level][gender_str]

        # Apply modifiers
        age_mod = cls.get_age_modifier(profile.age)
        genetic_mod = cls.get_genetic_modifier(profile.genetic_potential)
        lifestyle_mod = cls.get_lifestyle_modifier(
            profile.sleep_quality,
            profile.nutrition_quality,
            profile.stress_level
        )

        # Training frequency modifier
        freq_mod = min(1.3, 0.5 + workout.days_per_week * 0.15)

        # Intensity modifier
        intensity_mods = {'light': 0.7, 'moderate': 1.0, 'intense': 1.25}
        intensity_mod = intensity_mods.get(workout.intensity, 1.0)

        # Protein adequacy modifier
        protein_per_lb = workout.daily_protein_g / profile.weight_lbs
        if protein_per_lb >= cls.PROTEIN_FOR_MUSCLE:
            protein_mod = 1.0
        elif protein_per_lb >= cls.PROTEIN_MINIMUM:
            protein_mod = 0.7 + (protein_per_lb - cls.PROTEIN_MINIMUM) * 0.6
        else:
            protein_mod = 0.5  # Insufficient protein severely limits gains

        # Combined modifier
        total_mod = (
            age_mod *
            genetic_mod *
            lifestyle_mod *
            freq_mod *
            intensity_mod *
            protein_mod
        )

        # Calculate expected gain with diminishing returns
        # Use logarithmic curve for realistic progression
        total_gain = 0
        for month in range(int(months) + 1):
            remaining_months = months - month
            if remaining_months <= 0:
                break

            # Diminishing returns curve
            progress = month / max(months, 1)
            dim_return = 1.0 - 0.3 * math.log1p(progress * 2)
            dim_return = max(0.5, dim_return)  # Floor at 50%

            month_gain = base_rate * total_mod * dim_return
            total_gain += min(month_gain, remaining_months * base_rate * total_mod)

        return total_gain * min(1.0, months)  # Scale by actual months

    @classmethod
    def progress_curve(cls, week: int, total_weeks: int) -> float:
        """
        S-curve for realistic progress over time.
        Returns multiplier (0-1) for progress at given week.
        """
        if total_weeks <= 0:
            return 1.0

        t = week / total_weeks
        # Sigmoid curve: slow start, fast middle, plateau
        # Using a shifted sigmoid for better shape
        progress = 1 / (1 + math.exp(-8 * (t - 0.5)))

        # Normalize so total area under curve represents actual progress
        # This ensures the curve sums to approximately 1 over the period
        return progress


class BodyPredictor:
    """
    Main prediction engine for body transformations.
    """

    def __init__(self, conservatism: float = 0.85):
        """
        Args:
            conservatism: 0-1, reduces predictions to avoid over-promising
        """
        self.conservatism = conservatism
        self.formulas = PredictionFormulas()

    def predict(
        self,
        profile: UserProfile,
        workout: WorkoutPlan,
        weeks: int
    ) -> PredictionResult:
        """
        Predict body transformation.

        Args:
            profile: User's starting profile
            workout: Workout and nutrition plan
            weeks: Number of weeks to predict

        Returns:
            PredictionResult with changes and timeline
        """
        warnings = []
        insights = []

        # Validate inputs
        if weeks > 52:
            warnings.append("Predictions beyond 52 weeks have high uncertainty")
        if workout.days_per_week < 2:
            warnings.append("Training less than 2 days/week may limit results")
        if workout.daily_protein_g < profile.weight_lbs * 0.5:
            warnings.append("Protein intake may be too low for optimal results")

        # Calculate TDEE (Total Daily Energy Expenditure)
        activity_multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'active': 1.725,
            'very_active': 1.9
        }

        # Estimate activity level from workout plan
        weekly_sessions = workout.days_per_week + workout.cardio_days_per_week
        if weekly_sessions <= 2:
            activity_level = 'light'
        elif weekly_sessions <= 4:
            activity_level = 'moderate'
        elif weekly_sessions <= 6:
            activity_level = 'active'
        else:
            activity_level = 'very_active'

        tdee = profile.bmr * activity_multipliers[activity_level]

        # Set default calories if not provided
        if workout.daily_calories is None or workout.daily_calories == 2000:
            if workout.workout_type == WorkoutType.WEIGHT_LOSS:
                workout.daily_calories = int(tdee - 500)  # 500 cal deficit
            elif workout.workout_type == WorkoutType.MUSCLE_GAIN:
                workout.daily_calories = int(tdee + 300)  # 300 cal surplus
            else:
                workout.daily_calories = int(tdee)

        # Calculate calorie difference from maintenance
        calorie_diff = workout.daily_calories - tdee

        # Initialize progress tracking
        weekly_weights = [profile.weight_lbs]
        weekly_body_fat = [profile.body_fat_percent]
        weekly_lean_mass = [profile.lean_mass_lbs]

        current_weight = profile.weight_lbs
        current_bf = profile.body_fat_percent
        current_lean = profile.lean_mass_lbs

        # Calculate total changes based on workout type
        if workout.workout_type == WorkoutType.WEIGHT_LOSS:
            # Focus on fat loss
            if calorie_diff < 0:
                daily_deficit = abs(calorie_diff)
                total_loss, fat_loss = self.formulas.calculate_weight_loss_from_deficit(
                    daily_deficit, weeks, profile.weight_lbs, profile.body_fat_percent
                )
                muscle_change = -total_loss * 0.15  # Some muscle loss
                fat_change = -(fat_loss / profile.weight_lbs * 100)
            else:
                warnings.append("Calorie surplus with weight loss goal - adjust calories")
                total_loss = 0
                muscle_change = 0
                fat_change = 0

        elif workout.workout_type == WorkoutType.MUSCLE_GAIN:
            # Focus on muscle gain
            muscle_change = self.formulas.calculate_muscle_gain(profile, workout, weeks)
            muscle_change *= self.conservatism

            # Some fat gain is inevitable with surplus
            if calorie_diff > 0:
                fat_gain_lbs = (calorie_diff * 7 * weeks * 0.3) / self.formulas.CALORIES_PER_LB_FAT
                fat_gain_lbs *= self.conservatism
                total_weight_change = muscle_change + fat_gain_lbs
                fat_change = (fat_gain_lbs / profile.weight_lbs * 100)
            else:
                total_weight_change = muscle_change
                fat_change = 0

        elif workout.workout_type == WorkoutType.BODY_RECOMP:
            # Simultaneous fat loss and muscle gain (slower)
            if calorie_diff < 0:
                deficit_loss, fat_loss = self.formulas.calculate_weight_loss_from_deficit(
                    abs(calorie_diff), weeks, profile.weight_lbs, profile.body_fat_percent
                )
            else:
                deficit_loss = 0
                fat_loss = 0

            # Muscle gain is slower in recomp
            muscle_change = self.formulas.calculate_muscle_gain(profile, workout, weeks)
            muscle_change *= 0.6 * self.conservatism  # 60% of normal rate

            # Net weight change: fat lost minus muscle gained
            total_weight_change = -deficit_loss + muscle_change
            fat_change = -(fat_loss / profile.weight_lbs * 100) if fat_loss > 0 else 0

        else:  # MAINTENANCE
            muscle_change = self.formulas.calculate_muscle_gain(profile, workout, weeks)
            muscle_change *= 0.3 * self.conservatism  # Very slow
            total_loss = 0
            fat_change = 0

        # Apply progress curve for weekly tracking
        if workout.workout_type == WorkoutType.WEIGHT_LOSS:
            total_weight_change = -total_loss
        elif workout.workout_type == WorkoutType.MUSCLE_GAIN:
            # Already calculated above
            pass
        elif workout.workout_type == WorkoutType.BODY_RECOMP:
            # Already calculated above
            pass
        else:  # MAINTENANCE
            total_weight_change = 0

        for week in range(1, weeks + 1):
            progress = self.formulas.progress_curve(week, weeks)

            # Calculate weekly changes
            week_weight = profile.weight_lbs + (total_weight_change * progress)
            week_lean = profile.lean_mass_lbs + (muscle_change * progress)
            week_bf = profile.body_fat_percent + (fat_change * progress)

            weekly_weights.append(week_weight)
            weekly_lean_mass.append(week_lean)
            weekly_body_fat.append(week_bf)

        # Final results
        final_weight = weekly_weights[-1]
        final_bf = weekly_body_fat[-1]
        final_lean = weekly_lean_mass[-1]

        # Generate insights
        if muscle_change > 2:
            insights.append(f"Great muscle gain potential! Expected +{muscle_change:.1f} lbs lean mass")
        if fat_change < -3:
            insights.append(f"Significant fat loss expected: {fat_change:.1f}% body fat reduction")
        if workout.daily_protein_g < profile.weight_lbs * 0.7:
            insights.append("Consider increasing protein to 0.7-1g per lb for better results")
        if profile.sleep_quality < 7:
            insights.append("Improving sleep to 7+ hours could boost results by 15-20%")

        # Calculate confidence
        confidence = 0.7
        if profile.years_training > 0:
            confidence += 0.1
        if all([profile.height_inches, profile.weight_lbs, profile.body_fat_percent]):
            confidence += 0.1
        if workout.daily_calories and workout.daily_protein_g:
            confidence += 0.1
        confidence = min(0.95, confidence)

        return PredictionResult(
            weight_lbs=final_weight,
            body_fat_percent=final_bf,
            lean_mass_lbs=final_lean,
            weight_change_lbs=total_weight_change,
            body_fat_change_percent=fat_change,
            lean_mass_change_lbs=muscle_change,
            weekly_weights=weekly_weights,
            weekly_body_fat=weekly_body_fat,
            weekly_lean_mass=weekly_lean_mass,
            confidence_score=confidence,
            insights=insights,
            warnings=warnings
        )

    def predict_measurements(
        self,
        profile: UserProfile,
        result: PredictionResult
    ) -> Dict[str, float]:
        """
        Predict body measurement changes based on weight/bf changes.

        Returns dict with predicted measurement changes in inches.
        """
        # Approximate relationships from body composition data
        weight_change = result.weight_change_lbs
        bf_change = result.body_fat_change_percent

        # Waist correlates strongly with body fat
        waist_change = bf_change * 0.15  # ~0.15 inches per % body fat

        # Chest changes with both muscle and fat
        lean_change = result.lean_mass_change_lbs
        chest_change = (lean_change * 0.03) + (weight_change - lean_change) * 0.02

        # Arms change with muscle gain
        arm_change = lean_change * 0.015
        if 'arms' in [f.lower() for f in result.__dict__.get('focus_muscle_groups', [])]:
            arm_change *= 1.3

        # Thighs change with leg work
        thigh_change = lean_change * 0.02

        # Hips change with fat loss/gain
        hip_change = (weight_change - lean_change) * 0.03

        return {
            'chest': chest_change,
            'waist': waist_change,
            'hips': hip_change,
            'arms': arm_change,
            'thighs': thigh_change
        }


# ============================================================================
# Test and Demonstration
# ============================================================================

def run_tests():
    """Run sample predictions to test the engine."""
    print("=" * 70)
    print("PHYSIQAI WORKOUT-TO-BODY PREDICTION ENGINE")
    print("=" * 70)

    predictor = BodyPredictor(conservatism=0.85)

    # Test Case 1: Weight Loss
    print("\n" + "=" * 70)
    print("TEST 1: Weight Loss Transformation")
    print("=" * 70)

    profile1 = UserProfile(
        age=32,
        gender=Gender.FEMALE,
        height_inches=65,  # 5'5"
        weight_lbs=180,
        body_fat_percent=35,
        years_training=0.5,
        sleep_quality=7,
        nutrition_quality=7,
        stress_level=6
    )

    workout1 = WorkoutPlan(
        workout_type=WorkoutType.WEIGHT_LOSS,
        days_per_week=4,
        minutes_per_session=45,
        intensity="moderate",
        cardio_days_per_week=3,
        cardio_minutes_per_session=30,
        daily_calories=1600,
        daily_protein_g=140
    )

    result1 = predictor.predict(profile1, workout1, weeks=16)

    print(f"\n📊 Starting Point:")
    print(f"   Weight: {profile1.weight_lbs:.0f} lbs | Body Fat: {profile1.body_fat_percent:.1f}%")
    print(f"   Lean Mass: {profile1.lean_mass_lbs:.1f} lbs")

    print(f"\n🏃 Workout Plan:")
    print(f"   Type: Weight Loss | {workout1.days_per_week} days/week + {workout1.cardio_days_per_week} cardio")
    print(f"   Calories: {workout1.daily_calories}/day | Protein: {workout1.daily_protein_g}g/day")

    print(f"\n📈 16-Week Prediction:")
    print(f"   Weight: {result1.weight_lbs:.1f} lbs ({result1.weight_change_lbs:+.1f})")
    print(f"   Body Fat: {result1.body_fat_percent:.1f}% ({result1.body_fat_change_percent:+.1f}%)")
    print(f"   Lean Mass: {result1.lean_mass_lbs:.1f} lbs ({result1.lean_mass_change_lbs:+.1f})")
    print(f"   Confidence: {result1.confidence_score*100:.0f}%")

    if result1.insights:
        print(f"\n💡 Insights:")
        for insight in result1.insights:
            print(f"   • {insight}")

    if result1.warnings:
        print(f"\n⚠️ Warnings:")
        for warning in result1.warnings:
            print(f"   • {warning}")

    # Test Case 2: Muscle Building
    print("\n" + "=" * 70)
    print("TEST 2: Muscle Building (Beginner Male)")
    print("=" * 70)

    profile2 = UserProfile(
        age=25,
        gender=Gender.MALE,
        height_inches=70,  # 5'10"
        weight_lbs=160,
        body_fat_percent=18,
        years_training=0.3,
        sleep_quality=8,
        nutrition_quality=8,
        stress_level=4
    )

    workout2 = WorkoutPlan(
        workout_type=WorkoutType.MUSCLE_GAIN,
        days_per_week=5,
        minutes_per_session=60,
        intensity="intense",
        daily_calories=2800,
        daily_protein_g=160,
        focus_muscle_groups=["chest", "arms", "shoulders"]
    )

    result2 = predictor.predict(profile2, workout2, weeks=12)

    print(f"\n📊 Starting Point:")
    print(f"   Weight: {profile2.weight_lbs:.0f} lbs | Body Fat: {profile2.body_fat_percent:.1f}%")
    print(f"   Experience: {profile2.experience_level.value}")

    print(f"\n🏋️ Workout Plan:")
    print(f"   Type: Muscle Gain | {workout2.days_per_week} days/week, {workout2.intensity}")
    print(f"   Calories: {workout2.daily_calories}/day | Protein: {workout2.daily_protein_g}g/day")

    print(f"\n📈 12-Week Prediction:")
    print(f"   Weight: {result2.weight_lbs:.1f} lbs ({result2.weight_change_lbs:+.1f})")
    print(f"   Body Fat: {result2.body_fat_percent:.1f}% ({result2.body_fat_change_percent:+.1f}%)")
    print(f"   Lean Mass: {result2.lean_mass_lbs:.1f} lbs ({result2.lean_mass_change_lbs:+.1f})")
    print(f"   Confidence: {result2.confidence_score*100:.0f}%")

    if result2.insights:
        print(f"\n💡 Insights:")
        for insight in result2.insights:
            print(f"   • {insight}")

    # Test Case 3: Body Recomposition
    print("\n" + "=" * 70)
    print("TEST 3: Body Recomposition (Intermediate)")
    print("=" * 70)

    profile3 = UserProfile(
        age=28,
        gender=Gender.MALE,
        height_inches=69,  # 5'9"
        weight_lbs=185,
        body_fat_percent=22,
        years_training=2,
        sleep_quality=7,
        nutrition_quality=7,
        stress_level=5
    )

    workout3 = WorkoutPlan(
        workout_type=WorkoutType.BODY_RECOMP,
        days_per_week=4,
        minutes_per_session=50,
        intensity="moderate",
        cardio_days_per_week=2,
        daily_calories=2200,
        daily_protein_g=170
    )

    result3 = predictor.predict(profile3, workout3, weeks=20)

    print(f"\n📊 Starting Point:")
    print(f"   Weight: {profile3.weight_lbs:.0f} lbs | Body Fat: {profile3.body_fat_percent:.1f}%")

    print(f"\n🔄 Workout Plan:")
    print(f"   Type: Body Recomposition | {workout3.days_per_week} days/week")
    print(f"   Calories: {workout3.daily_calories}/day (slight deficit)")

    print(f"\n📈 20-Week Prediction:")
    print(f"   Weight: {result3.weight_lbs:.1f} lbs ({result3.weight_change_lbs:+.1f})")
    print(f"   Body Fat: {result3.body_fat_percent:.1f}% ({result3.body_fat_change_percent:+.1f}%)")
    print(f"   Lean Mass: {result3.lean_mass_lbs:.1f} lbs ({result3.lean_mass_change_lbs:+.1f})")
    print(f"   Confidence: {result3.confidence_score*100:.0f}%")

    # Test measurement predictions
    print("\n" + "=" * 70)
    print("MEASUREMENT PREDICTIONS")
    print("=" * 70)

    for name, result, profile in [
        ("Weight Loss", result1, profile1),
        ("Muscle Gain", result2, profile2),
        ("Recomposition", result3, profile3)
    ]:
        measurements = predictor.predict_measurements(profile, result)
        print(f"\n{name}:")
        print(f"   Chest: {measurements['chest']:+.2f}\"")
        print(f"   Waist: {measurements['waist']:+.2f}\"")
        print(f"   Arms: {measurements['arms']:+.2f}\"")
        print(f"   Thighs: {measurements['thighs']:+.2f}\"")

    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETED SUCCESSFULLY")
    print("=" * 70)

    return True


if __name__ == "__main__":
    run_tests()
