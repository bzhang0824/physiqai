"""
PhysiqAI SMPL-Based Transformation Predictor
=============================================
Predicts body shape changes using SMPL parameters based on workout inputs.

This prototype implements:
1. Workout input → SMPL parameter change mapping
2. Physiologically constrained predictions
3. Time-based progression curves
4. Muscle group specific targeting

SMPL Shape Parameters (β):
- β₁: Overall body size (height-weight correlated)
- β₂: Height-weight ratio
- β₃: Upper/lower body proportion
- β₄: Torso width
- β₅: Arm thickness
- β₆: Leg thickness
- β₇: Chest depth
- β₈: Hip width
- β₉-β₁₀: Fine adjustments

Dependencies:
    pip install numpy scipy

For actual SMPL rendering, also need:
    pip install smplx torch trimesh pyrender

Usage:
    from smpl_predictor import WorkoutPredictor

    predictor = WorkoutPredictor()

    profile = UserProfile(
        age=28,
        gender='male',
        training_years=1,
        starting_body_fat=18,
    )

    workout = WorkoutPlan(
        frequency_per_week=4,
        split_type='push_pull_legs',
        focus_areas=['chest', 'arms'],
        cardio_hours_per_week=2,
    )

    changes = predictor.predict(profile, workout, weeks=12)
    print(changes.smpl_delta)  # Changes to apply to SMPL β parameters
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Gender(Enum):
    MALE = "male"
    FEMALE = "female"


class SplitType(Enum):
    PUSH_PULL_LEGS = "push_pull_legs"
    UPPER_LOWER = "upper_lower"
    BRO_SPLIT = "bro_split"  # One muscle group per day
    FULL_BODY = "full_body"
    CUSTOM = "custom"


class MuscleGroup(Enum):
    CHEST = "chest"
    BACK = "back"
    SHOULDERS = "shoulders"
    BICEPS = "biceps"
    TRICEPS = "triceps"
    QUADS = "quads"
    HAMSTRINGS = "hamstrings"
    GLUTES = "glutes"
    CALVES = "calves"
    CORE = "core"


@dataclass
class UserProfile:
    """User's physical profile and training history"""
    age: int
    gender: Gender
    training_years: float
    starting_body_fat: float  # Percentage
    height_inches: Optional[float] = None
    weight_lbs: Optional[float] = None
    genetic_potential: str = "average"  # "low", "average", "high"
    sleep_quality: float = 7.0  # 1-10
    nutrition_quality: float = 7.0  # 1-10

    @property
    def experience_level(self) -> str:
        if self.training_years < 1:
            return "beginner"
        elif self.training_years < 3:
            return "intermediate"
        else:
            return "advanced"


@dataclass
class WorkoutPlan:
    """User's workout plan details"""
    frequency_per_week: int  # 2-7 days
    split_type: SplitType
    focus_areas: List[MuscleGroup] = field(default_factory=list)
    cardio_hours_per_week: float = 0.0
    intensity: str = "moderate"  # "light", "moderate", "intense"
    progressive_overload: bool = True


@dataclass
class SMPLChanges:
    """Predicted changes to SMPL shape parameters"""
    beta_delta: Dict[int, float]  # Index -> change amount
    body_fat_delta: float
    muscle_mass_delta_lbs: float
    confidence: float  # 0-1

    @property
    def smpl_delta(self) -> np.ndarray:
        """Convert to 10-dimensional SMPL beta array"""
        delta = np.zeros(10)
        for idx, value in self.beta_delta.items():
            if 0 <= idx < 10:
                delta[idx] = value
        return delta


@dataclass
class PredictionResult:
    """Complete prediction result with progression"""
    smpl_changes: SMPLChanges
    weekly_progression: List[SMPLChanges]
    muscle_breakdown: Dict[str, float]
    warnings: List[str]
    recommendations: List[str]


