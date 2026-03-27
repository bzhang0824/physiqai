"""
Database models for PhysiqAI
============================

SQLAlchemy models for:
- Users
- UserPhotos
- Workouts
- WorkoutExercises
- BodyMeasurements
- ProgressEntries
- Goals
- SocialConnections
"""

from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass, field
import json
import numpy as np


@dataclass
class User:
    """User account model"""
    id: str
    email: str
    name: str
    gender: str  # 'male', 'female', 'other'
    birth_date: Optional[datetime] = None
    height_cm: Optional[float] = None  # cm
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Avatar settings
    avatar_style: str = "realistic"  # realistic, cartoon, minimalist
    avatar_color: str = "#4A90E2"

    # Preferences
    unit_system: str = "metric"  # metric, imperial
    privacy_level: str = "friends"  # private, friends, public

    # Stats
    current_weight_kg: Optional[float] = None
    current_body_fat_pct: Optional[float] = None
    current_muscle_mass_kg: Optional[float] = None

    @property
    def age(self) -> Optional[int]:
        if self.birth_date:
            today = datetime.now()
            return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        return None

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'gender': self.gender,
            'age': self.age,
            'height_cm': self.height_cm,
            'created_at': self.created_at.isoformat(),
            'avatar_style': self.avatar_style,
            'current_weight_kg': self.current_weight_kg,
            'current_body_fat_pct': self.current_body_fat_pct,
            'current_muscle_mass_kg': self.current_muscle_mass_kg,
        }


@dataclass
class UserPhoto:
    """User uploaded photo for avatar creation"""
    id: str
    user_id: str
    photo_path: str
    photo_type: str  # 'front', 'side', 'back'
    uploaded_at: datetime = field(default_factory=datetime.now)

    # Processing results
    processed: bool = False
    processing_error: Optional[str] = None

    # SMPL fitting results
    smpl_betas: Optional[List[float]] = None
    body_type: Optional[str] = None
    estimated_height_cm: Optional[float] = None
    estimated_weight_kg: Optional[float] = None
    confidence_score: Optional[float] = None

    # Avatar outputs
    avatar_mesh_path: Optional[str] = None
    avatar_image_path: Optional[str] = None
    avatar_gltf_path: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'photo_type': self.photo_type,
            'uploaded_at': self.uploaded_at.isoformat(),
            'processed': self.processed,
            'body_type': self.body_type,
            'estimated_height_cm': self.estimated_height_cm,
            'estimated_weight_kg': self.estimated_weight_kg,
            'confidence_score': self.confidence_score,
            'avatar_mesh_path': self.avatar_mesh_path,
            'avatar_image_path': self.avatar_image_path,
        }


@dataclass
class WorkoutExercise:
    """Individual exercise within a workout"""
    name: str
    muscle_groups: List[str]
    exercise_type: str  # compound, isolation, cardio, calisthenics
    sets: int
    reps: int
    weight_kg: float
    rpe: float = 7.0  # Rate of perceived exertion (1-10)
    rest_seconds: int = 60
    notes: str = ""

    @property
    def volume(self) -> float:
        """Total volume (weight × reps × sets)"""
        return self.weight_kg * self.reps * self.sets

    @property
    def intensity_score(self) -> float:
        """Intensity based on volume and RPE"""
        return (self.volume / 1000) * (self.rpe / 5)

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'muscle_groups': self.muscle_groups,
            'exercise_type': self.exercise_type,
            'sets': self.sets,
            'reps': self.reps,
            'weight_kg': self.weight_kg,
            'volume': self.volume,
            'rpe': self.rpe,
            'rest_seconds': self.rest_seconds,
            'notes': self.notes,
        }


@dataclass
class Workout:
    """Workout session model"""
    id: str
    user_id: str
    name: str
    workout_type: str  # strength, cardio, mixed, hiit
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[float] = None
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    exercises: List[WorkoutExercise] = field(default_factory=list)

    # Calculated fields
    total_volume: float = 0.0
    muscle_groups_trained: List[str] = field(default_factory=list)

    def calculate_stats(self):
        """Calculate workout statistics"""
        self.total_volume = sum(ex.volume for ex in self.exercises)

        groups = set()
        for ex in self.exercises:
            groups.update(ex.muscle_groups)
        self.muscle_groups_trained = list(groups)

        if self.end_time and self.start_time:
            self.duration_minutes = (self.end_time - self.start_time).total_seconds() / 60

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'workout_type': self.workout_type,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_minutes': self.duration_minutes,
            'total_volume': self.total_volume,
            'muscle_groups_trained': self.muscle_groups_trained,
            'exercises': [ex.to_dict() for ex in self.exercises],
            'notes': self.notes,
        }


