#!/usr/bin/env python3
"""
workout_morph.py - Workout-to-Body Transformation Engine

Converts workout logs into real-time avatar updates with
immediate pump effects and long-term adaptation projections.
"""

import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum

from .vertex_displacement import MuscleGroup, MuscleDisplacementSystem


class ExerciseType(Enum):
    """Types of exercises with different morphing effects"""
    COMPOUND = "compound"      # Multi-joint, systemic effect
    ISOLATION = "isolation"    # Single muscle, localized pump
    CARDIO = "cardio"          # Fat burn, minimal pump
    CALISTHENICS = "calisthenics"  # Bodyweight, moderate effect


@dataclass
class Exercise:
    """Individual exercise in a workout"""
    name: str
    muscle_groups: List[MuscleGroup]
    exercise_type: ExerciseType
    sets: int
    reps: int
    weight: float  # lbs
    rpe: float = 7.0  # Rate of perceived exertion (1-10)

    @property
    def volume(self) -> float:
        """Calculate total volume (weight × reps × sets)"""
        return self.weight * self.reps * self.sets

    @property
    def intensity_score(self) -> float:
        """Calculate intensity score based on volume and RPE"""
        return (self.volume / 1000) * (self.rpe / 5)


@dataclass
class WorkoutSession:
    """Complete workout session"""
    exercises: List[Exercise]
    start_time: datetime
    duration_minutes: float
    notes: str = ""

    @property
    def total_volume(self) -> float:
        return sum(ex.volume for ex in self.exercises)

    @property
    def muscle_groups_trained(self) -> set:
        groups = set()
        for ex in self.exercises:
            groups.update(ex.muscle_groups)
        return groups


@dataclass
class ImmediateEffects:
    """Immediate post-workout effects (pump, vascularity)"""
    muscle_pump: Dict[MuscleGroup, float]  # Swelling per muscle
    vascularity_boost: float  # Overall vascularity increase
    duration_minutes: float  # How long effects last

    def get_displacement_activations(self) -> Dict[MuscleGroup, float]:
        """Convert to format for MuscleDisplacementSystem"""
        return self.muscle_pump


@dataclass
class LongTermAdaptation:
    """Projected long-term changes from consistent training"""
    muscle_gain_rate_per_week: Dict[MuscleGroup, float]  # lbs per week
    fat_burn_per_session: float  # lbs per workout
    metabolic_adaptation: float  # Calorie burn increase
    estimated_timeline_days: int

    def get_total_muscle_gain(self, timeframe_weeks: int = 4) -> float:
        """Estimate total muscle gain over timeframe"""
        weekly_total = sum(self.muscle_gain_rate_per_week.values())
        return weekly_total * timeframe_weeks


@dataclass
class MorphUpdate:
    """Complete morph update from workout"""
    workout: WorkoutSession
    immediate: ImmediateEffects
    projected: LongTermAdaptation
    timestamp: datetime

    def to_dict(self) -> dict:
        """Serialize for storage"""
        return {
            'workout': {
                'exercises': [self._exercise_to_dict(ex) for ex in self.workout.exercises],
                'total_volume': self.workout.total_volume,
                'duration': self.workout.duration_minutes
            },
            'immediate': {
                'muscle_pump': {mg.value: v for mg, v in self.immediate.muscle_pump.items()},
                'vascularity_boost': self.immediate.vascularity_boost,
                'duration_minutes': self.immediate.duration_minutes
            },
            'projected': {
                'muscle_gain_per_week': {mg.value: v for mg, v in self.projected.muscle_gain_rate_per_week.items()},
                'fat_burn_per_session': self.projected.fat_burn_per_session,
                'timeline_days': self.projected.estimated_timeline_days
            },
            'timestamp': self.timestamp.isoformat()
        }

    def _exercise_to_dict(self, ex: Exercise) -> dict:
        return {
            'name': ex.name,
            'muscle_groups': [mg.value for mg in ex.muscle_groups],
            'type': ex.exercise_type.value,
            'sets': ex.sets,
            'reps': ex.reps,
            'weight': ex.weight,
            'volume': ex.volume
        }


