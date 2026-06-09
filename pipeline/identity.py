"""Identity gate: decide whether a generated image is recognizably the same person.

Scoring is a facenet cosine-similarity model call (see scorer wiring in run.py).
Everything here is the pure decision policy so it can be tested deterministically.

Threshold rationale: facenet cosine >= 0.85 is the commonly used "same identity"
bar; below it we retry, then fall back to a different edit model, then rely on the
face-lock composite as the hard backstop.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

DEFAULT_THRESHOLD = 0.85


@dataclass
class IdentityPolicy:
    threshold: float = DEFAULT_THRESHOLD
    max_attempts: int = 3


def passes(score: float, threshold: float = DEFAULT_THRESHOLD) -> bool:
    return score >= threshold


def next_action(best_score: float, attempts_used: int, policy: IdentityPolicy) -> str:
    """Return one of: 'accept', 'retry', 'fallback'."""
    if passes(best_score, policy.threshold):
        return "accept"
    if attempts_used < policy.max_attempts:
        return "retry"
    return "fallback"


def best_candidate(candidates: List[Tuple[object, float]]) -> Optional[Tuple[object, float]]:
    """Pick the highest-scoring (image, score) pair; None if empty."""
    if not candidates:
        return None
    return max(candidates, key=lambda c: c[1])