class PhysiologyModel:
    """
    Models for physiologically accurate predictions.
    Based on exercise science research.
    """

    # Base muscle gain rates (lbs per month) by experience
    BASE_MUSCLE_GAIN_RATES = {
        'beginner': {'male': 2.0, 'female': 1.0},
        'intermediate': {'male': 1.0, 'female': 0.5},
        'advanced': {'male': 0.5, 'female': 0.25},
    }

    # Muscle group proportions (contribution to total muscle mass)
    MUSCLE_PROPORTIONS = {
        MuscleGroup.CHEST: 0.10,
        MuscleGroup.BACK: 0.15,
        MuscleGroup.SHOULDERS: 0.08,
        MuscleGroup.BICEPS: 0.04,
        MuscleGroup.TRICEPS: 0.05,
        MuscleGroup.QUADS: 0.20,
        MuscleGroup.HAMSTRINGS: 0.12,
        MuscleGroup.GLUTES: 0.15,
        MuscleGroup.CALVES: 0.06,
        MuscleGroup.CORE: 0.05,
    }

    # Muscle group growth rates (relative, 1.0 = average)
    MUSCLE_GROWTH_RATES = {
        MuscleGroup.CHEST: 1.1,
        MuscleGroup.BACK: 1.2,
        MuscleGroup.SHOULDERS: 1.0,
        MuscleGroup.BICEPS: 0.9,
        MuscleGroup.TRICEPS: 0.95,
        MuscleGroup.QUADS: 1.3,
        MuscleGroup.HAMSTRINGS: 1.0,
        MuscleGroup.GLUTES: 1.1,
        MuscleGroup.CALVES: 0.6,
        MuscleGroup.CORE: 0.8,
    }

    # Mapping muscle groups to SMPL beta parameters
    MUSCLE_TO_SMPL_BETA = {
        MuscleGroup.CHEST: {6: 0.15},  # β₇: Chest depth
        MuscleGroup.BACK: {3: 0.12},   # β₄: Torso width
        MuscleGroup.SHOULDERS: {3: 0.10, 4: 0.08},  # Torso + arm thickness
        MuscleGroup.BICEPS: {4: 0.20},  # β₅: Arm thickness
        MuscleGroup.TRICEPS: {4: 0.15},
        MuscleGroup.QUADS: {5: 0.25},   # β₆: Leg thickness
        MuscleGroup.HAMSTRINGS: {5: 0.15},
        MuscleGroup.GLUTES: {7: 0.20},  # β₈: Hip width
        MuscleGroup.CALVES: {5: 0.05},
        MuscleGroup.CORE: {3: 0.05, 6: -0.02},  # Slight taper effect
    }

    # Split type -> muscle frequency per week
    SPLIT_FREQUENCIES = {
        SplitType.PUSH_PULL_LEGS: {
            MuscleGroup.CHEST: 2,
            MuscleGroup.BACK: 2,
            MuscleGroup.SHOULDERS: 2,
            MuscleGroup.BICEPS: 2,
            MuscleGroup.TRICEPS: 2,
            MuscleGroup.QUADS: 2,
            MuscleGroup.HAMSTRINGS: 2,
            MuscleGroup.GLUTES: 2,
            MuscleGroup.CALVES: 2,
            MuscleGroup.CORE: 2,
        },
        SplitType.UPPER_LOWER: {
            MuscleGroup.CHEST: 2,
            MuscleGroup.BACK: 2,
            MuscleGroup.SHOULDERS: 2,
            MuscleGroup.BICEPS: 2,
            MuscleGroup.TRICEPS: 2,
            MuscleGroup.QUADS: 2,
            MuscleGroup.HAMSTRINGS: 2,
            MuscleGroup.GLUTES: 2,
            MuscleGroup.CALVES: 2,
            MuscleGroup.CORE: 2,
        },
        SplitType.BRO_SPLIT: {
            MuscleGroup.CHEST: 1,
            MuscleGroup.BACK: 1,
            MuscleGroup.SHOULDERS: 1,
            MuscleGroup.BICEPS: 1,
            MuscleGroup.TRICEPS: 1,
            MuscleGroup.QUADS: 1,
            MuscleGroup.HAMSTRINGS: 1,
            MuscleGroup.GLUTES: 1,
            MuscleGroup.CALVES: 1,
            MuscleGroup.CORE: 1,
        },
        SplitType.FULL_BODY: {
            MuscleGroup.CHEST: 3,
            MuscleGroup.BACK: 3,
            MuscleGroup.SHOULDERS: 3,
            MuscleGroup.BICEPS: 3,
            MuscleGroup.TRICEPS: 3,
            MuscleGroup.QUADS: 3,
            MuscleGroup.HAMSTRINGS: 3,
            MuscleGroup.GLUTES: 3,
            MuscleGroup.CALVES: 3,
            MuscleGroup.CORE: 3,
        },
    }

    @classmethod
    def get_age_modifier(cls, age: int) -> float:
        """Muscle gain decreases with age after 30"""
        if age < 30:
            return 1.0
        else:
            return max(0.5, 1.0 - (age - 30) * 0.02)

    @classmethod
    def get_genetic_modifier(cls, genetic_potential: str) -> float:
        """Modifier based on genetic potential"""
        modifiers = {
            'low': 0.7,
            'average': 1.0,
            'high': 1.4,
        }
        return modifiers.get(genetic_potential, 1.0)

    @classmethod
    def get_lifestyle_modifier(cls, sleep: float, nutrition: float) -> float:
        """Combined sleep and nutrition modifier"""
        sleep_mod = 0.6 + (sleep / 10) * 0.4
        nutrition_mod = 0.5 + (nutrition / 10) * 0.5
        return sleep_mod * nutrition_mod

    @classmethod
    def diminishing_returns_curve(cls, weeks: int, total_weeks: int) -> float:
        """
        Model diminishing returns over time.
        Returns a multiplier that decreases as training progresses.
        """
        # Use logarithmic curve for realistic diminishing returns
        progress = weeks / total_weeks
        return 1.0 - 0.3 * np.log1p(progress * 3)


