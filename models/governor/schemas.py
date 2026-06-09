"""Input/output dataclasses for the PhysiqAI physiology engine (the Governor).
Internal units are metric (kg, m); the UI layer converts from lb/inches.
See docs/ENGINE_SPEC_DRAFT.md."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Literal, Dict


@dataclass
class UserProfile:
    age: int
    sex: Literal["M", "F"]
    height_m: float
    weight_kg: float
    bf_pct: float
    years_training: float = 0.0
    sleep_hrs_per_night: float = 7.5
    stress_level: int = 5
    genetic_potential: Literal["low", "average", "high"] = "average"
    bf_estimated: bool = True

    @property
    def experience_level(self) -> str:
        if self.years_training < 1:
            return "beginner"
        if self.years_training < 3:
            return "intermediate"
        return "advanced"

    @property
    def lean_mass_kg(self) -> float:
        return self.weight_kg * (1 - self.bf_pct / 100)


@dataclass
class GoalSpec:
    primary: Literal["fat_loss", "muscle_gain", "recomp", "maintenance"]
    lean_preference: Literal["standard", "lean_bulk", "aggressive_bulk"] = "standard"
    acceptable_fat_gain_kg_per_month: float = 0.5


@dataclass
class NutritionSpec:
    daily_calories: Optional[int] = None
    protein_g: Optional[float] = None
    tracking_method: Literal["weighing", "app", "eyeballing", "none"] = "none"

    @property
    def protein_known(self) -> bool:
        return self.protein_g is not None


@dataclass
class TrainingSpec:
    days_per_week: int = 4
    sets_per_muscle_per_week: int = 12
    intensity: Literal["light", "moderate", "intense"] = "moderate"
    cardio_days_per_week: int = 0
    focus_muscle_groups: List[str] = field(default_factory=list)


@dataclass
class WeeklyState:
    week: int
    weight_kg: float
    fat_mass_kg: float
    lean_mass_kg: float
    bf_pct: float
    normalized_ffmi: float


@dataclass
class GovernorResult:
    initial_state: "WeeklyState"
    final_state: "WeeklyState"
    weekly_timeline: List["WeeklyState"]
    mode: str
    confidence_score: float
    ci_half_width: float
    measurement_deltas: Dict[str, float]
    warnings: List[str] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)

    _KG = 0.453592

    def weight_change_lbs(self) -> float:
        return (self.final_state.weight_kg - self.initial_state.weight_kg) / self._KG

    def confidence_range_lbs(self):
        ch = self.weight_change_lbs()
        return (ch * (1 - self.ci_half_width), ch * (1 + self.ci_half_width))
