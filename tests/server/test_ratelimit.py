"""Tests for server/ratelimit.py and the CORS allowlist on server/app.

Hermetic — no network. The limiter is exercised via its `now` hook and via a
tiny FastAPI app so we never call the real (paid) /transform endpoint.
"""
from __future__ import annotations

import pathlib
import sys

import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from server.ratelimit import SlidingWindowLimiter, client_ip, rate_limit_dependency


# ---------------------------------------------------------------------------
# SlidingWindowLimiter
# ---------------------------------------------------------------------------

def test_allows_up_to_max_then_blocks():
    lim = SlidingWindowLimiter(max_requests=3, window_s=60)
    assert lim.check("ip", now=1000)[0] is True
    assert lim.check("ip", now=1001)[0] is True
    assert lim.check("ip", now=1002)[0] is True
    allowed, retry = lim.check("ip", now=1003)
    assert allowed is False
    assert retry > 0


def test_window_expiry_frees_a_slot():
    lim = SlidingWindowLimiter(max_requests=1, window_s=60)
    assert lim.check("ip", now=1000)[0] is True
    assert lim.check("ip", now=1030)[0] is False      # within window → blocked
    assert lim.check("ip", now=1061)[0] is True        # window passed → allowed


def test_keys_are_isolated_per_ip():
    lim = SlidingWindowLimiter(max_requests=1, window_s=60)
    assert lim.check("ip-a", now=1000)[0] is True
    assert lim.check("ip-b", now=1000)[0] is True       # different IP, own bucket
    assert lim.check("ip-a", now=1000)[0] is False


def test_retry_after_reflects_oldest_hit():
    lim = SlidingWindowLimiter(max_requests=1, window_s=100)
    lim.check("ip", now=1000)
    _, retry = lim.check("ip", now=1010)
    # oldest hit at 1000, window 100 → frees at 1100, ~90s from now (1010)
    assert 85 <= retry <= 95


# ---------------------------------------------------------------------------
# client_ip
# ---------------------------------------------------------------------------

def test_client_ip_prefers_forwarded_for():
    app = FastAPI()

    @app.get("/ip")
    def ip(request: Request):
        return {"ip": client_ip(request)}

    c = TestClient(app)
    r = c.get("/ip", headers={"X-Forwarded-For": "203.0.113.7, 10.0.0.1"})
    assert r.json()["ip"] == "203.0.113.7"  # first entry = real client


def test_client_ip_falls_back_to_peer():
    app = FastAPI()

    @app.get("/ip")
    def ip(request: Request):
        return {"ip": client_ip(request)}

    c = TestClient(app)
    r = c.get("/ip")  # no XFF → falls back to socket peer (TestClient = "testclient")
    assert r.json()["ip"]  # non-empty


# ---------------------------------------------------------------------------
# rate_limit_dependency (429 behaviour)
# ---------------------------------------------------------------------------

def _limited_app(max_requests: int):
    lim = SlidingWindowLimiter(max_requests=max_requests, window_s=3600)
    app = FastAPI()

    @app.get("/limited", dependencies=[Depends(rate_limit_dependency(lim, "test"))])
    def limited():
        return {"ok": True}

    return app


def test_dependency_returns_429_after_limit():
    c = TestClient(_limited_app(max_requests=2))
    h = {"X-Forwarded-For": "198.51.100.5"}
    assert c.get("/limited", headers=h).status_code == 200
    assert c.get("/limited", headers=h).status_code == 200
    blocked = c.get("/limited", headers=h)
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers
    assert int(blocked.headers["Retry-After"]) > 0


def test_dependency_isolated_per_ip():
    c = TestClient(_limited_app(max_requests=1))
    assert c.get("/limited", headers={"X-Forwarded-For": "1.1.1.1"}).status_code == 200
    # different IP not affected by the first IP hitting its limit
    assert c.get("/limited", headers={"X-Forwarded-For": "2.2.2.2"}).status_code == 200
    assert c.get("/limited", headers={"X-Forwarded-For": "1.1.1.1"}).status_code == 429


# ---------------------------------------------------------------------------
# CORS allowlist on the real app
# ---------------------------------------------------------------------------

def test_cors_allows_listed_origin():
    import server.app as app_module

    c = TestClient(app_module.app)
    origin = app_module.ALLOWED_ORIGINS[0]
    r = c.get("/health", headers={"Origin": origin})
    assert r.headers.get("access-control-allow-origin") == origin


def test_cors_blocks_unlisted_origin():
    import server.app as app_module

    c = TestClient(app_module.app)
    r = c.get("/health", headers={"Origin": "https://evil.example.com"})
    # Starlette only echoes ACAO for allowed origins; absent == not allowed.
    assert r.headers.get("access-control-allow-origin") != "https://evil.example.com"
    assert "access-control-allow-origin" not in {k.lower() for k in r.headers}
