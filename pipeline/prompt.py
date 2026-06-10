"""Turn a MorphSpec into a bounded, identity-preserving image-edit prompt.

Architecture A's prompt is the ONLY natural-language guardrail on magnitude, so
it must faithfully translate the engine's per-body-part numbers — not hand-wave
them. The engine already folds every input lever (training volume, intensity,
genetics, sleep, stress, nutrition) into concrete measurement deltas
(chest/arms/waist/thighs/hips, in cm); this builder renders those deltas as
calibrated visual instructions so the image neither under- nor over-shoots.

The identity + scene lock and the anti-exaggeration clause are appended to every
prompt (face-lock is the hard backstop, but the model is told too).
"""
from __future__ import annotations

from typing import List

from .engine_bridge import MorphSpec

# Hard identity + scene lock — appended to every prompt.
_LOCK = (
    "CRITICAL: keep the face, hair, skin tone and identity EXACTLY the same; "
    "keep the same pose, body position, clothing, background, lighting, camera "
    "angle and image quality. Photorealistic, natural result."
)

# Anti-exaggeration clause — keeps results believable, not stage-physique fantasy.
_NO_EXAGGERATION = (
    "Natural, realistic natural-lifter result, NOT a stage or professional "
    "bodybuilder, no oil, no extreme vascularity, no exaggeration."
)

# Per-region visual mapping, in head-to-toe order. For each: the body-part label,
# the phrase when the measurement GROWS (positive cm delta), and when it SHRINKS.
_REGIONS = [
    ("chest_cm",  "chest and upper back", "fuller and broader",      "leaner and flatter"),
    ("arms_cm",   "arms",                 "fuller with more muscle", "leaner"),
    ("waist_cm",  "waist",                "thicker",                 "tighter and slimmer"),
    ("hips_cm",   "hips and glutes",      "fuller",                  "tighter"),
    ("thighs_cm", "thighs",               "fuller and stronger",     "leaner"),
]

# Below this many cm a change isn't worth instructing the model on.
_NEGLIGIBLE_CM = 0.4


def _mag_adverb(cm: float) -> str:
    """Magnitude → calibrated language. This is the anti-over/undershoot lever."""
    cm = abs(cm)
    if cm < 1.5:
        return "slightly"
    if cm < 3.0:
        return "visibly"
    return "clearly"


def _region_phrases(measurements_cm: dict) -> List[str]:
    """One calibrated visual instruction per non-negligible body-part delta."""
    phrases: List[str] = []
    for key, label, grow, shrink in _REGIONS:
        delta = measurements_cm.get(key)
        if delta is None or abs(delta) < _NEGLIGIBLE_CM:
            continue
        adverb = _mag_adverb(delta)
        descriptor = grow if delta > 0 else shrink
        cm = round(abs(delta))
        if cm >= 1:
            phrases.append(f"{label} {adverb} {descriptor} (~{cm} cm)")
        else:
            phrases.append(f"{label} {adverb} {descriptor}")
    return phrases


def _body(spec: MorphSpec) -> str:
    mo = spec.months
    bf0, bf1 = round(spec.bf_before), round(spec.bf_after)
    lb = round(abs(spec.weight_delta_lb))
    lean = round(abs(spec.lean_delta_lb))
    regions = _region_phrases(spec.measurements_cm)
    region_clause = f"Specifically: {'; '.join(regions)}." if regions else ""

    if spec.direction == "cut":
        intro = (
            f"Edit this exact photo to show the SAME person after a realistic {mo}-month "
            f"fat-loss program. Body fat from ~{bf0}% down to ~{bf1}% (about {lb} lb lighter), "
            f"keeping the same muscle size."
        )
        calib = (
            f"The fat loss should be clearly visible but believable for {mo} months — a tighter "
            f"waist and more defined muscle, not a dramatic crash transformation."
        )
    elif spec.direction == "gain":
        intro = (
            f"Edit this exact photo to show the SAME person after {mo} months of natural "
            f"resistance training: about {lean} lb of added lean muscle, body fat around ~{bf1}%."
        )
        calib = (
            f"This is {mo} months of natural muscle growth — a visible but modest improvement, "
            f"not a multi-year or enhanced bodybuilder transformation."
        )
    elif spec.direction == "recomp":
        intro = (
            f"Edit this exact photo to show the SAME person after a {mo}-month body recomposition: "
            f"lose fat (body fat ~{bf0}% to ~{bf1}%) while adding a little lean muscle, at about the "
            f"same body weight."
        )
        calib = (
            "The result is leaner and slightly more muscular and defined — a subtle, believable "
            "recomposition, not a dramatic before/after."
        )
    else:  # maintain
        intro = (
            f"Edit this exact photo with only minimal, subtle changes — the person is maintaining "
            f"their current physique over {mo} months. Body fat ~{bf1}%, same muscle size, "
            f"essentially the same body."
        )
        calib = ""

    return " ".join(p for p in (intro, region_clause, calib) if p)


def build_prompt(spec: MorphSpec) -> str:
    return f"{_body(spec)} {_NO_EXAGGERATION} {_LOCK}"
