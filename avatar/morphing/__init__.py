#!/usr/bin/env python3
"""
PhysiqAI Body Morphing System

A hybrid body parameter morphing system that combines:
- SMPL shape parameters (betas) for overall body shape
- Vertex displacement for localized muscle effects
- Smooth interpolation between states
- Real-time workout-driven updates
- Visual feedback for different change types

Usage:
    from morphing import BodyMorphingSystem, BodyState

    # Create system
    morph = BodyMorphingSystem(gender='male')

    # Define body state
    state = BodyState(weight=180, muscle_pct=35, fat_pct=25)

    # Generate mesh
    mesh = morph.generate_mesh(state)

    # Process workout for updates
    morph.process_workout(workout_data)

    # Get updated mesh with effects
    mesh = morph.get_current_mesh()
"""

__version__ = "1.0.0"
__author__ = "PhysiqAI"

# Core imports
from .body_mapper import BodyState, BodyToSMPLMapper
from .smpl_core import SMPLModel, generate_body, load_smpl_model
from .interpolator import Interpolator, InterpolationConfig, EasingType, MorphTargetCache
from .vertex_displacement import (
    MuscleDisplacementSystem,
    MuscleGroup,
    MuscleRegion
)
from .workout_morph import (
    WorkoutMorphEngine,
    WorkoutSession,
    Exercise,
    ExerciseType,
    MorphUpdate,
    ImmediateEffects,
    LongTermAdaptation
)
from .update_queue import (
    ProgressiveUpdateQueue,
    PendingChange,
    ChangeType,
    BodyChangeState
)
from .visual_feedback import (
    VisualFeedbackSystem,
    ChangeVisualizationType,
    VisualEffect,
    SHADER_CODE
)


class BodyMorphingSystem:
    """
    Unified interface for the body morphing system.

    Combines all components into a single easy-to-use interface.
    """

    def __init__(self, gender: str = 'neutral', use_cache: bool = True):
        """
        Initialize the body morphing system.

        Args:
            gender: 'male', 'female', or 'neutral'
            use_cache: Whether to pre-compute morph targets
        """
        self.gender = gender

        # Initialize components
        try:
            self.smpl_model = load_smpl_model(gender)
            self.mapper = BodyToSMPLMapper(gender=gender)
            self.has_smpl = True
        except FileNotFoundError:
            print("⚠️  SMPL models not found. Running in demo mode.")
            self.smpl_model = None
            self.mapper = BodyToSMPLMapper(gender=gender)
            self.has_smpl = False

        self.interpolator = Interpolator()
        self.displacement = MuscleDisplacementSystem()
        self.workout_engine = WorkoutMorphEngine()
        self.visual_feedback = VisualFeedbackSystem()

        # State management
        self.current_state = self.mapper.get_preset_body('average')
        self.update_queue = None

        # Cache
        self.cache = None
        if use_cache and self.has_smpl:
            self.cache = MorphTargetCache(self.smpl_model)

    def set_body_state(self, state: BodyState) -> dict:
        """
        Set current body state.

        Args:
            state: New BodyState

        Returns:
            Mesh data dict with vertices and faces
        """
        self.current_state = state

        if self.update_queue is None:
            self.update_queue = ProgressiveUpdateQueue(state)

        return self.generate_mesh(state)

    def generate_mesh(self, state: BodyState = None,
                     apply_effects: bool = True) -> dict:
        """
        Generate mesh for body state.

        Args:
            state: BodyState (uses current if None)
            apply_effects: Whether to apply active pump effects

        Returns:
            Dict with 'vertices', 'faces', and shader params
        """
        if state is None:
            state = self.current_state

        # Generate base mesh
        if self.has_smpl:
            betas = self.mapper.map_to_betas(state)
            mesh = self.smpl_model.forward(betas=betas)
            vertices = mesh['vertices']
            faces = mesh['faces']
        else:
            # Demo mode - return placeholder
            vertices = np.zeros((6890, 3))
            faces = np.zeros((13776, 3), dtype=int)

        # Apply active effects
        if apply_effects and self.update_queue:
            vertices = self.update_queue.get_vertices_with_effects(vertices)

        # Get visual feedback
        visual_state = {}
        if self.update_queue:
            visual_state = self.update_queue.get_current_visual_state()

        return {
            'vertices': vertices,
            'faces': faces,
            'body_state': state.to_dict(),
            'visual_state': visual_state
        }

    def process_workout(self, workout) -> dict:
        """
        Process workout and queue body changes.

        Args:
            workout: WorkoutSession object

        Returns:
            Update status dict
        """
        if self.update_queue is None:
            self.update_queue = ProgressiveUpdateQueue(self.current_state)

        morph_update = self.workout_engine.process_workout(workout)
        self.update_queue.add_workout(morph_update)

        return {
            'workout_processed': True,
            'pump_duration_minutes': morph_update.immediate.duration_minutes,
            'muscle_groups': [mg.value for mg in morph_update.immediate.muscle_pump.keys()],
            'projected_weekly_gain': sum(morph_update.projected.muscle_gain_rate_per_week.values())
        }

    def update(self, current_time=None) -> dict:
        """
        Update body state based on pending changes.

        Call periodically to apply time-based changes.

        Returns:
            Current status dict
        """
        if self.update_queue is None:
            return {'error': 'No state initialized'}

        status = self.update_queue.update(current_time)
        self.current_state = self.update_queue.current_state

        return status

    def interpolate_to(self, target_state: BodyState,
                      duration_seconds: float = 2.0) -> list:
        """
        Generate interpolation frames to target state.

        Args:
            target_state: Target BodyState
            duration_seconds: Animation duration

        Returns:
            List of mesh dicts for each frame
        """
        config = InterpolationConfig(duration_seconds=duration_seconds)
        interp = Interpolator(config)

        # Interpolate body parameters
        trajectory = interp.interpolate_body_state(
            self.current_state, target_state
        )

        # Generate mesh for each frame
        frames = []
        for params in trajectory:
            state = BodyState(
                weight=params['weight'],
                muscle_pct=params['muscle_pct'],
                fat_pct=params['fat_pct'],
                measurements=params['measurements']
            )
            mesh = self.generate_mesh(state, apply_effects=False)
            mesh['frame'] = params['frame']
            mesh['progress'] = params['progress']
            frames.append(mesh)

        return frames

    def get_comparison(self, other_state: BodyState = None) -> dict:
        """
        Get visual comparison between current and another state.

        Args:
            other_state: State to compare to (uses initial if None)

        Returns:
            Comparison dict with effects and stats
        """
        if other_state is None and self.update_queue:
            other_state = self.update_queue.initial_state
        elif other_state is None:
            return {'error': 'No comparison state available'}

        return self.visual_feedback.compare_states(other_state, self.current_state)

    def precompute_cache(self, resolution: int = 5) -> int:
        """
        Pre-compute morph targets for fast interpolation.

        Args:
            resolution: Grid resolution per parameter

        Returns:
            Number of states cached
        """
        if self.cache is None:
            return 0

        return self.cache.precompute_grid(
            weight_range=(120, 300, resolution),
            muscle_range=(15, 60, resolution),
            fat_range=(8, 45, resolution)
        )


