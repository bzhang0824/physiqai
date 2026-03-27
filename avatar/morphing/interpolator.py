#!/usr/bin/env python3
"""
interpolator.py - Smooth Body State Interpolation

Handles smooth transitions between body states with various easing functions
and interpolation strategies.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Callable, Optional, Literal
from enum import Enum


class EasingType(Enum):
    """Available easing functions"""
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    EASE_OUT_BOUNCE = "ease_out_bounce"
    EASE_OUT_ELASTIC = "ease_out_elastic"
    EASE_IN_OUT_CUBIC = "ease_in_out_cubic"


@dataclass
class InterpolationConfig:
    """Configuration for interpolation"""
    duration_seconds: float = 2.0
    fps: int = 60
    easing: EasingType = EasingType.EASE_IN_OUT

    @property
    def total_frames(self) -> int:
        return int(self.duration_seconds * self.fps)


class Interpolator:
    """
    Handles smooth interpolation between body states.

    Supports multiple easing functions and can interpolate
    at different levels (parameters, betas, or vertices).
    """

    def __init__(self, config: Optional[InterpolationConfig] = None):
        self.config = config or InterpolationConfig()
        self._easing_functions = self._init_easings()

    def _init_easings(self) -> dict:
        """Initialize easing function lookup"""
        return {
            EasingType.LINEAR: self._linear,
            EasingType.EASE_IN: self._ease_in_quad,
            EasingType.EASE_OUT: self._ease_out_quad,
            EasingType.EASE_IN_OUT: self._ease_in_out_quad,
            EasingType.EASE_OUT_BOUNCE: self._ease_out_bounce,
            EasingType.EASE_OUT_ELASTIC: self._ease_out_elastic,
            EasingType.EASE_IN_OUT_CUBIC: self._ease_in_out_cubic,
        }

    # Easing function implementations
    def _linear(self, t: float) -> float:
        return t

    def _ease_in_quad(self, t: float) -> float:
        return t ** 2

    def _ease_out_quad(self, t: float) -> float:
        return 1 - (1 - t) ** 2

    def _ease_in_out_quad(self, t: float) -> float:
        """Smoothstep"""
        return t ** 2 * (3 - 2 * t)

    def _ease_in_out_cubic(self, t: float) -> float:
        if t < 0.5:
            return 4 * t ** 3
        return 1 - (-2 * t + 2) ** 3 / 2

    def _ease_out_bounce(self, t: float) -> float:
        """Bounce easing for attention-grabbing effects"""
        n1 = 7.5625
        d1 = 2.75

        if t < 1 / d1:
            return n1 * t * t
        elif t < 2 / d1:
            t -= 1.5 / d1
            return n1 * t * t + 0.75
        elif t < 2.5 / d1:
            t -= 2.25 / d1
            return n1 * t * t + 0.9375
        else:
            t -= 2.625 / d1
            return n1 * t * t + 0.984375

    def _ease_out_elastic(self, t: float) -> float:
        """Elastic easing for playful effects"""
        c4 = (2 * np.pi) / 3

        if t == 0:
            return 0
        elif t == 1:
            return 1
        else:
            return np.power(2, -10 * t) * np.sin((t * 10 - 0.75) * c4) + 1

    def interpolate_scalar(self, start: float, end: float,
                          progress: float) -> float:
        """
        Interpolate between two scalar values.

        Args:
            start: Starting value
            end: Ending value
            progress: 0.0 to 1.0 (will be eased)

        Returns:
            Interpolated value
        """
        easing_fn = self._easing_functions[self.config.easing]
        eased_t = easing_fn(progress)
        return start + (end - start) * eased_t

    def interpolate_array(self, start: np.ndarray, end: np.ndarray,
                         progress: float) -> np.ndarray:
        """
        Interpolate between two arrays (element-wise).

        Args:
            start: Starting array
            end: Ending array
            progress: 0.0 to 1.0

        Returns:
            Interpolated array
        """
        easing_fn = self._easing_functions[self.config.easing]
        eased_t = easing_fn(progress)
        return start * (1 - eased_t) + end * eased_t

    def generate_trajectory(self, start: np.ndarray, end: np.ndarray) -> List[np.ndarray]:
        """
        Generate full interpolation trajectory as list of frames.

        Args:
            start: Starting array (betas or vertices)
            end: Ending array

        Returns:
            List of arrays, one per frame
        """
        trajectory = []
        total_frames = self.config.total_frames

        for frame in range(total_frames + 1):
            t = frame / total_frames
            interpolated = self.interpolate_array(start, end, t)
            trajectory.append(interpolated)

        return trajectory

    def interpolate_body_state(self, state_a, state_b) -> List[dict]:
        """
        Generate trajectory between two BodyStates.

        Returns list of body parameter dicts for each frame.
        """
        from body_mapper import BodyState

        trajectory = []
        total_frames = self.config.total_frames

        for frame in range(total_frames + 1):
            t = frame / total_frames

            # Interpolate core parameters
            weight = self.interpolate_scalar(state_a.weight, state_b.weight, t)
            muscle = self.interpolate_scalar(state_a.muscle_pct, state_b.muscle_pct, t)
            fat = self.interpolate_scalar(state_a.fat_pct, state_b.fat_pct, t)

            # Interpolate measurements
            measurements = {}
            for key in state_a.measurements:
                if key in state_b.measurements:
                    measurements[key] = self.interpolate_scalar(
                        state_a.measurements[key],
                        state_b.measurements[key],
                        t
                    )

            trajectory.append({
                'weight': weight,
                'muscle_pct': muscle,
                'fat_pct': fat,
                'measurements': measurements,
                'frame': frame,
                'progress': t
            })

        return trajectory

    def interpolate_vertices(self, verts_a: np.ndarray, verts_b: np.ndarray,
                            return_trajectory: bool = True):
        """
        Direct vertex interpolation.

        Most efficient for pre-computed meshes.
        """
        if return_trajectory:
            return self.generate_trajectory(verts_a, verts_b)
        else:
            # Return just a generator for memory efficiency
            total_frames = self.config.total_frames
            for frame in range(total_frames + 1):
                t = frame / total_frames
                yield self.interpolate_array(verts_a, verts_b, t)


class MorphTargetCache:
    """
    Pre-computed morph targets for fast real-time interpolation.

    Instead of computing SMPL forward pass every frame,
    interpolate between cached meshes.
    """

    def __init__(self, smpl_model, cache_dir=None):
        self.smpl = smpl_model
        self.cache_dir = cache_dir
        self.cache = {}  # (w, m, f) -> vertices

    def precompute_grid(self,
                       weight_range=(120, 300, 10),  # min, max, steps
                       muscle_range=(15, 60, 5),
                       fat_range=(8, 45, 5)):
        """
        Pre-compute meshes on a grid of body parameters.

        Args:
            weight_range: (min, max, num_steps)
            muscle_range: (min, max, num_steps)
            fat_range: (min, max, num_steps)
        """
        from body_mapper import BodyToSMPLMapper, BodyState

        mapper = BodyToSMPLMapper()

        weights = np.linspace(*weight_range)
        muscles = np.linspace(*muscle_range)
        fats = np.linspace(*fat_range)

        print(f"Pre-computing {len(weights)}×{len(muscles)}×{len(fats)} = "
              f"{len(weights)*len(muscles)*len(fats)} body states...")

        count = 0
        for w in weights:
            for m in muscles:
                for f in fats:
                    # Skip impossible combinations
                    if m + f >= 90:
                        continue

                    body = BodyState(weight=w, muscle_pct=m, fat_pct=f)
                    betas = mapper.map_to_betas(body)
                    mesh = self.smpl.forward(betas=betas)

                    key = (round(w), round(m), round(f))
                    self.cache[key] = mesh['vertices']
                    count += 1

        print(f"✅ Cached {count} body states")
        return count

    def get_nearest(self, weight: float, muscle: float, fat: float):
        """Get nearest cached mesh"""
        # Quantize to cache grid
        w = round(weight / 20) * 20
        m = round(muscle / 10) * 10
        f = round(fat / 10) * 10
        return self.cache.get((w, m, f))

    def interpolate_from_cache(self, weight: float, muscle: float, fat: float,
                               k: int = 8) -> np.ndarray:
        """
        k-nearest neighbor interpolation from cache.

        Faster than full SMPL forward pass.
        """
        # Find k nearest neighbors
        neighbors = []
        for (w, m, f), vertices in self.cache.items():
            dist = np.sqrt(
                ((weight - w) / 100) ** 2 +
                ((muscle - m) / 50) ** 2 +
                ((fat - f) / 50) ** 2
            )
            neighbors.append((dist, vertices))

        # Sort by distance and take k nearest
        neighbors.sort(key=lambda x: x[0])
        neighbors = neighbors[:k]

        # Weighted average (inverse distance weighting)
        weights = [1 / (d + 0.001) for d, _ in neighbors]
        total = sum(weights)
        weights = [w / total for w in weights]

        # Blend vertices
        result = np.zeros_like(neighbors[0][1])
        for (_, vertices), weight in zip(neighbors, weights):
            result += vertices * weight

        return result


def demo_interpolation():
    """Demonstrate interpolation capabilities"""
    print("Interpolation Demo")
    print("=" * 50)

    # Test different easings
    easings = [
        EasingType.LINEAR,
        EasingType.EASE_IN_OUT,
        EasingType.EASE_OUT_BOUNCE,
        EasingType.EASE_OUT_ELASTIC
    ]

    print("\nEasing function comparison (0 to 1 over 10 steps):")
    print("-" * 50)

    steps = 10
    for easing in easings:
        config = InterpolationConfig(duration_seconds=1.0, fps=steps, easing=easing)
        interp = Interpolator(config)

        values = []
        for i in range(steps + 1):
            t = i / steps
            val = interp.interpolate_scalar(0, 1, t)
            values.append(f"{val:.2f}")

        print(f"\n{easing.value:20s}: {', '.join(values)}")

    # Test array interpolation
    print("\n" + "=" * 50)
    print("\nArray interpolation (SMPL betas):")

    start_betas = np.array([0.5, -0.3, 0.2, 0, 0, 0, 0, 0, 0, 0])
    end_betas = np.array([1.2, 0.1, 0.6, 0.2, 0.1, 0, 0, 0, 0, 0])

    config = InterpolationConfig(duration_seconds=1.0, fps=5)
    interp = Interpolator(config)

    trajectory = interp.generate_trajectory(start_betas, end_betas)

    print(f"\nInterpolating from {start_betas[:3]} to {end_betas[:3]}")
    print("-" * 50)

    for i, betas in enumerate(trajectory[::5]):  # Sample every 5th frame
        print(f"Frame {i*5:2d}: β₀={betas[0]:+.2f}, β₁={betas[1]:+.2f}, β₂={betas[2]:+.2f}")


if __name__ == "__main__":
    demo_interpolation()