@dataclass
class BodyMeasurement:
    """Body measurements entry"""
    id: str
    user_id: str
    measured_at: datetime = field(default_factory=datetime.now)

    # Basic metrics
    weight_kg: Optional[float] = None
    body_fat_pct: Optional[float] = None
    muscle_mass_kg: Optional[float] = None
    bmi: Optional[float] = None

    # Circumferences (cm)
    chest_cm: Optional[float] = None
    waist_cm: Optional[float] = None
    hips_cm: Optional[float] = None
    shoulders_cm: Optional[float] = None
    arms_cm: Optional[float] = None
    thighs_cm: Optional[float] = None
    calves_cm: Optional[float] = None

    # Source
    source: str = "manual"  # manual, smart_scale, photo_estimate

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'measured_at': self.measured_at.isoformat(),
            'weight_kg': self.weight_kg,
            'body_fat_pct': self.body_fat_pct,
            'muscle_mass_kg': self.muscle_mass_kg,
            'bmi': self.bmi,
            'chest_cm': self.chest_cm,
            'waist_cm': self.waist_cm,
            'hips_cm': self.hips_cm,
            'shoulders_cm': self.shoulders_cm,
            'arms_cm': self.arms_cm,
            'thighs_cm': self.thighs_cm,
            'calves_cm': self.calves_cm,
            'source': self.source,
        }


@dataclass
class ProgressEntry:
    """Progress tracking entry"""
    id: str
    user_id: str
    entry_type: str  # weight, photo, measurement, milestone
    recorded_at: datetime = field(default_factory=datetime.now)

    # Values
    value: Optional[float] = None
    unit: Optional[str] = None
    notes: str = ""

    # Media
    photo_before_path: Optional[str] = None
    photo_after_path: Optional[str] = None
    avatar_state_before: Optional[dict] = None
    avatar_state_after: Optional[dict] = None

    # Milestone
    milestone_name: Optional[str] = None
    milestone_achieved: bool = False

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'entry_type': self.entry_type,
            'recorded_at': self.recorded_at.isoformat(),
            'value': self.value,
            'unit': self.unit,
            'notes': self.notes,
            'milestone_name': self.milestone_name,
            'milestone_achieved': self.milestone_achieved,
        }


@dataclass
class Goal:
    """User fitness goal"""
    id: str
    user_id: str
    goal_type: str  # weight_loss, muscle_gain, body_recomposition, maintenance
    title: str
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    target_date: Optional[datetime] = None

    # Target metrics
    target_weight_kg: Optional[float] = None
    target_body_fat_pct: Optional[float] = None
    target_muscle_mass_kg: Optional[float] = None

    # Starting point (snapshot when goal created)
    start_weight_kg: Optional[float] = None
    start_body_fat_pct: Optional[float] = None

    # Progress
    status: str = "active"  # active, achieved, paused, abandoned
    progress_pct: float = 0.0
    achieved_at: Optional[datetime] = None

    # Avatar projections
    projected_avatar_path: Optional[str] = None
    timeline_weeks: int = 12

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'goal_type': self.goal_type,
            'title': self.title,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'target_weight_kg': self.target_weight_kg,
            'target_body_fat_pct': self.target_body_fat_pct,
            'target_muscle_mass_kg': self.target_muscle_mass_kg,
            'start_weight_kg': self.start_weight_kg,
            'start_body_fat_pct': self.start_body_fat_pct,
            'status': self.status,
            'progress_pct': self.progress_pct,
            'timeline_weeks': self.timeline_weeks,
        }


@dataclass
class SocialConnection:
    """Social connection between users"""
    id: str
    requester_id: str
    recipient_id: str
    status: str = "pending"  # pending, accepted, rejected, blocked
    created_at: datetime = field(default_factory=datetime.now)
    accepted_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'requester_id': self.requester_id,
            'recipient_id': self.recipient_id,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'accepted_at': self.accepted_at.isoformat() if self.accepted_at else None,
        }


@dataclass
class SharedProgress:
    """Shared progress post"""
    id: str
    user_id: str
    share_type: str  # transformation, milestone, workout, comparison
    title: str
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    # Content
    before_photo_path: Optional[str] = None
    after_photo_path: Optional[str] = None
    avatar_animation_path: Optional[str] = None
    progress_data: dict = field(default_factory=dict)

    # Engagement
    likes_count: int = 0
    comments_count: int = 0

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'share_type': self.share_type,
            'title': self.title,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'progress_data': self.progress_data,
            'likes_count': self.likes_count,
            'comments_count': self.comments_count,
        }