# Convenience functions
def quick_morph(start_preset: str, end_preset: str, steps: int = 30) -> list:
    """
    Quick morph between two preset body types.

    Args:
        start_preset: Starting preset name
        end_preset: Ending preset name
        steps: Number of morph steps

    Returns:
        List of body state dicts
    """
    morph = BodyMorphingSystem()
    start = morph.mapper.get_preset_body(start_preset)
    end = morph.mapper.get_preset_body(end_preset)

    return morph.interpolate_to(end, duration_seconds=steps / 30)


def demo():
    """Run system demo"""
    print("PhysiqAI Body Morphing System Demo")
    print("=" * 60)

    # Initialize
    morph = BodyMorphingSystem(gender='male')

    print(f"\n✅ System initialized")
    print(f"   SMPL available: {morph.has_smpl}")

    # Set initial state
    initial = morph.mapper.get_preset_body('average')
    morph.set_body_state(initial)

    print(f"\n📊 Initial state:")
    print(f"   Weight: {initial.weight:.0f} lbs")
    print(f"   Muscle: {initial.muscle_pct:.0f}%")
    print(f"   Fat: {initial.fat_pct:.0f}%")

    # Generate mesh
    mesh = morph.generate_mesh()
    print(f"\n🎨 Generated mesh: {mesh['vertices'].shape}")

    # Morph to target
    print("\n📈 Morphing to 'muscular' preset...")
    target = morph.mapper.get_preset_body('muscular')
    frames = morph.interpolate_to(target, duration_seconds=1.0)

    print(f"   Generated {len(frames)} frames")
    print(f"   Sample frame 15: β₀={frames[15]['visual_state']}")

    print("\n✅ Demo complete!")


if __name__ == "__main__":
    demo()
