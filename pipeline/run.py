"""Orchestrate one transformation: photo + MorphSpec -> believable, identity-locked image.

Flow:  build prompt -> body mask -> [generate -> face-lock -> identity score] x N
       -> if still failing, fallback model once -> return best candidate.

Stages are injected (see Stages) so the control flow is testable without API calls;
run.py also provides default fal-backed stages via build_default_stages().
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

from .engine_bridge import MorphSpec
from .identity import IdentityPolicy, best_candidate, passes
from .prompt import build_prompt


@dataclass
class Stages:
    mask: Callable          # (photo) -> mask
    generate: Callable      # (photo, prompt, mask) -> generated image
    facelock: Callable      # (photo, generated) -> composited image (real face)
    score: Callable         # (photo, candidate) -> identity cosine
    generate_fallback: Optional[Callable] = None  # (photo, prompt, mask) -> image


@dataclass
class PipelineResult:
    image: object
    identity_score: float
    accepted: bool
    attempts: int
    used_fallback: bool
    prompt: str
    spec: MorphSpec
    candidates: List[Tuple[object, float]] = field(default_factory=list)


def _attempt(stages: Stages, photo, prompt, mask, generator) -> Tuple[object, float]:
    generated = generator(photo, prompt, mask)
    locked = stages.facelock(photo, generated)  # identity backstop, always applied
    return locked, stages.score(photo, locked)


def run_transformation(photo, spec: MorphSpec, stages: Stages,
                       policy: IdentityPolicy = IdentityPolicy()) -> PipelineResult:
    prompt = build_prompt(spec)
    mask = stages.mask(photo)

    candidates: List[Tuple[object, float]] = []
    attempts = 0
    while attempts < policy.max_attempts:
        attempts += 1
        candidates.append(_attempt(stages, photo, prompt, mask, stages.generate))
        if passes(candidates[-1][1], policy.threshold):
            break

    used_fallback = False
    best = best_candidate(candidates)
    if (best is None or not passes(best[1], policy.threshold)) and stages.generate_fallback:
        used_fallback = True
        candidates.append(_attempt(stages, photo, prompt, mask, stages.generate_fallback))
        best = best_candidate(candidates)

    image, score = best
    return PipelineResult(
        image=image, identity_score=score, accepted=passes(score, policy.threshold),
        attempts=attempts, used_fallback=used_fallback, prompt=prompt, spec=spec,
        candidates=candidates,
    )
