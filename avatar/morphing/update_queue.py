#!/usr/bin/env python3
"""
update_queue.py - Progressive Body Update Queue

Manages time-based application of body changes for realistic
progress visualization. Handles immediate pump effects, short-term
water retention, and long-term adaptations.
"""

import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from enum import Enum
import heapq

from .body_mapper import BodyState
from .workout_morph import MorphUpdate, ImmediateEffects, LongTermAdaptation
from .vertex_displacement import MuscleGroup, MuscleDisplacementSystem


class ChangeType(Enum):
    """Types of body changes"""
    IMMEDIATE_PUMP = "pump"           # Temporary, fades in hours
    WATER_RETENTION = "water"         # Glycogen/water, days
    MUSCLE_GROWTH = "muscle"          # Hypertrophy, weeks
    FAT_LOSS = "fat"                  # Fat oxidation, weeks
    RECOMPOSITION = "recomp"          # Simultaneous muscle/fat


@dataclass
class PendingChange:
    """
    Represents a pending body change in the queue.

    Changes are applied progressively over their duration
    rather than instantly.
    """
    change_type: ChangeType
    magnitude: float  # Amount of change
    muscle_groups: Optional[Dict[MuscleGroup, float]] = None
    start_time: datetime = field(default_factory=datetime.now)
    duration_hours: float = 24.0
    easing: str = "ease_out"  # How change is applied over time
    priority: int = 5  # Lower = higher priority

    def __lt__(self, other):
        # For heapq ordering
        return self.start_time < other.start_time

    @property
    def end_time(self) -> datetime:
        return self.start_time + timedelta(hours=self.duration_hours)

    def get_progress(self, current_time: datetime) -> float:
        """
        Get completion progress (0-1) at current time.

        Uses easing function for natural progression.
        """
        if current_time < self.start_time:
            return 0.0
        if current_time >= self.end_time:
            return 1.0

        elapsed = (current_time - self.start_time).total_seconds() / 3600
        raw_progress = elapsed / self.duration_hours

        # Apply easing
        if self.easing == "linear":
            return raw_progress
        elif self.easing == "ease_in":
            return raw_progress ** 2
        elif self.easing == "ease_out":
            return 1 - (1 - raw_progress) ** 2
        elif self.easing == "ease_in_out":
            return raw_progress ** 2 * (3 - 2 * raw_progress)
        else:
            return raw_progress

    def get_current_magnitude(self, current_time: datetime) -> float:
        """Get current magnitude of change based on progress"""
        return self.magnitude * self.get_progress(current_time)

    def is_complete(self, current_time: datetime) -> bool:
        """Check if change has been fully applied"""
        return current_time >= self.end_time

    def is_active(self, current_time: datetime) -> bool:
        """Check if change is currently being applied"""
        return self.start_time <= current_time < self.end_time


@dataclass
class BodyChangeState:
    """Tracks cumulative changes applied to body"""
    muscle_mass_delta: float = 0.0  # lbs
    fat_mass_delta: float = 0.0  # lbs
    muscle_pump_active: Dict[MuscleGroup, float] = field(default_factory=dict)
    water_weight_delta: float = 0.0  # lbs

    def get_total_weight_delta(self) -> float:
        """Total weight change including water"""
        return self.muscle_mass_delta + self.fat_mass_delta + self.water_weight_delta