class WorkoutPredictor:
    """
    Main predictor class that combines all models to predict
    body transformation based on workout inputs.
    """

    def __init__(self, conservatism: float = 0.8):
        """
        Args:
            conservatism: 0-1, how conservative predictions should be
                         (1.0 = very conservative, unlikely to over-promise)
        """
        self.conservatism = conservatism
        self.physiology = PhysiologyModel()

    def predict(
        self,
        profile: UserProfile,
        workout: WorkoutPlan,
        weeks: int,
        include_regression: bool = False
    ) -> PredictionResult:
        """
        Predict body transformation based on user profile and workout plan.

        Args:
            profile: User's physical profile
            workout: Workout plan details
            weeks: Number of weeks to predict
            include_regression: If True, also model what happens if training stops

        Returns:
            PredictionResult with SMPL changes and detailed breakdown
        """
        warnings = []
        recommendations = []

        # Validate inputs
        if weeks > 52:
            warnings.append("Predictions beyond 52 weeks have high uncertainty")
            weeks = min(weeks, 52)

        if workout.frequency_per_week < 2:
            warnings.append("Less than 2 sessions/week may limit results")

        # Calculate base gain rate
        gender_str = profile.gender.value if isinstance(profile.gender, Gender) else profile.gender
        base_rate = self.physiology.BASE_MUSCLE_GAIN_RATES[profile.experience_level][gender_str]

        # Apply modifiers
        age_mod = self.physiology.get_age_modifier(profile.age)
        genetic_mod = self.physiology.get_genetic_modifier(profile.genetic_potential)
        lifestyle_mod = self.physiology.get_lifestyle_modifier(
            profile.sleep_quality,
            profile.nutrition_quality
        )

        # Training frequency modifier
        freq_mod = min(1.3, 0.5 + workout.frequency_per_week * 0.15)

        # Intensity modifier
        intensity_mods = {'light': 0.7, 'moderate': 1.0, 'intense': 1.2}
        intensity_mod = intensity_mods.get(workout.intensity, 1.0)

        # Combined modifier
        total_modifier = (
            age_mod *
            genetic_mod *
            lifestyle_mod *
            freq_mod *
            intensity_mod *
            self.conservatism
        )

        # Calculate total expected muscle gain
        months = weeks / 4

        # Apply diminishing returns
        effective_months = 0
        for m in range(int(months) + 1):
            dim_return = self.physiology.diminishing_returns_curve(m, months)
            effective_months += dim_return / months if months > 0 else 0
        effective_months *= months

        total_muscle_gain = base_rate * total_modifier * effective_months

        # Calculate body fat change (simplified)
        # More cardio = more fat loss, muscle gain affects metabolism
        base_fat_change = -0.5 * (workout.cardio_hours_per_week / 2)  # Per month
        fat_change = base_fat_change * months * lifestyle_mod

        # Limit fat loss based on starting body fat
        min_healthy_bf = 8 if gender_str == 'male' else 15
        max_fat_loss = profile.starting_body_fat - min_healthy_bf
        fat_change = max(fat_change, -max_fat_loss)

        # Calculate muscle group breakdown
        muscle_breakdown = self._calculate_muscle_breakdown(
            workout,
            total_muscle_gain
        )

        # Convert to SMPL beta changes
        smpl_changes = self._convert_to_smpl_changes(
            muscle_breakdown,
            fat_change,
            total_muscle_gain,
            profile
        )

        # Generate weekly progression
        weekly_progression = self._generate_weekly_progression(
            smpl_changes,
            weeks
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            profile, workout, smpl_changes
        )

        return PredictionResult(
            smpl_changes=smpl_changes,
            weekly_progression=weekly_progression,
            muscle_breakdown={k.value: v for k, v in muscle_breakdown.items()},
            warnings=warnings,
            recommendations=recommendations
        )

    def _calculate_muscle_breakdown(
        self,
        workout: WorkoutPlan,
        total_gain: float
    ) -> Dict[MuscleGroup, float]:
        """Calculate how muscle gain distributes across muscle groups"""

        # Get base frequencies for split type
        split_type = workout.split_type if isinstance(workout.split_type, SplitType) else SplitType(workout.split_type)
        base_freq = self.physiology.SPLIT_FREQUENCIES.get(
            split_type,
            self.physiology.SPLIT_FREQUENCIES[SplitType.PUSH_PULL_LEGS]
        )

        # Apply focus area boost
        focus_boost = {}
        for muscle in workout.focus_areas:
            if isinstance(muscle, str):
                muscle = MuscleGroup(muscle)
            focus_boost[muscle] = 1.3  # 30% boost for focused areas

        # Calculate weighted distribution
        raw_scores = {}
        for muscle in MuscleGroup:
            freq = base_freq.get(muscle, 1)
            growth_rate = self.physiology.MUSCLE_GROWTH_RATES[muscle]
            proportion = self.physiology.MUSCLE_PROPORTIONS[muscle]
            boost = focus_boost.get(muscle, 1.0)

            raw_scores[muscle] = freq * growth_rate * proportion * boost

        # Normalize to total gain
        total_raw = sum(raw_scores.values())
        breakdown = {
            muscle: (score / total_raw) * total_gain
            for muscle, score in raw_scores.items()
        }

        return breakdown

    def _convert_to_smpl_changes(
        self,
        muscle_breakdown: Dict[MuscleGroup, float],
        fat_change: float,
        total_muscle_gain: float,
        profile: UserProfile
    ) -> SMPLChanges:
        """Convert muscle gains to SMPL beta parameter changes"""

        beta_changes = {}

        for muscle, gain in muscle_breakdown.items():
            mappings = self.physiology.MUSCLE_TO_SMPL_BETA.get(muscle, {})

            for beta_idx, sensitivity in mappings.items():
                current = beta_changes.get(beta_idx, 0)
                # Scale gain (in lbs) to SMPL parameter units
                # SMPL betas are typically in range [-3, 3] for realistic bodies
                smpl_change = gain * sensitivity * 0.1
                beta_changes[beta_idx] = current + smpl_change

        # Add body fat effect
        # Fat loss makes body appear more defined (slight reduction in overall size)
        if fat_change < 0:
            # Slight reduction in β₁ (overall size) for fat loss
            beta_changes[0] = beta_changes.get(0, 0) + fat_change * 0.02

        # Calculate confidence based on profile completeness
        confidence = 0.7
        if profile.height_inches and profile.weight_lbs:
            confidence += 0.1
        if profile.training_years > 0:
            confidence += 0.1
        confidence = min(0.95, confidence)

        return SMPLChanges(
            beta_delta=beta_changes,
            body_fat_delta=fat_change,
            muscle_mass_delta_lbs=total_muscle_gain,
            confidence=confidence
        )

    def _generate_weekly_progression(
        self,
        final_changes: SMPLChanges,
        total_weeks: int
    ) -> List[SMPLChanges]:
        """Generate week-by-week progression curve"""
        progression = []

        for week in range(1, total_weeks + 1):
            # Use smooth S-curve for realistic progression
            t = week / total_weeks
            progress = self._s_curve(t)

            week_beta = {
                idx: val * progress
                for idx, val in final_changes.beta_delta.items()
            }

            progression.append(SMPLChanges(
                beta_delta=week_beta,
                body_fat_delta=final_changes.body_fat_delta * progress,
                muscle_mass_delta_lbs=final_changes.muscle_mass_delta_lbs * progress,
                confidence=final_changes.confidence * 0.9  # Slightly lower for intermediate
            ))

        return progression

    def _s_curve(self, t: float) -> float:
        """S-curve (sigmoid) for smooth progression"""
        # Shifted sigmoid: slow start, fast middle, slow end
        return 1 / (1 + np.exp(-10 * (t - 0.5)))

    def _generate_recommendations(
        self,
        profile: UserProfile,
        workout: WorkoutPlan,
        changes: SMPLChanges
    ) -> List[str]:
        """Generate personalized recommendations"""
        recs = []

        if profile.sleep_quality < 7:
            recs.append(
                "Improving sleep to 7+ hours could increase gains by ~20%"
            )

        if profile.nutrition_quality < 7:
            recs.append(
                "Better nutrition (protein ~1g/lb bodyweight) could boost results"
            )

        if workout.frequency_per_week < 3:
            recs.append(
                "Increasing to 3+ sessions/week would significantly improve results"
            )

        if workout.cardio_hours_per_week == 0 and profile.starting_body_fat > 20:
            recs.append(
                "Adding 2-3 hours of cardio weekly would help with fat loss"
            )

        if len(workout.focus_areas) == 0:
            recs.append(
                "Consider specifying focus areas for more targeted visualization"
            )

        return recs


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("PhysiqAI SMPL Transformation Predictor")
    print("=" * 60)

    # Create user profile
    profile = UserProfile(
        age=28,
        gender=Gender.MALE,
        training_years=1.0,
        starting_body_fat=18.0,
        height_inches=70,
        weight_lbs=175,
        genetic_potential="average",
        sleep_quality=7.5,
        nutrition_quality=8.0
    )

    # Create workout plan
    workout = WorkoutPlan(
        frequency_per_week=4,
        split_type=SplitType.PUSH_PULL_LEGS,
        focus_areas=[MuscleGroup.CHEST, MuscleGroup.BICEPS],
        cardio_hours_per_week=2.0,
        intensity="moderate",
        progressive_overload=True
    )

    # Make prediction
    predictor = WorkoutPredictor(conservatism=0.8)
    result = predictor.predict(profile, workout, weeks=12)

    print(f"\n📊 Prediction for {profile.age}yo {profile.gender.value}")
    print(f"   Experience: {profile.experience_level}")
    print(f"   Starting BF: {profile.starting_body_fat}%")

    print(f"\n💪 Workout Plan:")
    print(f"   {workout.frequency_per_week}x per week, {workout.split_type.value}")
    print(f"   Focus: {[m.value for m in workout.focus_areas]}")
    print(f"   Cardio: {workout.cardio_hours_per_week} hrs/week")

    print(f"\n📈 Predicted Changes (12 weeks):")
    print(f"   Muscle gain: +{result.smpl_changes.muscle_mass_delta_lbs:.1f} lbs")
    print(f"   Body fat: {result.smpl_changes.body_fat_delta:.1f}%")
    print(f"   Confidence: {result.smpl_changes.confidence*100:.0f}%")

    print(f"\n🎯 SMPL Beta Changes:")
    smpl_delta = result.smpl_changes.smpl_delta
    param_names = [
        "Overall size", "Height-weight", "Upper/Lower", "Torso width",
        "Arm thickness", "Leg thickness", "Chest depth", "Hip width",
        "Fine adj. 1", "Fine adj. 2"
    ]
    for i, (name, val) in enumerate(zip(param_names, smpl_delta)):
        if abs(val) > 0.01:
            print(f"   β{i} ({name}): {val:+.3f}")

    print(f"\n💪 Muscle Breakdown:")
    sorted_muscles = sorted(
        result.muscle_breakdown.items(),
        key=lambda x: x[1],
        reverse=True
    )
    for muscle, gain in sorted_muscles[:5]:
        print(f"   {muscle}: +{gain:.2f} lbs")

    if result.warnings:
        print(f"\n⚠️ Warnings:")
        for w in result.warnings:
            print(f"   - {w}")

    if result.recommendations:
        print(f"\n💡 Recommendations:")
        for r in result.recommendations:
            print(f"   - {r}")

    print(f"\n📅 Week 4 Preview:")
    week4 = result.weekly_progression[3]
    print(f"   Muscle: +{week4.muscle_mass_delta_lbs:.1f} lbs")
    print(f"   Body fat: {week4.body_fat_delta:.1f}%")