class WorkoutMorphEngine:
    """
    Main engine for converting workouts to body morph updates.

    Processes workout data and calculates:
    1. Immediate pump effects (temporary)
    2. Long-term adaptation projections
    3. Visual feedback parameters
    """

    def __init__(self):
        self.displacement_system = MuscleDisplacementSystem()

        # Training response models (simplified - would be trained on data)
        self.muscle_response_rates = {
            # Muscle group: max weekly gain (lbs) for beginner
            MuscleGroup.BICEPS: 0.05,
            MuscleGroup.TRICEPS: 0.05,
            MuscleGroup.CHEST: 0.08,
            MuscleGroup.SHOULDERS: 0.06,
            MuscleGroup.LATS: 0.08,
            MuscleGroup.ABS: 0.03,
            MuscleGroup.QUADS: 0.10,
            MuscleGroup.HAMSTRINGS: 0.08,
            MuscleGroup.CALVES: 0.04,
            MuscleGroup.GLUTES: 0.08,
            MuscleGroup.TRAPS: 0.04,
        }

    def process_workout(self, workout: WorkoutSession) -> MorphUpdate:
        """
        Process workout and generate morph update.

        Args:
            workout: WorkoutSession with exercises

        Returns:
            MorphUpdate with immediate and projected effects
        """
        immediate = self._calculate_immediate_effects(workout)
        projected = self._calculate_long_term_adaptation(workout)

        return MorphUpdate(
            workout=workout,
            immediate=immediate,
            projected=projected,
            timestamp=workout.start_time
        )

    def _calculate_immediate_effects(self, workout: WorkoutSession) -> ImmediateEffects:
        """
        Calculate immediate post-workout pump effects.

        Pump depends on:
        - Volume per muscle group
        - Exercise type (isolation > compound for pump)
        - Time under tension
        """
        muscle_pump = {mg: 0.0 for mg in MuscleGroup}

        for exercise in workout.exercises:
            # Calculate pump factor for this exercise
            volume = exercise.volume

            # Exercise type modifier
            type_multipliers = {
                ExerciseType.ISOLATION: 1.5,  # Best for pump
                ExerciseType.COMPOUND: 1.0,
                ExerciseType.CALISTHENICS: 0.8,
                ExerciseType.CARDIO: 0.2,
            }
            type_mult = type_multipliers.get(exercise.exercise_type, 1.0)

            # Volume to pump conversion
            # 1000 lbs = moderate pump
            base_pump = min(volume / 1500, 1.0) * type_mult

            # Apply to each muscle group trained
            for muscle in exercise.muscle_groups:
                # Accumulate pump (max 1.0)
                muscle_pump[muscle] = min(1.0, muscle_pump[muscle] + base_pump)

        # Vascularity depends on overall intensity and body fat
        avg_pump = np.mean([v for v in muscle_pump.values() if v > 0]) if any(muscle_pump.values()) else 0
        vascularity_boost = avg_pump * 0.5

        # Duration depends on intensity
        max_pump = max(muscle_pump.values()) if muscle_pump else 0
        duration = 60 + max_pump * 120  # 60-180 minutes

        return ImmediateEffects(
            muscle_pump=muscle_pump,
            vascularity_boost=vascularity_boost,
            duration_minutes=duration
        )

    def _calculate_long_term_adaptation(self, workout: WorkoutSession) -> LongTermAdaptation:
        """
        Calculate projected muscle growth and fat loss.

        Uses simplified training science:
        - Hypertrophy requires progressive overload
        - Growth rate depends on training status
        - Fat loss from calorie burn
        """
        muscle_gains = {}

        for exercise in workout.exercises:
            volume = exercise.volume

            for muscle in exercise.muscle_groups:
                if muscle not in self.muscle_response_rates:
                    continue

                # Base response rate for this muscle
                base_rate = self.muscle_response_rates[muscle]

                # Volume stimulus
                # Minimum effective volume: ~1000 lbs per week per muscle
                # Maximum recoverable: ~5000 lbs
                volume_factor = min(volume / 2000, 1.0)

                # Weekly rate from this exercise
                weekly_gain = base_rate * volume_factor

                # Accumulate across exercises
                if muscle in muscle_gains:
                    muscle_gains[muscle] += weekly_gain * 0.7  # Diminishing returns
                else:
                    muscle_gains[muscle] = weekly_gain

        # Cap at realistic rates
        for muscle in muscle_gains:
            muscle_gains[muscle] = min(muscle_gains[muscle], base_rate * 1.5)

        # Fat burn from workout
        # Approx 100 calories per 1000 lbs volume
        calories_burned = workout.total_volume / 10
        fat_burn_lbs = calories_burned / 3500

        # Metabolic adaptation
        # More muscle = higher BMR
        metabolic_adaptation = len(muscle_gains) * 5  # Approx 5 cal per muscle

        return LongTermAdaptation(
            muscle_gain_rate_per_week=muscle_gains,
            fat_burn_per_session=fat_burn_lbs,
            metabolic_adaptation=metabolic_adaptation,
            estimated_timeline_days=30  # Visible results in ~1 month
        )

    def generate_timeline_projection(self,
                                    workout_plan: List[WorkoutSession],
                                    start_body_state,
                                    weeks: int = 12) -> List[dict]:
        """
        Generate projected body changes over time.

        Args:
            workout_plan: List of planned workouts
            start_body_state: Initial BodyState
            weeks: Number of weeks to project

        Returns:
            List of weekly body state projections
        """
        timeline = []
        current_state = start_body_state

        # Group workouts by week
        weekly_workouts = [[] for _ in range(weeks)]
        for workout in workout_plan:
            week = min(int((workout.start_time - datetime.now()).days / 7), weeks - 1)
            if week >= 0:
                weekly_workouts[week].append(workout)

        # Project week by week
        for week_idx, workouts in enumerate(weekly_workouts):
            weekly_muscle_gain = 0
            weekly_fat_loss = 0

            for workout in workouts:
                update = self.process_workout(workout)
                weekly_muscle_gain += sum(update.projected.muscle_gain_rate_per_week.values())
                weekly_fat_loss += update.projected.fat_burn_per_session

            # Update body state
            new_weight = current_state.weight + weekly_muscle_gain - weekly_fat_loss
            new_muscle_pct = (current_state.lean_mass + weekly_muscle_gain) / new_weight * 100
            new_fat_pct = current_state.fat_pct - (weekly_fat_loss / current_state.weight * 100)

            timeline.append({
                'week': week_idx + 1,
                'weight': new_weight,
                'muscle_pct': new_muscle_pct,
                'fat_pct': max(5, new_fat_pct),
                'muscle_gain': weekly_muscle_gain,
                'fat_loss': weekly_fat_loss
            })

            # Update for next iteration
            current_state = current_state.__class__(
                weight=new_weight,
                muscle_pct=new_muscle_pct,
                fat_pct=max(5, new_fat_pct)
            )

        return timeline