class ProgressiveUpdateQueue:
    """
    Manages queue of body changes applied over time.

    Creates realistic progression where:
    - Pump appears immediately and fades over hours
    - Water retention changes over days
    - Muscle/fat changes happen over weeks
    """

    def __init__(self, initial_state: BodyState):
        self.initial_state = initial_state
        self.current_state = initial_state
        self.change_state = BodyChangeState()

        # Priority queue of pending changes
        self.pending_changes: List[PendingChange] = []

        # History of completed changes
        self.change_history: List[PendingChange] = []

        # Displacement system for vertex effects
        self.displacement = MuscleDisplacementSystem()

        # Last update time
        self.last_update = datetime.now()

    def add_workout(self, morph_update: MorphUpdate):
        """
        Add workout effects to the update queue.

        Creates multiple changes:
        1. Immediate pump (2-3 hours)
        2. Water retention from glycogen (24-48 hours)
        3. Muscle growth projection (over weeks)
        4. Fat loss from calorie burn (over days)
        """
        now = morph_update.timestamp

        # 1. Immediate pump effect
        if morph_update.immediate.muscle_pump:
            pump_change = PendingChange(
                change_type=ChangeType.IMMEDIATE_PUMP,
                magnitude=1.0,  # Binary - pump is on/off
                muscle_groups=morph_update.immediate.muscle_pump,
                start_time=now,
                duration_hours=morph_update.immediate.duration_minutes / 60,
                easing="ease_out",
                priority=1
            )
            self._add_change(pump_change)

        # 2. Water retention from glycogen storage
        # Each gram of glycogen holds ~3g of water
        # Typical workout stores 100-300g glycogen
        glycogen_storage = sum(morph_update.immediate.muscle_pump.values()) * 200
        water_weight = glycogen_storage * 3 / 453.592  # Convert to lbs

        water_change = PendingChange(
            change_type=ChangeType.WATER_RETENTION,
            magnitude=water_weight,
            start_time=now + timedelta(hours=2),  # Delayed
            duration_hours=48,
            easing="ease_in_out",
            priority=2
        )
        self._add_change(water_change)

        # 3. Muscle growth (distributed over weeks)
        for muscle, weekly_rate in morph_update.projected.muscle_gain_rate_per_week.items():
            if weekly_rate > 0:
                muscle_change = PendingChange(
                    change_type=ChangeType.MUSCLE_GROWTH,
                    magnitude=weekly_rate,
                    muscle_groups={muscle: 1.0},
                    start_time=now + timedelta(days=1),  # Delayed onset
                    duration_hours=24 * 7,  # Over 1 week
                    easing="ease_out",
                    priority=5
                )
                self._add_change(muscle_change)

        # 4. Fat loss (immediate but small)
        if morph_update.projected.fat_burn_per_session > 0:
            fat_change = PendingChange(
                change_type=ChangeType.FAT_LOSS,
                magnitude=morph_update.projected.fat_burn_per_session,
                start_time=now + timedelta(hours=6),  # Delayed
                duration_hours=24,
                easing="linear",
                priority=3
            )
            self._add_change(fat_change)

    def _add_change(self, change: PendingChange):
        """Add change to priority queue"""
        heapq.heappush(self.pending_changes, change)

    def update(self, current_time: Optional[datetime] = None) -> dict:
        """
        Apply pending changes up to current time.

        Call this periodically (e.g., every frame or minute)
        to update body state.

        Returns:
            Status dict with current state info
        """
        if current_time is None:
            current_time = datetime.now()

        # Reset change state for recalculation
        self.change_state = BodyChangeState()

        # Process all changes
        active_changes = []
        completed_changes = []

        # Copy pending changes list (heapq doesn't support removal well)
        still_pending = []

        for change in self.pending_changes:
            if change.is_complete(current_time):
                # Move to history
                completed_changes.append(change)
                self._apply_completed_change(change)
            elif change.is_active(current_time):
                # Currently applying
                active_changes.append(change)
                self._apply_active_change(change, current_time)
            else:
                # Not started yet
                still_pending.append(change)

        # Rebuild heap
        self.pending_changes = still_pending
        heapq.heapify(self.pending_changes)
        self.change_history.extend(completed_changes)

        # Update body state
        self._recompute_body_state()

        self.last_update = current_time

        return {
            'timestamp': current_time,
            'active_changes': len(active_changes),
            'pending_changes': len(self.pending_changes),
            'completed_changes': len(self.change_history),
            'current_weight': self.current_state.weight,
            'weight_delta': self.change_state.get_total_weight_delta(),
            'muscle_pump_active': len(self.change_state.muscle_pump_active) > 0
        }

    def _apply_completed_change(self, change: PendingChange):
        """Apply full magnitude of completed change"""
        if change.change_type == ChangeType.MUSCLE_GROWTH:
            self.change_state.muscle_mass_delta += change.magnitude
        elif change.change_type == ChangeType.FAT_LOSS:
            self.change_state.fat_mass_delta -= change.magnitude
        elif change.change_type == ChangeType.WATER_RETENTION:
            self.change_state.water_weight_delta += change.magnitude

    def _apply_active_change(self, change: PendingChange, current_time: datetime):
        """Apply partial magnitude of active change"""
        progress = change.get_progress(current_time)
        current_magnitude = change.magnitude * progress

        if change.change_type == ChangeType.IMMEDIATE_PUMP:
            # Pump is special - it's a temporary vertex displacement
            if change.muscle_groups:
                for muscle, intensity in change.muscle_groups.items():
                    self.change_state.muscle_pump_active[muscle] = intensity * (1 - progress)

        elif change.change_type == ChangeType.MUSCLE_GROWTH:
            self.change_state.muscle_mass_delta += current_magnitude

        elif change.change_type == ChangeType.FAT_LOSS:
            self.change_state.fat_mass_delta -= current_magnitude

        elif change.change_type == ChangeType.WATER_RETENTION:
            self.change_state.water_weight_delta += current_magnitude

    def _recompute_body_state(self):
        """Recompute current body state from base + changes"""
        new_weight = (self.initial_state.weight +
                     self.change_state.get_total_weight_delta())

        # Recalculate composition
        initial_lean = self.initial_state.lean_mass
        new_lean = initial_lean + self.change_state.muscle_mass_delta
        new_fat = (self.initial_state.weight - initial_lean) + self.change_state.fat_mass_delta

        new_muscle_pct = (new_lean / new_weight * 100) if new_weight > 0 else 0
        new_fat_pct = (new_fat / new_weight * 100) if new_weight > 0 else 0

        # Create new state
        self.current_state = BodyState(
            weight=new_weight,
            muscle_pct=max(5, new_muscle_pct),
            fat_pct=max(3, new_fat_pct),
            height=self.initial_state.height,
            measurements=self.initial_state.measurements.copy()
        )

    def get_vertices_with_effects(self, base_vertices: np.ndarray) -> np.ndarray:
        """
        Get mesh vertices with all active effects applied.

        Applies pump displacement if active.
        """
        vertices = base_vertices.copy()

        # Apply muscle pump if active
        if self.change_state.muscle_pump_active:
            # Calculate time since last workout for decay
            hours_since = 0  # Would track from change timestamps
            vertices = self.displacement_system.apply_muscle_pump(
                vertices,
                self.change_state.muscle_pump_active,
                time_since_workout=hours_since
            )

        return vertices

    def get_current_visual_state(self) -> dict:
        """
        Get visual state for rendering.

        Returns dict with shader parameters:
        - Pump level per muscle
        - Vascularity boost
        - Skin tightness
        """
        max_pump = max(self.change_state.muscle_pump_active.values()) if self.change_state.muscle_pump_active else 0

        return {
            'pump_intensity': max_pump,
            'vascularity_boost': max_pump * 0.5,
            'skin_tightness': 1.0 + max_pump * 0.1,
            'active_muscles': list(self.change_state.muscle_pump_active.keys()),
            'body_state': self.current_state.to_dict()
        }

    def simulate_to(self, target_time: datetime) -> List[dict]:
        """
        Simulate updates up to target time, returning state history.

        Useful for previewing future progress.
        """
        history = []
        current = self.last_update

        # Step forward in 1-hour increments
        while current < target_time:
            current += timedelta(hours=1)
            status = self.update(current)
            history.append(status)

        return history


