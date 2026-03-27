#!/usr/bin/env python3
"""
Workout Engine Service
======================

Processes workout logs and calculates:
- Immediate effects (pump, vascularity)
- Long-term adaptations (muscle gain, fat loss)
- Body predictions over time
- Avatar morphing parameters
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np
import uuid

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models.database import (
    Workout, WorkoutExercise, BodyMeasurement, Goal,
    ProgressEntry, User, db
)


# Muscle group definitions with anatomical relationships
MUSCLE_GROUPS = {
    'chest': {' antagonists': ['lats', 'traps'], 'synergists': ['shoulders', 'triceps']},
    'back': {'antagonists': ['chest', 'abs'], 'synergists': ['biceps', 'traps']},
    'lats': {'antagonists': ['chest'], 'synergists': ['biceps', 'traps']},
    'traps': {'antagonists': [''], 'synergists': ['shoulders', 'lats']},
    'shoulders': {'antagonists': ['lats'], 'synergists': ['triceps', 'traps']},
    'biceps': {'antagonists': ['triceps'], 'synergists': ['forearms']},
    'triceps': {'antagonists': ['biceps'], 'synergists': ['shoulders', 'chest']},
    'forearms': {'antagonists': [''], 'synergists': ['biceps']},
    'abs': {'antagonists': ['lower_back'], 'synergists': ['obliques']},
    'obliques': {'antagonists': [''], 'synergists': ['abs']},
    'lower_back': {'antagonists': ['abs'], 'synergists': ['glutes']},
    'glutes': {'antagonists': ['hip_flexors'], 'synergists': ['hamstrings']},
    'quads': {'antagonists': ['hamstrings'], 'synergists': ['glutes']},
    'hamstrings': {'antagonists': ['quads'], 'synergists': ['glutes', 'calves']},
    'calves': {'antagonists': ['tibialis'], 'synergists': ['hamstrings']},
    'tibialis': {'antagonists': ['calves'], 'synergists': ['']},
    'hip_flexors': {'antagonists': ['glutes'], 'synergists': ['quads']},
    'neck': {'antagonists': [''], 'synergists': ['traps']},
}

# Training response rates (max weekly gain in kg for beginner/intermediate/advanced)
MUSCLE_RESPONSE_RATES = {
    'biceps': {'beginner': 0.025, 'intermediate': 0.012, 'advanced': 0.005},
    'triceps': {'beginner': 0.025, 'intermediate': 0.012, 'advanced': 0.005},
    'chest': {'beginner': 0.040, 'intermediate': 0.020, 'advanced': 0.008},
    'shoulders': {'beginner': 0.030, 'intermediate': 0.015, 'advanced': 0.006},
    'lats': {'beginner': 0.040, 'intermediate': 0.020, 'advanced': 0.008},
    'traps': {'beginner': 0.020, 'intermediate': 0.010, 'advanced': 0.004},
    'abs': {'beginner': 0.015, 'intermediate': 0.008, 'advanced': 0.003},
    'obliques': {'beginner': 0.015, 'intermediate': 0.008, 'advanced': 0.003},
    'lower_back': {'beginner': 0.020, 'intermediate': 0.010, 'advanced': 0.004},
    'quads': {'beginner': 0.050, 'intermediate': 0.025, 'advanced': 0.010},
    'hamstrings': {'beginner': 0.040, 'intermediate': 0.020, 'advanced': 0.008},
    'glutes': {'beginner': 0.040, 'intermediate': 0.020, 'advanced': 0.008},
    'calves': {'beginner': 0.020, 'intermediate': 0.010, 'advanced': 0.004},
    'forearms': {'beginner': 0.015, 'intermediate': 0.008, 'advanced': 0.003},
}


@dataclass
class ImmediateEffects:
    """Immediate post-workout effects"""
    muscle_pump: Dict[str, float]  # Pump per muscle (0-1)
    vascularity_boost: float  # Overall vascularity increase (0-1)
    energy_expenditure_kcal: float
    duration_minutes: float  # How long effects last

    def to_dict(self) -> dict:
        return {
            'muscle_pump': self.muscle_pump,
            'vascularity_boost': round(self.vascularity_boost, 3),
            'energy_expenditure_kcal': round(self.energy_expenditure_kcal, 1),
            'duration_minutes': round(self.duration_minutes, 1),
        }


@dataclass
class LongTermAdaptation:
    """Projected long-term changes"""
    muscle_gain_rate_per_week_kg: Dict[str, float]
    fat_burn_per_session_kg: float
    metabolic_adaptation_kcal: float  # Daily BMR increase
    estimated_timeline_weeks: int
    projected_weight_change_kg: float
    projected_body_fat_change_pct: float

    def to_dict(self) -> dict:
        return {
            'muscle_gain_rate_per_week_kg': {k: round(v, 4) for k, v in self.muscle_gain_rate_per_week_kg.items()},
            'fat_burn_per_session_kg': round(self.fat_burn_per_session_kg, 4),
            'metabolic_adaptation_kcal': round(self.metabolic_adaptation_kcal, 2),
            'estimated_timeline_weeks': self.estimated_timeline_weeks,
            'projected_weight_change_kg': round(self.projected_weight_change_kg, 2),
            'projected_body_fat_change_pct': round(self.projected_body_fat_change_pct, 2),
        }


@dataclass
class WorkoutAnalysis:
    """Complete workout analysis"""
    workout: Workout
    immediate_effects: ImmediateEffects
    long_term_adaptation: LongTermAdaptation
    avatar_morph_params: Dict[str, float]  # Parameters for avatar morphing
    recommendations: List[str]

    def to_dict(self) -> dict:
        return {
            'workout': self.workout.to_dict(),
            'immediate_effects': self.immediate_effects.to_dict(),
            'long_term_adaptation': self.long_term_adaptation.to_dict(),
            'avatar_morph_params': self.avatar_morph_params,
            'recommendations': self.recommendations,
        }


@dataclass
class BodyPrediction:
    """Predicted body state at a future date"""
    weeks_from_now: int
    predicted_weight_kg: float
    predicted_body_fat_pct: float
    predicted_muscle_mass_kg: float
    predicted_measurements: Dict[str, float]
    smpl_betas: List[float]  # Adjusted shape parameters
    confidence: float

    def to_dict(self) -> dict:
        return {
            'weeks_from_now': self.weeks_from_now,
            'predicted_weight_kg': round(self.predicted_weight_kg, 1),
            'predicted_body_fat_pct': round(self.predicted_body_fat_pct, 1),
            'predicted_muscle_mass_kg': round(self.predicted_muscle_mass_kg, 1),
            'predicted_measurements': {k: round(v, 1) for k, v in self.predicted_measurements.items()},
            'smpl_betas': [round(b, 3) for b in self.smpl_betas],
            'confidence': round(self.confidence, 2),
        }


class WorkoutEngine:
    """
    Main workout processing engine.

    Uses exercise science principles:
    - Volume drives hypertrophy (sets × reps × weight)
    - Progressive overload required for adaptation
    - Recovery time affects muscle growth
    - Individual response rates vary by training status
    """

    def __init__(self):
        self.output_dir = Path(__file__).parent.parent.parent / 'output' / 'predictions'
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def analyze_workout(self, workout: Workout, user: User) -> WorkoutAnalysis:
        """
        Analyze a workout and generate predictions.

        Args:
            workout: The workout to analyze
            user: The user who performed the workout

        Returns:
            Complete workout analysis with effects and predictions
        """
        # Calculate workout stats
        workout.calculate_stats()

        # Determine training status based on workout history
        training_status = self._determine_training_status(user)

        # Calculate immediate effects
        immediate = self._calculate_immediate_effects(workout, user)

        # Calculate long-term adaptations
        long_term = self._calculate_long_term_adaptation(workout, user, training_status)

        # Generate avatar morphing parameters
        avatar_params = self._calculate_avatar_morph_params(immediate, long_term)

        # Generate recommendations
        recommendations = self._generate_recommendations(workout, user, training_status)

        return WorkoutAnalysis(
            workout=workout,
            immediate_effects=immediate,
            long_term_adaptation=long_term,
            avatar_morph_params=avatar_params,
            recommendations=recommendations,
        )

    def _determine_training_status(self, user: User) -> str:
        """Determine user's training status based on history"""
        workouts = db.get_user_workouts(user.id, limit=52)  # Last year

        if len(workouts) < 10:
            return 'beginner'
        elif len(workouts) < 50:
            return 'intermediate'
        else:
            return 'advanced'

    def _calculate_immediate_effects(self, workout: Workout, user: User) -> ImmediateEffects:
        """Calculate immediate post-workout effects"""
        muscle_pump = {}

        total_volume = workout.total_volume

        for exercise in workout.exercises:
            volume = exercise.volume

            # Exercise type modifier
            type_multipliers = {
                'isolation': 1.5,  # Best pump
                'compound': 1.0,
                'calisthenics': 0.8,
                'cardio': 0.2,
            }
            type_mult = type_multipliers.get(exercise.exercise_type, 1.0)

            # RPE modifier (higher RPE = more pump)
            rpe_mult = exercise.rpe / 7.0

            # Calculate pump for each muscle
            base_pump = min(volume / 1500, 1.0) * type_mult * rpe_mult

            for muscle in exercise.muscle_groups:
                current_pump = muscle_pump.get(muscle, 0)
                muscle_pump[muscle] = min(1.0, current_pump + base_pump)

        # Vascularity depends on intensity and body fat
        active_pumps = [v for v in muscle_pump.values() if v > 0]
        avg_pump = np.mean(active_pumps) if active_pumps else 0
        vascularity_boost = avg_pump * 0.6

        # Energy expenditure
        # Approx 0.1 kcal per lb of volume
        energy_exp = total_volume * 0.05  # Simplified

        # Duration depends on intensity
        max_pump = max(muscle_pump.values()) if muscle_pump else 0
        duration = 60 + max_pump * 120  # 60-180 minutes

        return ImmediateEffects(
            muscle_pump=muscle_pump,
            vascularity_boost=vascularity_boost,
            energy_expenditure_kcal=energy_exp,
            duration_minutes=duration,
        )

    def _calculate_long_term_adaptation(self, workout: Workout, user: User,
                                        training_status: str) -> LongTermAdaptation:
        """Calculate projected long-term adaptations"""
        muscle_gains = {}

        for exercise in workout.exercises:
            volume = exercise.volume

            for muscle in exercise.muscle_groups:
                if muscle not in MUSCLE_RESPONSE_RATES:
                    continue

                # Get response rate for this muscle and training status
                base_rate = MUSCLE_RESPONSE_RATES[muscle][training_status]

                # Volume factor
                # MEV (minimum effective volume): ~2000 kg/week
                # MRV (maximum recoverable): ~8000 kg/week
                volume_factor = min(volume / 2500, 1.2)

                # Progressive overload check (would compare to previous workouts)
                overload_factor = 1.0  # Simplified

                # Weekly rate from this exercise
                weekly_gain = base_rate * volume_factor * overload_factor

                # Accumulate with diminishing returns
                if muscle in muscle_gains:
                    muscle_gains[muscle] += weekly_gain * 0.7
                else:
                    muscle_gains[muscle] = weekly_gain

        # Cap at realistic rates
        for muscle in muscle_gains:
            max_rate = MUSCLE_RESPONSE_RATES.get(muscle, {}).get(training_status, 0.01) * 1.5
            muscle_gains[muscle] = min(muscle_gains[muscle], max_rate)

        # Fat burn
        calories_burned = workout.total_volume * 0.1  # Simplified
        fat_burn_kg = calories_burned / 7700  # kg of fat

        # Metabolic adaptation
        # More muscle = higher BMR (~10 kcal per kg muscle)
        metabolic_adaptation = sum(muscle_gains.values()) * 10 * 7  # Weekly

        # Calculate 12-week projection
        weekly_muscle_gain = sum(muscle_gains.values())
        weekly_fat_loss = fat_burn_kg

        weeks = 12
        total_muscle_gain = weekly_muscle_gain * weeks
        total_fat_loss = weekly_fat_loss * weeks

        # Current stats
        current_weight = user.current_weight_kg or 75
        current_bf = user.current_body_fat_pct or 20
        current_muscle = user.current_muscle_mass_kg or (current_weight * 0.4)

        projected_weight = current_weight + total_muscle_gain - total_fat_loss
        projected_muscle = current_muscle + total_muscle_gain
        projected_bf = max(5, (current_bf * current_weight / 100 - total_fat_loss) / projected_weight * 100)

        return LongTermAdaptation(
            muscle_gain_rate_per_week_kg=muscle_gains,
            fat_burn_per_session_kg=fat_burn_kg,
            metabolic_adaptation_kcal=metabolic_adaptation,
            estimated_timeline_weeks=weeks,
            projected_weight_change_kg=projected_weight - current_weight,
            projected_body_fat_change_pct=projected_bf - current_bf,
        )

    def _calculate_avatar_morph_params(self, immediate: ImmediateEffects,
                                       long_term: LongTermAdaptation) -> Dict[str, float]:
        """Calculate avatar morphing parameters"""
        params = {}

        # Immediate effects (temporary)
        max_pump = max(immediate.muscle_pump.values()) if immediate.muscle_pump else 0
        params['pump_scale'] = 1.0 + max_pump * 0.05  # 0-5% size increase
        params['vascularity'] = immediate.vascularity_boost

        # Long-term adaptations (permanent)
        total_muscle_gain = sum(long_term.muscle_gain_rate_per_week_kg.values()) * 12

        # Adjust body shape based on muscle distribution
        # Beta 0: Overall size
        params['beta_0_adjustment'] = total_muscle_gain * 0.1

        # Beta 4: Arms
        arm_muscles = ['biceps', 'triceps', 'forearms']
        arm_gain = sum(long_term.muscle_gain_rate_per_week_kg.get(m, 0) for m in arm_muscles) * 12
        params['beta_4_adjustment'] = arm_gain * 2

        # Beta 5: Legs
        leg_muscles = ['quads', 'hamstrings', 'calves']
        leg_gain = sum(long_term.muscle_gain_rate_per_week_kg.get(m, 0) for m in leg_muscles) * 12
        params['beta_5_adjustment'] = leg_gain * 1.5

        # Beta 6: Chest
        chest_gain = long_term.muscle_gain_rate_per_week_kg.get('chest', 0) * 12
        params['beta_6_adjustment'] = chest_gain * 2

        # Beta 7: Hips/glutes
        hip_gain = long_term.muscle_gain_rate_per_week_kg.get('glutes', 0) * 12
        params['beta_7_adjustment'] = hip_gain * 1.5

        return params

    def _generate_recommendations(self, workout: Workout, user: User,
                                   training_status: str) -> List[str]:
        """Generate personalized recommendations"""
        recommendations = []

        # Volume recommendations
        total_volume = workout.total_volume
        if total_volume < 5000:
            recommendations.append("Consider increasing workout volume for better results")
        elif total_volume > 15000:
            recommendations.append("High volume workout - ensure adequate recovery")

        # Exercise balance
        muscle_counts = {}
        for ex in workout.exercises:
            for mg in ex.muscle_groups:
                muscle_counts[mg] = muscle_counts.get(mg, 0) + 1

        if 'chest' in muscle_counts and 'back' not in muscle_counts:
            recommendations.append("Add back exercises for balanced upper body development")

        if 'quads' in muscle_counts and 'hamstrings' not in muscle_counts:
            recommendations.append("Add hamstring exercises to prevent muscle imbalances")

        # Training status specific
        if training_status == 'beginner':
            recommendations.append("Focus on compound movements for maximum growth")
        elif training_status == 'advanced':
            recommendations.append("Consider periodization to break through plateaus")

        # Default
        if not recommendations:
            recommendations.append("Great workout! Keep up the consistent effort.")

        return recommendations

    def predict_body_timeline(self, user: User, weeks: int = 12,
                               workout_plan: Optional[List[Workout]] = None) -> List[BodyPrediction]:
        """
        Generate body predictions over time.

        Args:
            user: The user to predict for
            weeks: Number of weeks to predict
            workout_plan: Optional list of planned workouts

        Returns:
            List of predictions for each week
        """
        predictions = []

        # Get current state
        current_weight = user.current_weight_kg or 75
        current_bf = user.current_body_fat_pct or 20
        current_muscle = user.current_muscle_mass_kg or (current_weight * 0.4)

        # Get current SMPL betas from latest photo
        photos = db.get_user_photos(user.id)
        current_betas = photos[-1].smpl_betas if photos and photos[-1].smpl_betas else [0.0] * 10
        current_betas = np.array(current_betas)

        # Default workout plan if none provided
        if not workout_plan:
            workout_plan = self._generate_default_workout_plan(weeks)

        # Calculate weekly adaptations
        weekly_adaptations = self._calculate_weekly_adaptations(workout_plan, weeks)

        for week in range(1, weeks + 1):
            adaptation = weekly_adaptations.get(week, {'muscle_gain': 0, 'fat_loss': 0})

            # Update body composition
            muscle_gain = adaptation['muscle_gain']
            fat_loss = adaptation['fat_loss']

            current_weight = current_weight + muscle_gain - fat_loss
            current_muscle = current_muscle + muscle_gain

            fat_mass = current_weight * (current_bf / 100) - fat_loss
            current_bf = max(5, (fat_mass / current_weight) * 100)

            # Adjust SMPL betas
            adjusted_betas = self._adjust_betas_for_composition(
                current_betas, muscle_gain, fat_loss, week
            )

            # Calculate measurements
            measurements = self._estimate_measurements(current_weight, current_bf, current_muscle)

            # Confidence decreases over time
            confidence = max(0.5, 0.9 - (week / weeks) * 0.4)

            predictions.append(BodyPrediction(
                weeks_from_now=week,
                predicted_weight_kg=current_weight,
                predicted_body_fat_pct=current_bf,
                predicted_muscle_mass_kg=current_muscle,
                predicted_measurements=measurements,
                smpl_betas=adjusted_betas.tolist(),
                confidence=confidence,
            ))

        return predictions

    def _generate_default_workout_plan(self, weeks: int) -> List[Workout]:
        """Generate a default 4-day split workout plan"""
        workouts = []
        base_date = datetime.now()

        for week in range(weeks):
            for day in range(4):  # 4 workout days per week
                workout_date = base_date + timedelta(weeks=week, days=day)

                if day == 0:  # Push
                    exercises = [
                        WorkoutExercise("Bench Press", ["chest", "triceps", "shoulders"], "compound", 4, 8, 80, 8),
                        WorkoutExercise("Overhead Press", ["shoulders", "triceps"], "compound", 3, 10, 50, 7),
                        WorkoutExercise("Incline DB Press", ["chest", "shoulders"], "compound", 3, 10, 30, 7),
                        WorkoutExercise("Lateral Raises", ["shoulders"], "isolation", 3, 15, 12, 7),
                        WorkoutExercise("Tricep Pushdowns", ["triceps"], "isolation", 3, 12, 25, 7),
                    ]
                elif day == 1:  # Pull
                    exercises = [
                        WorkoutExercise("Deadlifts", ["back", "hamstrings", "glutes"], "compound", 3, 5, 100, 8),
                        WorkoutExercise("Pull-ups", ["lats", "biceps"], "compound", 3, 8, 0, 7),
                        WorkoutExercise("Barbell Rows", ["lats", "biceps", "lower_back"], "compound", 4, 10, 60, 7),
                        WorkoutExercise("Face Pulls", ["shoulders", "traps"], "isolation", 3, 15, 20, 7),
                        WorkoutExercise("Bicep Curls", ["biceps"], "isolation", 3, 12, 15, 7),
                    ]
                elif day == 2:  # Legs
                    exercises = [
                        WorkoutExercise("Squats", ["quads", "glutes", "hamstrings"], "compound", 4, 8, 90, 8),
                        WorkoutExercise("Romanian Deadlifts", ["hamstrings", "glutes"], "compound", 3, 10, 70, 7),
                        WorkoutExercise("Leg Press", ["quads", "glutes"], "compound", 3, 12, 150, 7),
                        WorkoutExercise("Leg Curls", ["hamstrings"], "isolation", 3, 12, 40, 7),
                        WorkoutExercise("Calf Raises", ["calves"], "isolation", 4, 15, 60, 7),
                    ]
                else:  # Upper
                    exercises = [
                        WorkoutExercise("Incline Bench", ["chest", "shoulders"], "compound", 3, 10, 60, 7),
                        WorkoutExercise("Cable Rows", ["lats", "biceps"], "compound", 3, 12, 55, 7),
                        WorkoutExercise("Dumbbell Press", ["shoulders"], "compound", 3, 10, 25, 7),
                        WorkoutExercise("Lat Pulldowns", ["lats"], "compound", 3, 12, 50, 7),
                        WorkoutExercise("Tricep Extensions", ["triceps"], "isolation", 3, 12, 15, 7),
                        WorkoutExercise("Hammer Curls", ["biceps", "forearms"], "isolation", 3, 12, 15, 7),
                    ]

                workout = Workout(
                    id=str(uuid.uuid4())[:8],
                    user_id="default",
                    name=f"Week {week+1} Day {day+1}",
                    workout_type="strength",
                    start_time=workout_date,
                    exercises=exercises,
                )
                workout.calculate_stats()
                workouts.append(workout)

        return workouts

    def _calculate_weekly_adaptations(self, workout_plan: List[Workout], weeks: int) -> Dict:
        """Calculate adaptations for each week"""
        adaptations = {}

        # Group workouts by week
        weekly_workouts = {w: [] for w in range(1, weeks + 1)}
        for workout in workout_plan:
            # Assume workouts are in order
            week = min(len(adaptations) + 1, weeks)
            weekly_workouts[week].append(workout)

        for week in range(1, weeks + 1):
            workouts = weekly_workouts[week]

            total_muscle_gain = 0
            total_fat_loss = 0

            for workout in workouts:
                analysis = self.analyze_workout(workout, User(id="temp", email="", name="", gender="other"))
                total_muscle_gain += sum(analysis.long_term_adaptation.muscle_gain_rate_per_week_kg.values())
                total_fat_loss += analysis.long_term_adaptation.fat_burn_per_session_kg

            adaptations[week] = {
                'muscle_gain': total_muscle_gain,
                'fat_loss': total_fat_loss,
            }

        return adaptations

    def _adjust_betas_for_composition(self, base_betas: np.ndarray,
                                       muscle_gain: float, fat_loss: float,
                                       week: int) -> np.ndarray:
        """Adjust SMPL betas based on body composition changes"""
        adjusted = base_betas.copy()

        # Beta 0: Overall size (weight change)
        weight_change = muscle_gain - fat_loss
        adjusted[0] += weight_change * 0.02

        # Muscle distribution affects other betas
        adjusted[4] += muscle_gain * 0.05  # Arms
        adjusted[5] += muscle_gain * 0.08  # Legs
        adjusted[6] += muscle_gain * 0.04  # Chest
        adjusted[7] += muscle_gain * 0.03  # Hips

        return np.clip(adjusted, -3, 3)

    def _estimate_measurements(self, weight: float, body_fat: float,
                                muscle_mass: float) -> Dict[str, float]:
        """Estimate body measurements from composition"""
        # Simplified estimation formulas
        lean_mass = weight * (1 - body_fat / 100)

        return {
            'chest_cm': 90 + (lean_mass - 50) * 0.8,
            'waist_cm': 75 + (weight - 70) * 0.4 + body_fat * 0.3,
            'hips_cm': 90 + (weight - 70) * 0.5,
            'arms_cm': 32 + (lean_mass - 50) * 0.15,
            'thighs_cm': 55 + (weight - 70) * 0.4,
        }

    def log_weight(self, user: User, weight_kg: float,
                   body_fat_pct: Optional[float] = None,
                   measured_at: Optional[datetime] = None) -> BodyMeasurement:
        """
        Log user weight and update avatar.

        Args:
            user: The user
            weight_kg: Weight in kg
            body_fat_pct: Optional body fat percentage
            measured_at: Optional measurement timestamp

        Returns:
            BodyMeasurement record
        """
        measurement = BodyMeasurement(
            id=str(uuid.uuid4())[:8],
            user_id=user.id,
            weight_kg=weight_kg,
            body_fat_pct=body_fat_pct,
            measured_at=measured_at or datetime.now(),
        )

        # Calculate muscle mass if body fat known
        if body_fat_pct:
            fat_mass = weight_kg * (body_fat_pct / 100)
            measurement.muscle_mass_kg = (weight_kg - fat_mass) * 0.45  # Simplified

            # Calculate BMI if height known
            if user.height_cm:
                measurement.bmi = weight_kg / ((user.height_cm / 100) ** 2)

        # Update user current stats
        user.current_weight_kg = weight_kg
        if body_fat_pct:
            user.current_body_fat_pct = body_fat_pct
            user.current_muscle_mass_kg = measurement.muscle_mass_kg

        # Save to database
        db.save_measurement(measurement)
        db.save_user(user)

        # Create progress entry
        entry = ProgressEntry(
            id=str(uuid.uuid4())[:8],
            user_id=user.id,
            entry_type='weight',
            value=weight_kg,
            unit='kg',
            recorded_at=measurement.measured_at,
        )
        db.save_progress_entry(entry)

        return measurement

    def log_workout(self, user: User, workout: Workout) -> WorkoutAnalysis:
        """
        Log a workout and generate analysis.

        Args:
            user: The user
            workout: The workout to log

        Returns:
            Complete workout analysis
        """
        workout.user_id = user.id
        workout.end_time = workout.end_time or datetime.now()
        workout.calculate_stats()

        # Save workout
        db.save_workout(workout)

        # Analyze
        analysis = self.analyze_workout(workout, user)

        # Create progress entry
        entry = ProgressEntry(
            id=str(uuid.uuid4())[:8],
            user_id=user.id,
            entry_type='workout',
            value=workout.total_volume,
            unit='kg',
            notes=f"{len(workout.exercises)} exercises",
        )
        db.save_progress_entry(entry)

        return analysis


# Singleton instance
workout_engine = WorkoutEngine()


if __name__ == "__main__":
    print("Workout Engine Service")
    print("=" * 60)
    print("\nThis service processes workouts and calculates predictions.")
    print("Import and use WorkoutEngine class in your application.")
    print("\nExample:")
    print("  from backend.services.workout_engine import workout_engine")
    print("  analysis = workout_engine.log_workout(user, workout)")
