"""In-memory per-IP rate limiting for cost-sensitive endpoints (fal.ai spend).

A sliding-window log keyed by client IP. This is intentionally simple and
single-process: counters live in memory, reset on redeploy, and are not shared
across replicas — sufficient for the current single-instance Railway MVP. For a
multi-instance deployment, swap `SlidingWindowLimiter`'s store for Redis.

Note: an IP limit slows scripted abuse from one source but cannot stop an
attacker rotating IPs — that needs auth/captcha (out of scope here). The point
is to cap casual spam of the unauthenticated image-generation endpoint so a
single client can't run up the fal.ai bill.
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict
from typing import Callable, Optional

from fastapi import HTTPException, Request


def client_ip(request: Request) -> str:
    """Best-effort real client IP.

    Behind a proxy (Railway), the originating IP is the first entry of
    X-Forwarded-For; fall back to the socket peer for local/direct calls.
    """
    xff = request.headers.get("x-forwarded-for")
    if xff:
        first = xff.split(",")[0].strip()
        if first:
            return first
    return request.client.host if request.client else "unknown"


class SlidingWindowLimiter:
    """Allow at most `max_requests` per `window_s` seconds per key."""

    def __init__(self, max_requests: int, window_s: int):
        self.max = max_requests
        self.window = window_s
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def check(self, key: str, *, now: Optional[float] = None) -> tuple[bool, int]:
        """Record a hit for `key`. Returns (allowed, retry_after_seconds)."""
        now = time.time() if now is None else now
        cutoff = now - self.window
        with self._lock:
            recent = [t for t in self._hits[key] if t > cutoff]
            if len(recent) >= self.max:
                # Oldest hit in the window determines when a slot frees up.
                retry_after = int(recent[0] + self.window - now) + 1
                self._hits[key] = recent
                return False, max(retry_after, 1)
            recent.append(now)
            if recent:
                self._hits[key] = recent
            else:
                self._hits.pop(key, None)
            return True, 0


def rate_limit_dependency(limiter: SlidingWindowLimiter, label: str) -> Callable:
    """Build a FastAPI dependency that 429s when the per-IP limit is exceeded."""

    def _dep(request: Request) -> None:
        allowed, retry_after = limiter.check(client_ip(request))
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=f"Too many {label} requests from your network. "
                       f"Please try again in about {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)},
            )

    return _dep
