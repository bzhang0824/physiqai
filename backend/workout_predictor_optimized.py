"""
PhysiqAI Optimized Workout Predictor
=====================================
Production-ready ML model with improved accuracy, validation, and caching.
"""

import json
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
from functools import lru_cache
import logging
import hashlib
import warnings
warnings.filterwarnings('ignore')

from sklearn.model_selection import KFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.ensemble import GradientBoostingRegressor

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class UserProfile:
    """Enhanced user profile with all relevant features"""
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

    @property
    def lean_mass_lbs(self) -> float:
        return self.weight_lbs * (1 - self.body_fat_pct / 100)

    @property
    def bmi(self) -> float:
        weight_kg = self.weight_lbs * 0.453592
        height_m = self.height_inches * 0.0254
        return weight_kg / (height_m ** 2)

    @property
    def ffmi(self) -> float:
        lean_mass_kg = self.lean_mass_lbs * 0.453592
        height_m = self.height_inches * 0.0254
        return lean_mass_kg / (height_m ** 2)

    @property
    def experience_level(self) -> str:
        if self.training_years < 1:
            return 'beginner'
        elif self.training_years < 3:
            return 'intermediate'
        else:
            return 'advanced'

    def to_feature_vector(self) -> np.ndarray:
        gender_enc = 1 if self.gender.lower() == 'male' else 0
        body_type_map = {'ectomorph': 0, 'mesomorph': 1, 'endomorph': 2}
        body_type_enc = body_type_map.get(self.body_type.lower(), 1)
        exp_map = {'beginner': 0, 'intermediate': 1, 'advanced': 2}
        exp_enc = exp_map.get(self.experience_level, 1)

        return np.array([
            self.weight_lbs, self.height_inches, self.age, gender_enc,
            self.body_fat_pct, self.lean_mass_lbs, self.bmi, self.ffmi,
            self.training_years, self.training_frequency,
            self.sleep_hours, self.stress_level, body_type_enc, exp_enc,
            self.training_years * self.training_frequency,
            self.ffmi / (self.age + 20),
            self.sleep_hours / 10,
            (10 - self.stress_level) / 10,
        ])


@dataclass
class WorkoutPlan:
    """Enhanced workout plan"""
    weekly_volume_lbs: float
    sessions_per_week: int
    workout_type: str
    avg_intensity: float = 0.7
    cardio_minutes_per_week: float = 0
    progressive_overload: bool = False
    compound_ratio: float = 0.5

    def to_feature_vector(self) -> np.ndarray:
        workout_type_map = {'full_body': 0, 'upper_lower': 1, 'ppl': 2, 'bro_split': 3, 'phat': 4, 'other': 5}
        type_enc = workout_type_map.get(self.workout_type.lower(), 5)

        return np.array([
            self.weekly_volume_lbs, self.sessions_per_week,
            self.weekly_volume_lbs / max(self.sessions_per_week, 1),
            type_enc, self.avg_intensity, self.cardio_minutes_per_week,
            int(self.progressive_overload), self.compound_ratio,
            np.log1p(self.weekly_volume_lbs),
            self.avg_intensity * self.weekly_volume_lbs,
        ])


@dataclass
class NutritionPlan:
    """Enhanced nutrition plan"""
    daily_calories: float
    daily_protein_g: float
    caloric_surplus: float = 0
    protein_timing: str = 'average'
    meal_frequency: int = 3

    def get_protein_per_lb(self, weight_lbs: float) -> float:
        return self.daily_protein_g / weight_lbs if weight_lbs > 0 else 0

    def to_feature_vector(self, weight_lbs: float) -> np.ndarray:
        protein_per_lb = self.get_protein_per_lb(weight_lbs)
        timing_map = {'poor': 0, 'average': 1, 'optimal': 2}
        timing_enc = timing_map.get(self.protein_timing, 1)

        return np.array([
            self.daily_calories, self.daily_protein_g, self.caloric_surplus,
            protein_per_lb, timing_enc, self.meal_frequency,
            self.caloric_surplus / 500,
            min(protein_per_lb, 2.0) / 2.0,
        ])