# In-memory database for demo
class InMemoryDB:
    """Simple in-memory database for demo purposes"""

    def __init__(self):
        self.users: dict[str, User] = {}
        self.photos: dict[str, UserPhoto] = {}
        self.workouts: dict[str, Workout] = {}
        self.measurements: dict[str, BodyMeasurement] = {}
        self.progress_entries: dict[str, ProgressEntry] = {}
        self.goals: dict[str, Goal] = {}
        self.connections: dict[str, SocialConnection] = {}
        self.shared_progress: dict[str, SharedProgress] = {}

        # Indexes
        self.user_photos: dict[str, list[str]] = {}  # user_id -> photo_ids
        self.user_workouts: dict[str, list[str]] = {}  # user_id -> workout_ids
        self.user_measurements: dict[str, list[str]] = {}  # user_id -> measurement_ids
        self.user_progress: dict[str, list[str]] = {}  # user_id -> entry_ids
        self.user_goals: dict[str, list[str]] = {}  # user_id -> goal_ids
        self.user_connections: dict[str, list[str]] = {}  # user_id -> connection_ids

    def save_user(self, user: User) -> User:
        self.users[user.id] = user
        return user

    def get_user(self, user_id: str) -> Optional[User]:
        return self.users.get(user_id)

    def save_photo(self, photo: UserPhoto) -> UserPhoto:
        self.photos[photo.id] = photo
        if photo.user_id not in self.user_photos:
            self.user_photos[photo.user_id] = []
        if photo.id not in self.user_photos[photo.user_id]:
            self.user_photos[photo.user_id].append(photo.id)
        return photo

    def get_user_photos(self, user_id: str) -> List[UserPhoto]:
        photo_ids = self.user_photos.get(user_id, [])
        return [self.photos[pid] for pid in photo_ids if pid in self.photos]

    def save_workout(self, workout: Workout) -> Workout:
        self.workouts[workout.id] = workout
        if workout.user_id not in self.user_workouts:
            self.user_workouts[workout.user_id] = []
        if workout.id not in self.user_workouts[workout.user_id]:
            self.user_workouts[workout.user_id].append(workout.id)
        return workout

    def get_user_workouts(self, user_id: str, limit: int = 50) -> List[Workout]:
        workout_ids = self.user_workouts.get(user_id, [])[-limit:]
        return [self.workouts[wid] for wid in workout_ids if wid in self.workouts]

    def save_measurement(self, measurement: BodyMeasurement) -> BodyMeasurement:
        self.measurements[measurement.id] = measurement
        if measurement.user_id not in self.user_measurements:
            self.user_measurements[measurement.user_id] = []
        self.user_measurements[measurement.user_id].append(measurement.id)
        return measurement

    def get_user_measurements(self, user_id: str, limit: int = 100) -> List[BodyMeasurement]:
        measurement_ids = self.user_measurements.get(user_id, [])[-limit:]
        return [self.measurements[mid] for mid in measurement_ids if mid in self.measurements]

    def save_goal(self, goal: Goal) -> Goal:
        self.goals[goal.id] = goal
        if goal.user_id not in self.user_goals:
            self.user_goals[goal.user_id] = []
        self.user_goals[goal.user_id].append(goal.id)
        return goal

    def get_user_goals(self, user_id: str) -> List[Goal]:
        goal_ids = self.user_goals.get(user_id, [])
        return [self.goals[gid] for gid in goal_ids if gid in self.goals]

    def save_progress_entry(self, entry: ProgressEntry) -> ProgressEntry:
        self.progress_entries[entry.id] = entry
        if entry.user_id not in self.user_progress:
            self.user_progress[entry.user_id] = []
        self.user_progress[entry.user_id].append(entry.id)
        return entry

    def get_user_progress(self, user_id: str, limit: int = 50) -> List[ProgressEntry]:
        entry_ids = self.user_progress.get(user_id, [])[-limit:]
        return [self.progress_entries[eid] for eid in entry_ids if eid in self.progress_entries]

    def save_shared_progress(self, shared: SharedProgress) -> SharedProgress:
        self.shared_progress[shared.id] = shared
        return shared

    def get_shared_progress(self, limit: int = 20) -> List[SharedProgress]:
        shared_ids = list(self.shared_progress.keys())[-limit:]
        return [self.shared_progress[sid] for sid in shared_ids]


# Global database instance
db = InMemoryDB()