def create_sample_workout() -> WorkoutSession:
    """Create a sample upper body workout for demo"""
    exercises = [
        Exercise(
            name="Bench Press",
            muscle_groups=[MuscleGroup.CHEST, MuscleGroup.SHOULDERS, MuscleGroup.TRICEPS],
            exercise_type=ExerciseType.COMPOUND,
            sets=4,
            reps=8,
            weight=185,
            rpe=8
        ),
        Exercise(
            name="Overhead Press",
            muscle_groups=[MuscleGroup.SHOULDERS, MuscleGroup.TRAPS],
            exercise_type=ExerciseType.COMPOUND,
            sets=3,
            reps=10,
            weight=115,
            rpe=7
        ),
        Exercise(
            name="Bicep Curls",
            muscle_groups=[MuscleGroup.BICEPS],
            exercise_type=ExerciseType.ISOLATION,
            sets=4,
            reps=12,
            weight=35,
            rpe=8
        ),
        Exercise(
            name="Tricep Pushdowns",
            muscle_groups=[MuscleGroup.TRICEPS],
            exercise_type=ExerciseType.ISOLATION,
            sets=3,
            reps=15,
            weight=50,
            rpe=7
        ),
        Exercise(
            name="Lateral Raises",
            muscle_groups=[MuscleGroup.SHOULDERS],
            exercise_type=ExerciseType.ISOLATION,
            sets=3,
            reps=15,
            weight=20,
            rpe=7
        )
    ]

    return WorkoutSession(
        exercises=exercises,
        start_time=datetime.now(),
        duration_minutes=60,
        notes="Upper body hypertrophy focus"
    )


def demo_workout_morph():
    """Demonstrate workout morph engine"""
    print("Workout Morph Engine Demo")
    print("=" * 60)

    # Create engine and sample workout
    engine = WorkoutMorphEngine()
    workout = create_sample_workout()

    print("\nSample Workout:")
    print("-" * 60)
    print(f"Duration: {workout.duration_minutes} minutes")
    print(f"Total Volume: {workout.total_volume:,.0f} lbs")
    print("\nExercises:")
    for ex in workout.exercises:
        print(f"  {ex.name:20s} {ex.sets}×{ex.reps} @ {ex.weight} lbs "
              f"(vol: {ex.volume:,.0f})")

    # Process workout
    print("\n" + "=" * 60)
    update = engine.process_workout(workout)

    # Immediate effects
    print("\nImmediate Effects (Pump):")
    print("-" * 60)
    print(f"Duration: {update.immediate.duration_minutes:.0f} minutes")
    print(f"Vascularity boost: {update.immediate.vascularity_boost:.0%}")
    print("\nMuscle pump by group:")
    for muscle, pump in sorted(update.immediate.muscle_pump.items(),
                                key=lambda x: x[1], reverse=True):
        if pump > 0:
            bar = "█" * int(pump * 20)
            print(f"  {muscle.value:12s}: {pump:.0%} {bar}")

    # Long-term projections
    print("\n" + "=" * 60)
    print("\nLong-term Adaptation (per week):")
    print("-" * 60)
    print(f"Fat burn per session: {update.projected.fat_burn_per_session:.3f} lbs")
    print(f"Metabolic adaptation: +{update.projected.metabolic_adaptation:.0f} cal/day")
    print("\nProjected muscle gain rate:")
    total_gain = 0
    for muscle, rate in sorted(update.projected.muscle_gain_rate_per_week.items(),
                                key=lambda x: x[1], reverse=True):
        if rate > 0:
            total_gain += rate
            bar = "█" * int(rate / 0.02)
            print(f"  {muscle.value:12s}: {rate*1000:.1f}g/week {bar}")

    print(f"\nTotal weekly muscle gain: {total_gain*1000:.1f}g")
    print(f"12-week projection: {total_gain * 12 * 1000:.0f}g ({total_gain * 12:.2f} lbs)")


if __name__ == "__main__":
    demo_workout_morph()