@dataclass
class PredictionResult:
    """Enhanced prediction results with confidence intervals"""
    weight_change_lbs: float
    muscle_change_lbs: float
    fat_change_lbs: float
    new_body_fat_pct: float
    new_weight_lbs: float
    new_smpl_betas: List[float]
    confidence: float
    confidence_interval: Tuple[float, float]
    weekly_breakdown: List[Dict[str, float]] = field(default_factory=list)
    feature_importance: Optional[Dict[str, float]] = None
    key_factors: List[str] = field(default_factory=list)

    def summary(self) -> str:
        return f"""
╔══════════════════════════════════════════════════════════════╗
║            PHYSIQUE PREDICTION RESULTS (Optimized)             ║
╠══════════════════════════════════════════════════════════════╣
║  Weight Change:     {self.weight_change_lbs:+.1f} lbs    [{self.confidence_interval[0]:+.1f} to {self.confidence_interval[1]:+.1f}]         ║
║  New Weight:        {self.new_weight_lbs:.1f} lbs                                   ║
║  Muscle Change:     {self.muscle_change_lbs:+.1f} lbs                               ║
║  Fat Change:        {self.fat_change_lbs:+.1f} lbs                                  ║
║  New Body Fat:      {self.new_body_fat_pct:.1f}%                                    ║
║  Confidence:        {self.confidence*100:.0f}%                                      ║
╚══════════════════════════════════════════════════════════════╝
Key Factors: {', '.join(self.key_factors) if self.key_factors else 'Standard progression'}
"""


class PhysiquePredictorModel:
    """Machine learning model for physique prediction using gradient boosting"""

    def __init__(self):
        self.models = {'weight': None, 'muscle': None, 'fat': None}
        self.is_trained = False
        self.cv_scores = {}

    def _get_model(self, target: str):
        if HAS_XGBOOST:
            return xgb.XGBRegressor(
                n_estimators=100, max_depth=6, learning_rate=0.1,
                subsample=0.8, colsample_bytree=0.8, random_state=42, n_jobs=-1
            )
        else:
            return GradientBoostingRegressor(
                n_estimators=100, max_depth=5, learning_rate=0.1,
                subsample=0.8, random_state=42
            )

    def _create_feature_matrix(self, users, workouts, nutritions, weeks):
        features = []
        for user, workout, nutrition, week in zip(users, workouts, nutritions, weeks):
            user_vec = user.to_feature_vector()
            workout_vec = workout.to_feature_vector()
            nutrition_vec = nutrition.to_feature_vector(user.weight_lbs)
            combined = np.concatenate([user_vec, workout_vec, nutrition_vec, [week, week**2]])
            features.append(combined)
        return np.array(features)

    def train(self, users, workouts, nutritions, weeks, targets, validate=True):
        X = self._create_feature_matrix(users, workouts, nutritions, weeks)
        X_scaled = StandardScaler().fit_transform(X)

        metrics = {}
        for target_name in ['weight', 'muscle', 'fat']:
            y = targets[target_name]

            if validate and len(y) >= 10:
                kf = KFold(n_splits=min(5, len(y)), shuffle=True, random_state=42)
                cv_mae = -cross_val_score(self._get_model(target_name), X_scaled, y, cv=kf, scoring='neg_mean_absolute_error')
                cv_r2 = cross_val_score(self._get_model(target_name), X_scaled, y, cv=kf, scoring='r2')
                self.cv_scores[target_name] = {'mae_mean': cv_mae.mean(), 'mae_std': cv_mae.std(), 'r2_mean': cv_r2.mean()}
                logger.info(f"CV {target_name}: MAE={cv_mae.mean():.2f}±{cv_mae.std():.2f}, R²={cv_r2.mean():.3f}")

            model = self._get_model(target_name)
            model.fit(X_scaled, y)
            self.models[target_name] = model
            y_pred = model.predict(X_scaled)
            metrics[f'{target_name}_mae'] = mean_absolute_error(y, y_pred)
            metrics[f'{target_name}_r2'] = r2_score(y, y_pred)

        self.is_trained = True
        return metrics

    def predict(self, user, workout, nutrition, weeks):
        if not self.is_trained:
            raise RuntimeError("Model must be trained before prediction")

        X = self._create_feature_matrix([user], [workout], [nutrition], [weeks])
        X_scaled = StandardScaler().fit_transform(X)

        predictions = {}
        for target_name in ['weight', 'muscle', 'fat']:
            predictions[target_name] = self.models[target_name].predict(X_scaled)[0]

        if 'weight' in self.cv_scores:
            mae = self.cv_scores['weight']['mae_mean']
            predictions['confidence_interval'] = (predictions['weight'] - 1.96 * mae, predictions['weight'] + 1.96 * mae)
        else:
            predictions['confidence_interval'] = (predictions['weight'] * 0.7, predictions['weight'] * 1.3)

        return predictions

    def get_feature_importance(self):
        importance = {}
        for target_name, model in self.models.items():
            if model is not None and hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
                importance[target_name] = {f'feature_{i}': float(imp) for i, imp in enumerate(importances[:10])}
        return importance


