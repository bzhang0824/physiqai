"""Science-grounded constants for the Governor. Citations inline.
Primary sources: docs/PHYSIOLOGY_SOURCES.md, docs/NUTRITION_RESEARCH.md."""

# Caloric surplus over TDEE by experience x lean preference (kcal/day).
# Iraki et al. 2019 (PMC6680710): smaller surplus -> leaner gains.
SURPLUS_BY_EXPERIENCE = {
    "beginner":     {"standard": 400, "lean_bulk": 200, "aggressive_bulk": 600},
    "intermediate": {"standard": 300, "lean_bulk": 150, "aggressive_bulk": 500},
    "advanced":     {"standard": 200, "lean_bulk": 100, "aggressive_bulk": 350},
}

# Essential body-fat floor (hard physiological stop) and practical (sustainable) floor, by sex.
ESSENTIAL_FAT_FLOOR = {"M": 5.0, "F": 13.0}
PRACTICAL_FAT_FLOOR = {"M": 7.0, "F": 16.0}

# Natural normalized-FFMI ceiling (Kouri et al. 1995, PMID 7496846).
FFMI_CEILING = 25.0
FFMI_WARN = 24.0

# 1 kg of fat ~= 7700 kcal (Forbes). Used internally (metric).
KCAL_PER_KG_FAT = 7700.0
