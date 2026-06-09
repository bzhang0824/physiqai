"""Turn a MorphSpec into a bounded, identity-preserving image-edit prompt.

In Architecture A the prompt is the ONLY guardrail on magnitude, so it states
the engine's exact numbers and explicitly forbids exaggeration. The identity +
scene lock is appended to every prompt (face-lock is the hard backstop, but the
model should also be told not to touch the face/background).
"""
from __future__ import annotations

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
    "bodybuilder, no oil, no vascularity, no exaggeration."
)


def _body(spec: MorphSpec) -> str:
    mo = spec.months
    bf0, bf1 = round(spec.bf_before), round(spec.bf_after)
    lb = round(abs(spec.weight_delta_lb))
    lean = round(spec.lean_delta_lb)

    if spec.direction == "cut":
        return (
            f"Edit this exact photo to show the SAME person after a realistic {mo}-month "
            f"fat-loss program: body fat from ~{bf0}% down to ~{bf1}% (about {lb} lb lighter), "
            f"a tighter, slimmer waist and more visible muscle definition while keeping the "
            f"same muscle size."
        )
    if spec.direction == "gain":
        return (
            f"Edit this exact photo to show the SAME person after {mo} months of training: add "
            f"about {abs(lean)} lb of lean muscle (fuller chest, shoulders, arms and back), "
            f"body fat staying around ~{bf1}%."
        )
    if spec.direction == "recomp":
        return (
            f"Edit this exact photo to show the SAME person after a {mo}-month body recomposition: "
            f"lose fat (body fat ~{bf0}% to ~{bf1}%) while adding a little lean muscle, for a "
            f"leaner, slightly more muscular and more defined look at about the same body weight."
        )
    # maintain
    return (
        f"Edit this exact photo with only minimal, subtle changes — the person is maintaining "
        f"their current physique over {mo} months. Keep body fat ~{bf1}% and the same muscle size; "
        f"essentially the same body."
    )


def build_prompt(spec: MorphSpec) -> str:
    return f"{_body(spec)} {_NO_EXAGGERATION} {_LOCK}"