class SyntheticDataGenerator:
    """Generate realistic training data based on exercise science"""

    @staticmethod
    def generate_training_data(n_samples: int = 1000):
        np.random.seed(42)
        users, workouts, nutritions, weeks_list = [], [], [], []
        targets = {'weight': [], 'muscle': [], 'fat': []}

        for _ in range(n_samples):
            gender = np.random.choice(['male', 'female'])
            if gender == 'male':
                weight = np.random.normal(180, 30)
                height = np.random.normal(70, 3)
                bf = np.random.beta(2, 5) * 30 + 8
            else:
                weight = np.random.normal(150, 25)
                height = np.random.normal(65, 2.5)
                bf = np.random.beta(2, 4) * 25 + 15

            user = UserProfile(
                weight_lbs=max(100, weight), height_inches=max(60, height),
                age=np.random.randint(18, 55), gender=gender,
                body_fat_pct=np.clip(bf, 5, 50),
                training_years=min(np.random.exponential(2), 15),
                training_frequency=np.random.choice([2, 3, 4, 5, 6], p=[0.1, 0.3, 0.35, 0.2, 0.05]),
                sleep_hours=np.clip(np.random.normal(7, 1), 5, 10),
                stress_level=np.random.randint(1, 10),
                body_type=np.random.choice(['ectomorph', 'mesomorph', 'endomorph'])
            )

            workout = WorkoutPlan(
                weekly_volume_lbs=np.random.lognormal(9.5, 0.5),
                sessions_per_week=np.random.choice([3, 4, 5, 6]),
                workout_type=np.random.choice(['ppl', 'upper_lower', 'full_body', 'bro_split']),
                avg_intensity=np.clip(np.random.beta(3, 2), 0.5, 0.95),
                cardio_minutes_per_week=np.random.exponential(60),
                progressive_overload=np.random.random() > 0.5,
                compound_ratio=np.random.beta(2, 2)
            )

            surplus = np.random.normal(0, 400)
            nutrition = NutritionPlan(
                daily_calories=2500 + surplus,
                daily_protein_g=weight * np.random.uniform(0.6, 1.2),
                caloric_surplus=surplus,
                protein_timing=np.random.choice(['poor', 'average', 'optimal'], p=[0.2, 0.5, 0.3]),
                meal_frequency=np.random.choice([2, 3, 4, 5])
            )

            weeks = np.random.choice([4, 8, 12, 16, 20, 24])

            exp_mult = {'beginner': 1.0, 'intermediate': 0.5, 'advanced': 0.25}[user.experience_level]
            base_muscle_rate = 0.5 if gender == 'male' else 0.25
            volume_factor = min(workout.weekly_volume_lbs / 10000, 1.5)
            protein_factor = min(nutrition.get_protein_per_lb(weight) / 0.8, 1.2)

            weekly_muscle = base_muscle_rate * exp_mult * volume_factor * protein_factor
            if surplus < -200:
                weekly_muscle *= 0.5
            total_muscle = weekly_muscle * weeks * np.random.uniform(0.7, 1.3)

            if surplus > 0:
                weekly_fat = (surplus * 7) / 3500 * np.random.uniform(0.3, 0.7)
            else:
                weekly_fat = (surplus * 7) / 3500 * np.random.uniform(0.8, 1.2)
            total_fat = weekly_fat * weeks

            users.append(user)
            workouts.append(workout)
            nutritions.append(nutrition)
            weeks_list.append(weeks)
            targets['weight'].append(total_muscle + total_fat)
            targets['muscle'].append(total_muscle)
            targets['fat'].append(total_fat)

        return users, workouts, nutritions, weeks_list, {k: np.array(v) for k, v in targets.items()}


