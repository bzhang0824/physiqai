#!/usr/bin/env python3
"""
body_mapper.py - Body Parameters to SMPL Mapping

Maps high-level body parameters (weight, muscle %, body fat %, measurements)
to SMPL shape parameters (betas).
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json


@dataclass
class BodyState:
    """
    Represents a complete body state with all parameters.
    """
    # Core parameters
    weight: float  # lbs
    muscle_pct: float  # 0-100
    fat_pct: float  # 0-100
    height: float = 70.0  # inches (default 5'10")

    # Measurements (inches)
    measurements: Dict[str, float] = field(default_factory=dict)

    # Computed properties
    betas: Optional[np.ndarray] = None  # SMPL shape params

    def __post_init__(self):
        """Validate and set defaults"""
        self.weight = max(80, min(400, self.weight))
        self.muscle_pct = max(5, min(70, self.muscle_pct))
        self.fat_pct = max(3, min(60, self.fat_pct))

        # Default measurements if not provided
        defaults = {
            'chest': 40.0,
            'waist': 32.0,
            'hips': 38.0,
            'shoulders': 44.0,
            'arms': 13.0,
            'thighs': 22.0,
            'calves': 15.0
        }

        for key, val in defaults.items():
            if key not in self.measurements:
                self.measurements[key] = val

    @property
    def bmi(self) -> float:
        """Calculate BMI"""
        weight_kg = self.weight * 0.453592
        height_m = self.height * 0.0254
        return weight_kg / (height_m ** 2)

    @property
    def lean_mass(self) -> float:
        """Calculate lean body mass in lbs"""
        return self.weight * (1 - self.fat_pct / 100)

    @property
    def ffmi(self) -> float:
        """Calculate Fat-Free Mass Index"""
        lean_mass_kg = self.lean_mass * 0.453592
        height_m = self.height * 0.0254
        return lean_mass_kg / (height_m ** 2)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            'weight': self.weight,
            'muscle_pct': self.muscle_pct,
            'fat_pct': self.fat_pct,
            'height': self.height,
            'measurements': self.measurements,
            'bmi': self.bmi,
            'lean_mass': self.lean_mass,
            'ffmi': self.ffmi
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'BodyState':
        """Create from dictionary"""
        return cls(
            weight=data['weight'],
            muscle_pct=data['muscle_pct'],
            fat_pct=data['fat_pct'],
            height=data.get('height', 70.0),
            measurements=data.get('measurements', {})
        )


class BodyToSMPLMapper:
    """
    Maps BodyState to SMPL beta parameters.

    Uses learned mappings to convert intuitive body parameters
    into SMPL shape coefficients.
    """

    def __init__(self, gender: str = 'neutral', model_path: Optional[Path] = None):
        """
        Initialize mapper.

        Args:
            gender: 'male', 'female', or 'neutral'
            model_path: Optional path to trained mapping weights
        """
        self.gender = gender

        # Load or initialize mapping weights
        if model_path and model_path.exists():
            self._load_weights(model_path)
        else:
            self._init_default_weights()

    def _init_default_weights(self):
        """
        Initialize default mapping weights based on SMPL beta semantics.

        SMPL betas roughly correspond to:
        β₀: Overall scale/size
        β₁: Height vs width ratio
        β₂: Upper body proportion
        β₃: Lower body proportion
        β₄: Body fat distribution
        β₅-β₉: Fine shape details
        """
        # Weight affects primarily β₀ (scale) and slightly β₂, β₃ (proportions)
        self.weight_to_beta = np.array([0.75, 0.05, 0.10, 0.05, 0.03, 0.01, 0.01, 0, 0, 0])

        # Muscle affects β₀ (slightly), β₂ (upper), β₃ (lower), β₅+ (details)
        self.muscle_to_beta = np.array([0.15, 0.05, 0.35, 0.30, 0.05, 0.05, 0.03, 0.01, 0.01, 0])

        # Fat affects β₀, β₁ (width), β₄ (fat distribution)
        self.fat_to_beta = np.array([0.55, 0.25, 0.05, 0.05, 0.08, 0.01, 0.01, 0, 0, 0])

        # Measurement adjustment weights (which betas affect which measurements)
        # Rows: measurements, Cols: betas
        self.measurement_jacobian = np.zeros((7, 10))

        # Approximate relationships
        # Chest affected by β₀, β₂
        self.measurement_jacobian[0, [0, 2]] = [0.4, 0.6]

        # Waist affected by β₀, β₁, β₄
        self.measurement_jacobian[1, [0, 1, 4]] = [0.3, 0.4, 0.3]

        # Hips affected by β₀, β₃, β₄
        self.measurement_jacobian[2, [0, 3, 4]] = [0.3, 0.5, 0.2]

        # Shoulders affected by β₀, β₂
        self.measurement_jacobian[3, [0, 2]] = [0.3, 0.7]

        # Arms affected by β₀, β₂, β₅
        self.measurement_jacobian[4, [0, 2, 5]] = [0.3, 0.5, 0.2]

        # Thighs affected by β₀, β₃
        self.measurement_jacobian[5, [0, 3]] = [0.4, 0.6]

        # Calves affected by β₀, β₃, β₆
        self.measurement_jacobian[6, [0, 3, 6]] = [0.3, 0.5, 0.2]

    def _load_weights(self, path: Path):
        """Load trained mapping weights from file"""
        with open(path) as f:
            data = json.load(f)

        self.weight_to_beta = np.array(data['weight_to_beta'])
        self.muscle_to_beta = np.array(data['muscle_to_beta'])
        self.fat_to_beta = np.array(data['fat_to_beta'])
        self.measurement_jacobian = np.array(data['measurement_jacobian'])

    def save_weights(self, path: Path):
        """Save mapping weights to file"""
        data = {
            'weight_to_beta': self.weight_to_beta.tolist(),
            'muscle_to_beta': self.muscle_to_beta.tolist(),
            'fat_to_beta': self.fat_to_beta.tolist(),
            'measurement_jacobian': self.measurement_jacobian.tolist(),
            'gender': self.gender
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def map_to_betas(self, body_state: BodyState,
                     use_measurements: bool = True) -> np.ndarray:
        """
        Convert BodyState to SMPL betas.

        Args:
            body_state: BodyState instance
            use_measurements: If True, adjust to match measurements

        Returns:
            betas: 10-element SMPL shape parameter vector
        """
        # Normalize inputs (center around typical values)
        # Typical: 180 lbs, 35% muscle, 25% fat
        weight_norm = (body_state.weight - 180) / 100
        muscle_norm = (body_state.muscle_pct - 35) / 35
        fat_norm = (body_state.fat_pct - 25) / 25

        # Linear combination of contributions
        betas = (
            self.weight_to_beta * weight_norm +
            self.muscle_to_beta * muscle_norm +
            self.fat_to_beta * fat_norm
        )

        # Clamp to valid range
        betas = np.clip(betas, -3.0, 3.0)

        # Fine-tune with measurements if provided
        if use_measurements and body_state.measurements:
            betas = self._apply_measurement_constraints(
                betas, body_state.measurements
            )

        return betas

    def _apply_measurement_constraints(self, betas: np.ndarray,
                                       measurements: Dict[str, float],
                                       iterations: int = 5) -> np.ndarray:
        """
        Adjust betas to better match target measurements.

        Uses iterative gradient descent.
        """
        measurement_order = ['chest', 'waist', 'hips', 'shoulders', 'arms', 'thighs', 'calves']
        target = np.array([measurements.get(m, 0) for m in measurement_order])

        # Skip if no measurements
        if np.all(target == 0):
            return betas

        current_betas = betas.copy()
        step_size = 0.1

        for _ in range(iterations):
            # Estimate current measurements from betas
            # This is a simplified model - in practice, would use actual SMPL
            current = self._estimate_measurements_from_betas(current_betas)

            # Compute error
            error = target - current

            # Skip if close enough
            if np.linalg.norm(error) < 0.1:
                break

            # Compute adjustment using Jacobian pseudoinverse
            # Δβ = J⁺ · Δm
            adjustment = self.measurement_jacobian.T @ error
            adjustment = adjustment * step_size / np.linalg.norm(adjustment + 1e-8)

            current_betas += adjustment
            current_betas = np.clip(current_betas, -3.0, 3.0)

        return current_betas

    def _estimate_measurements_from_betas(self, betas: np.ndarray) -> np.ndarray:
        """
        Estimate body measurements from SMPL betas.

        Simplified model for iterative refinement.
        """
        # Base measurements (typical male)
        base = np.array([40, 32, 38, 44, 13, 22, 15])

        # Apply Jacobian to estimate changes
        delta = self.measurement_jacobian @ betas

        return base + delta * 5  # Scale factor

    def map_from_betas(self, betas: np.ndarray, height: float = 70.0) -> BodyState:
        """
        Convert SMPL betas back to BodyState (approximate).

        This is an inverse mapping and will be approximate.
        """
        # Estimate weight from β₀
        weight = 180 + betas[0] * 100

        # Estimate muscle/fat from combination of betas
        # This is heuristic - would need training data for accuracy
        muscle_score = betas[2] * 0.5 + betas[3] * 0.3 + betas[0] * 0.2
        muscle_pct = 35 + muscle_score * 35

        fat_score = betas[0] * 0.6 + betas[1] * 0.3 + betas[4] * 0.1
        fat_pct = 25 + fat_score * 25

        return BodyState(
            weight=weight,
            muscle_pct=np.clip(muscle_pct, 5, 70),
            fat_pct=np.clip(fat_pct, 3, 60),
            height=height
        )

    def get_preset_body(self, preset_name: str) -> BodyState:
        """
        Get preset body configurations.

        Presets: 'skinny', 'average', 'fit', 'muscular', 'overweight', 'obese'
        """
        presets = {
            'skinny': BodyState(weight=130, muscle_pct=20, fat_pct=12),
            'average': BodyState(weight=180, muscle_pct=35, fat_pct=25),
            'fit': BodyState(weight=175, muscle_pct=45, fat_pct=15),
            'muscular': BodyState(weight=200, muscle_pct=55, fat_pct=12),
            'overweight': BodyState(weight=220, muscle_pct=30, fat_pct=35),
            'obese': BodyState(weight=280, muscle_pct=25, fat_pct=45),
        }

        return presets.get(preset_name, presets['average'])

    def create_body_matrix(self, weight_range: Tuple[float, float] = (120, 300),
                          muscle_range: Tuple[float, float] = (15, 60),
                          fat_range: Tuple[float, float] = (8, 45),
                          resolution: int = 5) -> List[BodyState]:
        """
        Create a grid of body states for pre-computation.

        Returns list of BodyStates covering the parameter space.
        """
        bodies = []

        weights = np.linspace(weight_range[0], weight_range[1], resolution)
        muscles = np.linspace(muscle_range[0], muscle_range[1], resolution)
        fats = np.linspace(fat_range[0], fat_range[1], resolution)

        for w in weights:
            for m in muscles:
                for f in fats:
                    # Skip impossible combinations
                    # Muscle % + Fat % should be < ~90%
                    if m + f < 90:
                        bodies.append(BodyState(weight=w, muscle_pct=m, fat_pct=f))

        return bodies


def demo_mapper():
    """Demonstrate body mapping"""
    print("Body Mapper Demo")
    print("=" * 50)

    mapper = BodyToSMPLMapper(gender='male')

    # Test presets
    presets = ['skinny', 'average', 'fit', 'muscular', 'overweight']

    print("\nPreset bodies and their SMPL betas:")
    print("-" * 50)

    for preset in presets:
        body = mapper.get_preset_body(preset)
        betas = mapper.map_to_betas(body)

        print(f"\n{preset.upper()}:")
        print(f"  Weight: {body.weight:.0f} lbs, Muscle: {body.muscle_pct:.0f}%, Fat: {body.fat_pct:.0f}%")
        print(f"  BMI: {body.bmi:.1f}, FFMI: {body.ffmi:.1f}")
        print(f"  Betas: [{', '.join([f'{b:+.2f}' for b in betas[:5]])}, ...]")

    # Test interpolation
    print("\n" + "=" * 50)
    print("\nInterpolation demo (Average → Muscular):")

    start = mapper.get_preset_body('average')
    end = mapper.get_preset_body('muscular')

    for i in range(6):
        t = i / 5
        weight = start.weight + (end.weight - start.weight) * t
        muscle = start.muscle_pct + (end.muscle_pct - start.muscle_pct) * t
        fat = start.fat_pct + (end.fat_pct - start.fat_pct) * t

        body = BodyState(weight=weight, muscle_pct=muscle, fat_pct=fat)
        betas = mapper.map_to_betas(body)

        print(f"  {t*100:.0f}%: β₀={betas[0]:+.2f}, β₁={betas[1]:+.2f}, β₂={betas[2]:+.2f}")


if __name__ == "__main__":
    demo_mapper()
