#!/usr/bin/env python3
"""
vertex_displacement.py - Localized Muscle Displacement

Adds detailed muscle pump and hypertrophy effects on top of SMPL base mesh.
Used for temporary effects (pump) and localized muscle growth visualization.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum


class MuscleGroup(Enum):
    """Major muscle groups for displacement"""
    BICEPS = "biceps"
    TRICEPS = "triceps"
    CHEST = "chest"
    SHOULDERS = "shoulders"
    LATS = "lats"
    ABS = "abs"
    OBLIQUES = "obliques"
    QUADS = "quads"
    HAMSTRINGS = "hamstrings"
    CALVES = "calves"
    GLUTES = "glutes"
    TRAPS = "traps"


@dataclass
class MuscleRegion:
    """Defines a muscle region for displacement"""
    name: str
    vertex_indices: np.ndarray  # Indices of affected vertices
    center: np.ndarray  # Center point (3D)
    radius: float  # Influence radius
    normal_direction: np.ndarray  # Primary displacement direction
    max_displacement: float  # Maximum displacement in meters
    falloff_exponent: float = 2.0  # Gaussian falloff exponent


class MuscleDisplacementSystem:
    """
    Applies localized vertex displacement for muscle effects.

    Two main use cases:
    1. Temporary "pump" effect after workouts
    2. Long-term hypertrophy visualization
    """

    def __init__(self, smpl_faces=None):
        """
        Initialize muscle displacement system.

        Args:
            smpl_faces: SMPL face indices for normal calculation
        """
        self.faces = smpl_faces
        self.regions = self._define_muscle_regions()
        self._vertex_normals_cache = None

    def _define_muscle_regions(self) -> Dict[MuscleGroup, MuscleRegion]:
        """
        Define muscle regions with approximate vertex indices.

        These would be refined with actual SMPL topology analysis.
        """
        regions = {}

        # Biceps (front upper arm)
        regions[MuscleGroup.BICEPS] = MuscleRegion(
            name="Biceps",
            vertex_indices=np.array(list(range(1400, 1500))),  # Placeholder
            center=np.array([0.25, 0.3, 0.05]),
            radius=0.08,
            normal_direction=np.array([0.3, 0, 0.9]),
            max_displacement=0.015,  # 1.5cm max pump
            falloff_exponent=2.0
        )

        # Triceps (back upper arm)
        regions[MuscleGroup.TRICEPS] = MuscleRegion(
            name="Triceps",
            vertex_indices=np.array(list(range(1500, 1600))),
            center=np.array([0.25, 0.3, -0.05]),
            radius=0.08,
            normal_direction=np.array([0.3, 0, -0.9]),
            max_displacement=0.012,
            falloff_exponent=2.0
        )

        # Chest (pectorals)
        regions[MuscleGroup.CHEST] = MuscleRegion(
            name="Chest",
            vertex_indices=np.array(list(range(1200, 1400))),
            center=np.array([0, 0.5, 0.15]),
            radius=0.18,
            normal_direction=np.array([0, 0.2, 0.95]),
            max_displacement=0.020,
            falloff_exponent=1.8
        )

        # Shoulders (deltoids)
        regions[MuscleGroup.SHOULDERS] = MuscleRegion(
            name="Shoulders",
            vertex_indices=np.array(list(range(1000, 1200))),
            center=np.array([0.35, 0.75, 0]),
            radius=0.12,
            normal_direction=np.array([0.9, 0.3, 0]),
            max_displacement=0.018,
            falloff_exponent=2.0
        )

        # Lats (latissimus dorsi)
        regions[MuscleGroup.LATS] = MuscleRegion(
            name="Lats",
            vertex_indices=np.array(list(range(2000, 2200))),
            center=np.array([0.15, 0.4, -0.15]),
            radius=0.15,
            normal_direction=np.array([0.2, 0, -0.95]),
            max_displacement=0.015,
            falloff_exponent=1.8
        )

        # Abs (rectus abdominis)
        regions[MuscleGroup.ABS] = MuscleRegion(
            name="Abs",
            vertex_indices=np.array(list(range(1600, 1800))),
            center=np.array([0, 0.25, 0.12]),
            radius=0.10,
            normal_direction=np.array([0, 0, 0.95]),
            max_displacement=0.010,
            falloff_exponent=2.0
        )

        # Quads (quadriceps)
        regions[MuscleGroup.QUADS] = MuscleRegion(
            name="Quads",
            vertex_indices=np.array(list(range(3000, 3200))),
            center=np.array([0.12, -0.3, 0.10]),
            radius=0.15,
            normal_direction=np.array([0.1, -0.2, 0.95]),
            max_displacement=0.025,
            falloff_exponent=1.8
        )

        # Hamstrings
        regions[MuscleGroup.HAMSTRINGS] = MuscleRegion(
            name="Hamstrings",
            vertex_indices=np.array(list(range(3200, 3400))),
            center=np.array([0.12, -0.35, -0.12]),
            radius=0.14,
            normal_direction=np.array([0.1, -0.2, -0.95]),
            max_displacement=0.020,
            falloff_exponent=1.8
        )

        # Calves (gastrocnemius)
        regions[MuscleGroup.CALVES] = MuscleRegion(
            name="Calves",
            vertex_indices=np.array(list(range(3500, 3700))),
            center=np.array([0.10, -0.75, -0.05]),
            radius=0.08,
            normal_direction=np.array([0, -0.3, -0.9]),
            max_displacement=0.012,
            falloff_exponent=2.0
        )

        # Glutes
        regions[MuscleGroup.GLUTES] = MuscleRegion(
            name="Glutes",
            vertex_indices=np.array(list(range(2200, 2400))),
            center=np.array([0.10, 0, -0.20]),
            radius=0.15,
            normal_direction=np.array([0, 0, -0.95]),
            max_displacement=0.018,
            falloff_exponent=1.8
        )

        # Traps (trapezius)
        regions[MuscleGroup.TRAPS] = MuscleRegion(
            name="Traps",
            vertex_indices=np.array(list(range(800, 1000))),
            center=np.array([0, 0.9, -0.05]),
            radius=0.12,
            normal_direction=np.array([0, 0.5, -0.8]),
            max_displacement=0.010,
            falloff_exponent=2.0
        )

        return regions

    def _calculate_vertex_normals(self, vertices: np.ndarray) -> np.ndarray:
        """
        Calculate vertex normals from mesh.

        Uses face normals averaged to vertices.
        """
        if self._vertex_normals_cache is not None:
            return self._vertex_normals_cache

        if self.faces is None:
            # Return default normals if no faces
            return np.tile(np.array([0, 0, 1]), (len(vertices), 1))

        # Calculate face normals
        v0 = vertices[self.faces[:, 0]]
        v1 = vertices[self.faces[:, 1]]
        v2 = vertices[self.faces[:, 2]]

        face_normals = np.cross(v1 - v0, v2 - v0)
        face_normals = face_normals / (np.linalg.norm(face_normals, axis=1, keepdims=True) + 1e-8)

        # Average to vertices
        vertex_normals = np.zeros_like(vertices)
        for i, face in enumerate(self.faces):
            for j in range(3):
                vertex_normals[face[j]] += face_normals[i]

        # Normalize
        vertex_normals = vertex_normals / (np.linalg.norm(vertex_normals, axis=1, keepdims=True) + 1e-8)

        self._vertex_normals_cache = vertex_normals
        return vertex_normals

    def apply_muscle_pump(self,
                         base_vertices: np.ndarray,
                         muscle_activations: Dict[MuscleGroup, float],
                         time_since_workout: float = 0) -> np.ndarray:
        """
        Apply temporary muscle pump effect.

        Args:
            base_vertices: SMPL mesh vertices (6890, 3)
            muscle_activations: Dict of activation levels (0-1) per muscle group
            time_since_workout: Hours since workout (affects pump decay)

        Returns:
            Displaced vertices with pump effect
        """
        displaced = base_vertices.copy()

        # Pump decays over time (2-3 hour half-life)
        pump_decay = np.exp(-time_since_workout / 2.0)

        # Get current normals
        normals = self._calculate_vertex_normals(base_vertices)

        for muscle, activation in muscle_activations.items():
            if muscle not in self.regions:
                continue

            region = self.regions[muscle]

            # Apply time decay to activation
            effective_activation = activation * pump_decay
            max_disp = region.max_displacement * effective_activation

            if max_disp < 0.001:  # Skip tiny displacements
                continue

            for idx in region.vertex_indices:
                if idx >= len(base_vertices):
                    continue

                vertex = base_vertices[idx]
                normal = normals[idx]

                # Distance from muscle center
                distance = np.linalg.norm(vertex - region.center)

                # Gaussian falloff
                influence = np.exp(-(distance ** region.falloff_exponent) /
                                  (2 * region.radius ** region.falloff_exponent))

                # Displace along vertex normal
                displacement = normal * max_disp * influence
                displaced[idx] += displacement

        return displaced

    def apply_hypertrophy(self,
                         base_vertices: np.ndarray,
                         muscle_growth: Dict[MuscleGroup, float]) -> np.ndarray:
        """
        Apply permanent muscle growth (hypertrophy).

        Similar to pump but represents long-term growth.

        Args:
            base_vertices: SMPL mesh vertices
            muscle_growth: Dict of growth factors (0-1) per muscle group

        Returns:
            Displaced vertices with hypertrophy
        """
        displaced = base_vertices.copy()
        normals = self._calculate_vertex_normals(base_vertices)

        for muscle, growth in muscle_growth.items():
            if muscle not in self.regions or growth <= 0:
                continue

            region = self.regions[muscle]

            # Hypertrophy is more subtle than pump (max 50% of pump)
            max_disp = region.max_displacement * 0.5 * growth

            for idx in region.vertex_indices:
                if idx >= len(base_vertices):
                    continue

                vertex = base_vertices[idx]
                normal = normals[idx]

                distance = np.linalg.norm(vertex - region.center)
                influence = np.exp(-(distance ** region.falloff_exponent) /
                                  (2 * region.radius ** region.falloff_exponent))

                displacement = normal * max_disp * influence
                displaced[idx] += displacement

        return displaced

    def apply_vascularity(self,
                         base_vertices: np.ndarray,
                         muscle_activations: Dict[MuscleGroup, float],
                         body_fat_pct: float) -> Dict[int, float]:
        """
        Calculate vascularity (vein visibility) per vertex.

        Returns vertex indices and visibility values for shader use.

        Args:
            base_vertices: SMPL mesh vertices
            muscle_activations: Current muscle activation
            body_fat_pct: Body fat percentage (lower = more visible veins)

        Returns:
            Dict of vertex_index -> visibility (0-1)
        """
        vascularity = {}

        # Vascularity inversely related to body fat
        # <10% = very vascular, >20% = minimal vascularity
        fat_factor = max(0, 1 - (body_fat_pct - 10) / 10)

        for muscle, activation in muscle_activations.items():
            if muscle not in self.regions:
                continue

            region = self.regions[muscle]

            # Veins most visible near muscle surface, less at center
            for idx in region.vertex_indices:
                if idx >= len(base_vertices):
                    continue

                vertex = base_vertices[idx]
                distance = np.linalg.norm(vertex - region.center)

                # Veins visible in "sweet spot" (not too deep, not too surface)
                vein_depth_factor = np.exp(-((distance - region.radius * 0.7) ** 2) /
                                          (2 * (region.radius * 0.3) ** 2))

                visibility = activation * fat_factor * vein_depth_factor * 0.5

                if visibility > 0.1:
                    vascularity[idx] = min(1.0, visibility)

        return vascularity

    def get_muscle_activation_from_workout(self, workout_exercises: List[dict]) -> Dict[MuscleGroup, float]:
        """
        Convert workout exercises to muscle activation levels.

        Args:
            workout_exercises: List of exercise dicts with:
                - 'name': exercise name
                - 'muscle_groups': list of MuscleGroups
                - 'sets': number of sets
                - 'reps': reps per set
                - 'weight': weight used

        Returns:
            Dict of muscle group -> activation (0-1)
        """
        activation = {mg: 0.0 for mg in MuscleGroup}

        for exercise in workout_exercises:
            volume = exercise.get('sets', 0) * exercise.get('reps', 0) * exercise.get('weight', 0)

            # Normalize volume to activation (rough heuristic)
            # 1000 lbs total volume = moderate activation
            base_activation = min(volume / 2000, 1.0)

            for muscle in exercise.get('muscle_groups', []):
                if isinstance(muscle, str):
                    try:
                        muscle = MuscleGroup(muscle)
                    except ValueError:
                        continue

                activation[muscle] = max(activation[muscle], base_activation)

        return activation


def demo_displacement():
    """Demonstrate muscle displacement system"""
    print("Muscle Displacement Demo")
    print("=" * 50)

    # Create system
    disp = MuscleDisplacementSystem()

    print(f"\nDefined {len(disp.regions)} muscle regions:")
    for mg, region in disp.regions.items():
        print(f"  {region.name:12s}: {len(region.vertex_indices)} vertices, "
              f"max disp: {region.max_displacement*1000:.1f}mm")

    # Simulate workout pump
    print("\n" + "=" * 50)
    print("\nSimulating arm workout pump:")

    workout = [
        {
            'name': 'Bicep Curls',
            'muscle_groups': [MuscleGroup.BICEPS],
            'sets': 4,
            'reps': 12,
            'weight': 30
        },
        {
            'name': 'Tricep Extensions',
            'muscle_groups': [MuscleGroup.TRICEPS],
            'sets': 4,
            'reps': 12,
            'weight': 25
        }
    ]

    activation = disp.get_muscle_activation_from_workout(workout)

    print("\nMuscle activation levels:")
    for muscle, level in activation.items():
        if level > 0:
            bar = "█" * int(level * 20)
            print(f"  {muscle.value:12s}: {level:.2f} {bar}")

    # Simulate pump over time
    print("\n" + "=" * 50)
    print("\nPump decay over time (biceps):")

    # Mock vertices
    mock_vertices = np.random.randn(6890, 3) * 0.1

    for hours in [0, 0.5, 1, 2, 3, 6]:
        pumped = disp.apply_muscle_pump(
            mock_vertices,
            {MuscleGroup.BICEPS: 0.8},
            time_since_workout=hours
        )

        # Calculate average displacement
        displacement = np.linalg.norm(pumped - mock_vertices, axis=1).mean()
        bar = "█" * int(displacement * 5000)
        print(f"  {hours:4.1f}h: {displacement*1000:.2f}mm avg {bar}")


if __name__ == "__main__":
    demo_displacement()