class OptimizedPredictor:
    """Production-ready predictor with caching and validation"""

    MIN_BODY_FAT_MALE = 8.0
    MIN_BODY_FAT_FEMALE = 15.0
    MAX_MUSCLE_GAIN_MALE = 0.5
    MAX_MUSCLE_GAIN_FEMALE = 0.25

    def __init__(self, cache_size: int = 128):
        self.ml_model = PhysiquePredictorModel()
        self.cache_size = cache_size
        self._cache = {}
        self._train_model()

    def _train_model(self):
        logger.info("Training ML model on synthetic data...")
        generator = SyntheticDataGenerator()
        users, workouts, nutritions, weeks, targets = generator.generate_training_data(2000)
        metrics = self.ml_model.train(users, workouts, nutritions, weeks, targets)
        logger.info(f"Training complete. MAE: {metrics.get('weight_mae', 0):.2f}, R²: {metrics.get('weight_r2', 0):.3f}")

    def _get_cache_key(self, user, workout, nutrition, weeks):
        key_data = f"{user.weight_lbs}:{user.body_fat_pct}:{user.training_years}:{workout.weekly_volume_lbs}:{nutrition.caloric_surplus}:{weeks}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def predict(self, user, workout, nutrition, weeks):
        cache_key = self._get_cache_key(user, workout, nutrition, weeks)
        if cache_key in self._cache:
            return self._cache[cache_key]

        ml_pred = self.ml_model.predict(user, workout, nutrition, weeks)

        weight_change = self._constrain_weight_change(ml_pred['weight'], user, nutrition, weeks)
        muscle_change = self._constrain_muscle_gain(ml_pred['muscle'], user, workout, nutrition, weeks)
        fat_change = self._constrain_fat_change(ml_pred['fat'], user, nutrition, weeks)
        weight_change = muscle_change + fat_change

        new_weight = user.weight_lbs + weight_change
        new_fat_mass = user.weight_lbs * (user.body_fat_pct / 100) + fat_change
        new_body_fat_pct = (new_fat_mass / new_weight) * 100 if new_weight > 0 else user.body_fat_pct

        min_bf = self.MIN_BODY_FAT_MALE if user.gender.lower() == 'male' else self.MIN_BODY_FAT_FEMALE
        if new_body_fat_pct < min_bf:
            target_fat_mass = new_weight * (min_bf / 100)
            fat_change = target_fat_mass - (user.weight_lbs * (user.body_fat_pct / 100))
            muscle_change = weight_change - fat_change
            new_body_fat_pct = min_bf

        new_betas = self._calculate_smpl_changes(user, muscle_change, fat_change, workout)
        confidence = self._calculate_confidence(user, workout, nutrition)
        weekly_breakdown = self._generate_weekly_breakdown(user, muscle_change, fat_change, weeks)
        key_factors = self._identify_key_factors(user, workout, nutrition)

        result = PredictionResult(
            weight_change_lbs=weight_change, muscle_change_lbs=muscle_change,
            fat_change_lbs=fat_change, new_body_fat_pct=new_body_fat_pct,
            new_weight_lbs=new_weight, new_smpl_betas=new_betas,
            confidence=confidence, confidence_interval=ml_pred.get('confidence_interval', (weight_change * 0.7, weight_change * 1.3)),
            weekly_breakdown=weekly_breakdown, key_factors=key_factors
        )

        if len(self._cache) >= self.cache_size:
            self._cache.pop(next(iter(self._cache)))
        self._cache[cache_key] = result

        return result

    def _constrain_weight_change(self, pred, user, nutrition, weeks):
        max_loss_per_week, max_gain_per_week = 2.0, 1.5
        weekly_change = pred / weeks if weeks > 0 else 0
        if weekly_change < 0:
            weekly_change = max(weekly_change, -max_loss_per_week)
        else:
            weekly_change = min(weekly_change, max_gain_per_week)
        return weekly_change * weeks

    def _constrain_muscle_gain(self, pred, user, workout, nutrition, weeks):
        max_weekly = self.MAX_MUSCLE_GAIN_MALE if user.gender.lower() == 'male' else self.MAX_MUSCLE_GAIN_FEMALE
        exp_mult = {'beginner': 1.0, 'intermediate': 0.5, 'advanced': 0.25}[user.experience_level]
        volume_factor = min(workout.weekly_volume_lbs / 10000, 1.0)
        protein_per_lb = nutrition.daily_protein_g / user.weight_lbs if user.weight_lbs > 0 else 0
        protein_factor = min(protein_per_lb / 0.8, 1.0) if nutrition.daily_protein_g > 0 else 0.5
        surplus_factor = 0.5 if nutrition.caloric_surplus <= 0 else min(nutrition.caloric_surplus / 300, 1.0)
        max_gain = max_weekly * exp_mult * volume_factor * protein_factor * surplus_factor * weeks
        return np.clip(pred, 0, max_gain)

    def _constrain_fat_change(self, pred, user, nutrition, weeks):
        weekly_caloric_impact = nutrition.caloric_surplus * 7
        if weekly_caloric_impact < 0:
            max_loss = -weekly_caloric_impact * weeks / 3500 * 1.1
            return np.clip(pred, max_loss, 0)
        else:
            min_gain = weekly_caloric_impact * weeks / 3500 * 0.3
            max_gain = weekly_caloric_impact * weeks / 3500 * 0.7
            return np.clip(pred, min_gain, max_gain)

    def _calculate_smpl_changes(self, user, muscle_change, fat_change, workout):
        new_betas = user.smpl_betas.copy() if user.smpl_betas else [0.0] * 10
        while len(new_betas) < 10:
            new_betas.append(0.0)
        new_betas = new_betas[:10]

        total_change = muscle_change + fat_change
        new_betas[0] += total_change * 0.02
        if fat_change < 0:
            new_betas[0] += fat_change * 0.01

        workout_type = workout.workout_type.lower()
        if 'ppl' in workout_type or 'push' in workout_type:
            new_betas[3] += muscle_change * 0.015
            new_betas[4] += muscle_change * 0.02
            new_betas[5] += muscle_change * 0.025
            new_betas[6] += muscle_change * 0.015
        elif 'upper' in workout_type:
            new_betas[3] += muscle_change * 0.02
            new_betas[4] += muscle_change * 0.025
            new_betas[6] += muscle_change * 0.02
            new_betas[5] += muscle_change * 0.015
        elif 'bro' in workout_type:
            new_betas[3] += muscle_change * 0.02
            new_betas[4] += muscle_change * 0.03
            new_betas[5] += muscle_change * 0.02
            new_betas[6] += muscle_change * 0.025
            new_betas[7] += muscle_change * 0.01
        else:
            new_betas[3] += muscle_change * 0.015
            new_betas[4] += muscle_change * 0.015
            new_betas[5] += muscle_change * 0.02
            new_betas[6] += muscle_change * 0.01

        if fat_change < 0:
            new_betas[2] -= fat_change * 0.005

        return [round(b, 4) for b in new_betas]

    def _calculate_confidence(self, user, workout, nutrition):
        confidence = 0.7
        if user.smpl_betas and len(user.smpl_betas) >= 10:
            confidence += 0.05
        if workout.weekly_volume_lbs > 0:
            confidence += 0.05
        if nutrition.daily_protein_g > 50:
            confidence += 0.05
        if user.experience_level == 'beginner':
            confidence += 0.05
        return min(0.95, confidence)

    def _generate_weekly_breakdown(self, user, total_muscle, total_fat, weeks):
        breakdown = []
        weekly_muscle = total_muscle / weeks if weeks > 0 else 0
        weekly_fat = total_fat / weeks if weeks > 0 else 0

        for week in range(1, weeks + 1):
            progress = week / weeks
            diminishing = 1.0 - (progress * 0.3)
            beginner_boost = 1.3 if user.experience_level == 'beginner' and week <= 4 else 1.0

            week_muscle = weekly_muscle * diminishing * beginner_boost
            week_fat = weekly_fat

            breakdown.append({
                'week': week,
                'muscle_gain': round(week_muscle, 3),
                'fat_change': round(week_fat, 3),
                'weight_change': round(week_muscle + week_fat, 3),
                'cumulative_muscle': round(week_muscle * week, 2),
                'cumulative_weight': round((week_muscle + week_fat) * week, 2)
            })
        return breakdown

    def _identify_key_factors(self, user, workout, nutrition):
        factors = []
        if user.experience_level == 'beginner':
            factors.append("Beginner gains potential")
        if nutrition.caloric_surplus > 300:
            factors.append("High caloric surplus")
        elif nutrition.caloric_surplus < -300:
            factors.append("Significant caloric deficit")
        if workout.progressive_overload:
            factors.append("Progressive overload")
        protein_per_lb = nutrition.daily_protein_g / user.weight_lbs if user.weight_lbs > 0 else 0
        if protein_per_lb >= 0.8:
            factors.append("Optimal protein intake")
        if workout.weekly_volume_lbs > 15000:
            factors.append("High training volume")
        if user.sleep_hours < 6:
            factors.append("Sleep deficit (recovery concern)")
        return factors if factors else ['Standard progression']

    def get_cv_scores(self):
        return self.ml_model.cv_scores

    def get_feature_importance(self):
        return self.ml_model.get_feature_importance()


