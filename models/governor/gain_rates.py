"""Stage 2/3: lean-mass gain rates and the FFMI natural ceiling.
Aragon/Helms bodyweight-anchored model; Kouri 1995 (PMID 7496846) ceiling."""
from __future__ import annotations
from . import constants


def compute_normalized_ffmi(lean_mass_kg: float, height_m: float) -> float:
    """Normalized FFMI (Kouri 1995): FFMI + 6.1*(1.8 - height_m)."""
    ffmi = lean_mass_kg / (height_m ** 2)
    return ffmi + 6.1 * (1.8 - height_m)


def ffmi_ceiling_factor(normalized_ffmi: float) -> float:
    """Throttle on further muscle gain: 1.0 below FFMI 22, linear decay to 0.0 at 25."""
    if normalized_ffmi <= 22.0:
        return 1.0
    if normalized_ffmi >= constants.FFMI_CEILING:
        return 0.0
    return (constants.FFMI_CEILING - normalized_ffmi) / (constants.FFMI_CEILING - 22.0)


_AH_PCT = {"beginner": 0.0125, "intermediate": 0.0075, "advanced": 0.00375}  # % BW / month


def aragon_helms_monthly_kg(weight_kg: float, experience: str, sex: str) -> float:
    """Monthly lean-mass gain = %BW/month (Aragon/Helms). Female absolute = 0.5x male
    (equal relative gains, lower absolute LBM; Roberts 2020 PMID 32218059)."""
    rate = weight_kg * _AH_PCT[experience]
    return rate * (0.5 if sex == "F" else 1.0)


def _sleep_mod(hrs: float) -> float:
    if hrs < 6: return 0.85
    if hrs < 7: return 0.95
    return 1.0


def _protein_mod(profile, nutrition) -> float:
    if nutrition.protein_g is None:
        return 0.95  # unknown -> mild penalty
    per_kg = nutrition.protein_g / profile.weight_kg
    if per_kg >= 1.6: return 1.0
    if per_kg >= 1.2: return 0.95
    return 0.85


def _age_mod(age: int) -> float:
    if age < 30: return 1.0
    if age < 40: return 0.95
    if age < 50: return 0.90
    return 0.80


# --- training-quality, stress, and genetic modifiers --------------------------
# All centered so the schema defaults (sets=12, intensity="moderate", stress=5,
# genetics="average") return 1.0, leaving the validated 7/7 calibration unchanged.

def _volume_mod(sets_per_week: int) -> float:
    """Resistance-training volume dose-response (Schoenfeld 2017 PMID 27433992;
    diminishing returns ~20 sets, Baz-Valle 2022 PMID 35291645)."""
    if sets_per_week < 5: return 0.80
    if sets_per_week < 10: return 0.92
    if sets_per_week < 20: return 1.00      # ~10-19 sets: the productive default range
    if sets_per_week < 25: return 1.03      # high but still productive
    return 1.00                              # >=25: junk volume, no extra benefit


def _intensity_mod(intensity: str) -> float:
    """Proximity-to-failure / effort. Conservative (no isolated RCT); moderate = baseline."""
    return {"light": 0.85, "moderate": 1.00, "intense": 1.05}[intensity]


def _stress_mod(stress_level: int) -> float:
    """Chronic stress -> cortisol -> reduced MPS/recovery (Lamon 2021 PMC7785053).
    1-10 scale, higher = more stress; <=5 (average) is neutral."""
    if stress_level <= 5: return 1.00
    if stress_level <= 7: return 0.95
    if stress_level <= 9: return 0.88
    return 0.82


def _genetic_mod(genetic_potential: str) -> float:
    """Individual variation in gain rate (Kouri 1995 FFMI variance, PMID 7496846).
    Bounded; FFMI ceiling still caps absolute lean."""
    return {"low": 0.85, "average": 1.00, "high": 1.15}[genetic_potential]


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def apply_gain_modifiers(base_kg: float, profile, training, nutrition) -> float:
    """Bounded, evidence-based multipliers on the base gain rate.

    recovery = sleep x protein x age (each <=1.0, penalties only).
    training_quality+genetics = volume x intensity x stress x genetics, with the
    combined product clamped to [0.55, 1.20] so extremes stay physiologically sane
    (and never breach the hard 'lean >1.0 kg/wk' rule; FFMI ceiling caps absolute lean).
    """
    recovery = (_sleep_mod(profile.sleep_hrs_per_night)
                * _protein_mod(profile, nutrition)
                * _age_mod(profile.age))
    quality = _clamp(
        _volume_mod(training.sets_per_muscle_per_week)
        * _intensity_mod(training.intensity)
        * _stress_mod(profile.stress_level)
        * _genetic_mod(profile.genetic_potential),
        0.55, 1.20)
    return base_kg * recovery * quality


# Fraction of a caloric surplus stored as FAT (vs lean), by training status & sex (P-ratio).
# Beginners/leaner/women partition more toward muscle (Iraki 2019; Aragon/Helms). Advanced
# trainees near their ceiling store proportionally more as fat.
_SURPLUS_FAT = {"beginner": 0.25, "intermediate": 0.40, "advanced": 0.55}


def surplus_fat_fraction(experience: str, sex: str) -> float:
    frac = _SURPLUS_FAT[experience]
    if sex == "F":
        frac *= 0.75
    return frac