def demo_update_queue():
    """Demonstrate progressive update queue"""
    print("Progressive Update Queue Demo")
    print("=" * 60)

    from body_mapper import BodyState
    from workout_morph import create_sample_workout, WorkoutMorphEngine

    # Create initial state
    initial = BodyState(weight=180, muscle_pct=35, fat_pct=25)
    queue = ProgressiveUpdateQueue(initial)

    print(f"\nInitial State:")
    print(f"  Weight: {initial.weight:.0f} lbs")
    print(f"  Muscle: {initial.muscle_pct:.0f}%")
    print(f"  Fat: {initial.fat_pct:.0f}%")

    # Create and process workout
    workout = create_sample_workout()
    engine = WorkoutMorphEngine()
    update = engine.process_workout(workout)

    queue.add_workout(update)

    print(f"\nWorkout added to queue:")
    print(f"  {len(queue.pending_changes)} pending changes")

    # Simulate timeline
    print("\n" + "=" * 60)
    print("\nSimulating effects over time:")
    print("-" * 60)

    base_time = workout.start_time
    check_points = [
        ("Immediate", timedelta(minutes=30)),
        ("1 Hour", timedelta(hours=1)),
        ("6 Hours", timedelta(hours=6)),
        ("24 Hours", timedelta(days=1)),
        ("1 Week", timedelta(days=7)),
        ("1 Month", timedelta(days=30)),
    ]

    for label, delta in check_points:
        status = queue.update(base_time + delta)

        print(f"\n{label}:")
        print(f"  Weight: {status['current_weight']:.1f} lbs "
              f"({status['weight_delta']:+.2f})")
        print(f"  Active changes: {status['active_changes']}")
        print(f"  Pump active: {status['muscle_pump_active']}")


if __name__ == "__main__":
    demo_update_queue()
