"""TDD for pipeline.identity: the identity-gate decision/retry policy.

The cosine *scoring* is a model call (facenet); the DECISION logic — pass/fail,
when to retry, when to fall back, which candidate to keep — is pure and tested here.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from pipeline.identity import IdentityPolicy, best_candidate, next_action, passes


def test_passes_at_or_above_threshold():
    assert passes(0.85) is True
    assert passes(0.90) is True


def test_fails_below_threshold():
    assert passes(0.84) is False


def test_accept_when_score_meets_threshold():
    pol = IdentityPolicy(threshold=0.85, max_attempts=3)
    assert next_action(best_score=0.88, attempts_used=1, policy=pol) == "accept"


def test_retry_when_below_threshold_and_attempts_remain():
    pol = IdentityPolicy(threshold=0.85, max_attempts=3)
    assert next_action(best_score=0.70, attempts_used=1, policy=pol) == "retry"


def test_fallback_when_attempts_exhausted_on_primary():
    pol = IdentityPolicy(threshold=0.85, max_attempts=3)
    # used all primary attempts, still failing -> switch model/strategy
    assert next_action(best_score=0.70, attempts_used=3, policy=pol) == "fallback"


def test_best_candidate_picks_highest_score():
    cands = [("imgA", 0.71), ("imgB", 0.88), ("imgC", 0.83)]
    img, score = best_candidate(cands)
    assert img == "imgB"
    assert score == 0.88


def test_best_candidate_empty_returns_none():
    assert best_candidate([]) is None