def run_test_suite():
    """Run comprehensive test suite"""
    print("=" * 70)
    print("PHYSIQAI OPTIMIZED PREDICTOR - TEST SUITE")
    print("=" * 70)

    predictor = OptimizedPredictor()
    results = []

    print("\n📊 TEST CASE 1: Beginner Male - Lean Bulk")
    print("-" * 70)
    user1 = UserProfile(
        weight_lbs=160, height_inches=70, age=22, gender='male', body_fat_pct=12,
        training_years=0.5, training_frequency=4, sleep_hours=8, stress_level=3,
        body_type='ectomorph', smpl_betas=[0.0] * 10
    )
    workout1 = WorkoutPlan(
        weekly_volume_lbs=15000, sessions_per_week=4, workout_type='ppl',
        avg_intensity=0.8, progressive_overload=True, compound_ratio=0.7
    )
    nutrition1 = NutritionPlan(
        daily_calories=3200, daily_protein_g=180, caloric_surplus=500,
        protein_timing='optimal', meal_frequency=4
    )
    result1 = predictor.predict(user1, workout1, nutrition1, weeks=12)
    print(result1.summary())
    results.append(('Beginner Male Bulk', result1))

    print("\n📊 TEST CASE 2: Intermediate Female - Cutting Phase")
    print("-" * 70)
    user2 = UserProfile(
        weight_lbs=145, height_inches=65, age=28, gender='female', body_fat_pct=25,
        training_years=2.5, training_frequency=5, sleep_hours=7, stress_level=6,
        body_type='mesomorph', smpl_betas=[0.0] * 10
    )
    workout2 = WorkoutPlan(
        weekly_volume_lbs=12000, sessions_per_week=5, workout_type='upper_lower',
        avg_intensity=0.75, cardio_minutes_per_week=120, compound_ratio=0.6
    )
    nutrition2 = NutritionPlan(
        daily_calories=1700, daily_protein_g=130, caloric_surplus=-400,
        protein_timing='average', meal_frequency=3
    )
    result2 = predictor.predict(user2, workout2, nutrition2, weeks=16)
    print(result2.summary())
    results.append(('Intermediate Female Cut', result2))

    print("\n📊 TEST CASE 3: Advanced Male - Body Recomposition")
    print("-" * 70)
    user3 = UserProfile(
        weight_lbs=190, height_inches=72, age=35, gender='male', body_fat_pct=18,
        training_years=8, training_frequency=6, sleep_hours=6.5, stress_level=7,
        body_type='endomorph', smpl_betas=[0.0] * 10
    )
    workout3 = WorkoutPlan(
        weekly_volume_lbs=20000, sessions_per_week=6, workout_type='phat',
        avg_intensity=0.85, progressive_overload=True, compound_ratio=0.75
    )
    nutrition3 = NutritionPlan(
        daily_calories=2600, daily_protein_g=200, caloric_surplus=-200,
        protein_timing='optimal', meal_frequency=5
    )
    result3 = predictor.predict(user3, workout3, nutrition3, weeks=20)
    print(result3.summary())
    results.append(('Advanced Male Recomp', result3))

    print("\n📊 TEST CASE 4: Edge Case - Significant Weight Loss")
    print("-" * 70)
    user4 = UserProfile(
        weight_lbs=280, height_inches=68, age=40, gender='male', body_fat_pct=35,
        training_years=0, training_frequency=3, sleep_hours=6, stress_level=8,
        body_type='endomorph', smpl_betas=[0.0] * 10
    )
    workout4 = WorkoutPlan(
        weekly_volume_lbs=8000, sessions_per_week=3, workout_type='full_body',
        avg_intensity=0.65, cardio_minutes_per_week=180, compound_ratio=0.8
    )
    nutrition4 = NutritionPlan(
        daily_calories=2200, daily_protein_g=200, caloric_surplus=-800,
        protein_timing='poor', meal_frequency=2
    )
    result4 = predictor.predict(user4, workout4, nutrition4, weeks=24)
    print(result4.summary())
    results.append(('Extreme Weight Loss', result4))

    print("\n" + "=" * 70)
    print("CROSS-VALIDATION SCORES")
    print("=" * 70)
    cv_scores = predictor.get_cv_scores()
    for target, scores in cv_scores.items():
        print(f"\n{target.upper()}:")
        print(f"  MAE: {scores['mae_mean']:.2f} ± {scores['mae_std']:.2f} lbs")
        print(f"  R²:  {scores['r2_mean']:.3f}")

    print("\n" + "=" * 70)
    print("TEST SUITE COMPLETE")
    print("=" * 70)

    return results, cv_scores


if __name__ == "__main__":
    run_test_suite()
