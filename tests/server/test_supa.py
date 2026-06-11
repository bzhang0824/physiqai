"""Hermetic unit tests for server/supa.py.

All tests monkeypatch os.environ for the required env vars and inject a fake
httpx.Client so no real network traffic occurs.
"""
from __future__ import annotations

import json
import os
import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import server.supa as supa


# ---------------------------------------------------------------------------
# Fake httpx client helpers
# ---------------------------------------------------------------------------

class FakeResponse:
    def __init__(self, status_code: int, body, *, headers: dict | None = None):
        self.status_code = status_code
        self._body = body
        self.headers = headers or {}

    def json(self):
        return self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            import httpx
            # Minimal httpx.HTTPStatusError
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}",
                request=None,  # type: ignore[arg-type]
                response=self,  # type: ignore[arg-type]
            )


class FakeClient:
    """Minimal synchronous httpx.Client stub that records calls."""

    def __init__(self, responses: list[FakeResponse]):
        self._responses = list(responses)
        self.calls: list[dict] = []

    def get(self, url, **kwargs) -> FakeResponse:
        self.calls.append({"method": "GET", "url": url, **kwargs})
        return self._pop()

    def post(self, url, **kwargs) -> FakeResponse:
        self.calls.append({"method": "POST", "url": url, **kwargs})
        return self._pop()

    def patch(self, url, **kwargs) -> FakeResponse:
        self.calls.append({"method": "PATCH", "url": url, **kwargs})
        return self._pop()

    def delete(self, url, **kwargs) -> FakeResponse:
        self.calls.append({"method": "DELETE", "url": url, **kwargs})
        return self._pop()

    def request(self, method, url, **kwargs) -> FakeResponse:
        self.calls.append({"method": method, "url": url, **kwargs})
        return self._pop()

    def close(self):
        pass

    def _pop(self) -> FakeResponse:
        if not self._responses:
            raise AssertionError("FakeClient ran out of responses")
        return self._responses.pop(0)


# ---------------------------------------------------------------------------
# Env fixture
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def supa_env(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "fake-service-key")


# ---------------------------------------------------------------------------
# verify_token
# ---------------------------------------------------------------------------

def test_verify_token_valid():
    body = {"id": "user-uuid-123", "email": "alice@example.com"}
    client = FakeClient([FakeResponse(200, body)])
    result = supa.verify_token("valid-token", _client=client)
    assert result == {"id": "user-uuid-123", "email": "alice@example.com"}


def test_verify_token_invalid_401():
    client = FakeClient([FakeResponse(401, {"message": "invalid JWT"})])
    result = supa.verify_token("bad-token", _client=client)
    assert result is None


def test_verify_token_uses_correct_url():
    body = {"id": "uid", "email": "e@e.com"}
    client = FakeClient([FakeResponse(200, body)])
    supa.verify_token("tok", _client=client)
    assert client.calls[0]["url"] == "https://fake.supabase.co/auth/v1/user"


def test_verify_token_passes_bearer_header():
    body = {"id": "uid", "email": "e@e.com"}
    client = FakeClient([FakeResponse(200, body)])
    supa.verify_token("mytoken", _client=client)
    headers = client.calls[0]["headers"]
    assert headers["Authorization"] == "Bearer mytoken"
    assert headers["apikey"] == "fake-service-key"


def test_verify_token_missing_env(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="SUPABASE_URL"):
        supa.verify_token("tok")


def test_verify_token_missing_service_key(monkeypatch):
    monkeypatch.delenv("SUPABASE_SERVICE_KEY", raising=False)
    with pytest.raises(RuntimeError, match="SUPABASE_SERVICE_KEY"):
        supa.verify_token("tok")


# ---------------------------------------------------------------------------
# count_user_avatars
# ---------------------------------------------------------------------------

def test_count_user_avatars_content_range():
    # PostgREST returns count in Content-Range header
    client = FakeClient([FakeResponse(200, [], headers={"content-range": "0-2/3"})])
    assert supa.count_user_avatars("uid-abc", _client=client) == 3


def test_count_user_avatars_zero():
    client = FakeClient([FakeResponse(200, [], headers={"content-range": "*/0"})])
    assert supa.count_user_avatars("uid-abc", _client=client) == 0


def test_count_user_avatars_fallback_to_len():
    # If Content-Range header is missing, fall back to len(rows)
    rows = [{"id": "r1"}, {"id": "r2"}]
    client = FakeClient([FakeResponse(200, rows)])
    assert supa.count_user_avatars("uid-abc", _client=client) == 2


# ---------------------------------------------------------------------------
# get_avatar_limit
# ---------------------------------------------------------------------------

def test_get_avatar_limit_profile_exists():
    client = FakeClient([FakeResponse(200, [{"avatar_limit": 5}])])
    assert supa.get_avatar_limit("uid-abc", _client=client) == 5


def test_get_avatar_limit_no_profile_defaults_to_1():
    client = FakeClient([FakeResponse(200, [])])
    assert supa.get_avatar_limit("uid-abc", _client=client) == 1


def test_get_avatar_limit_missing_key_defaults_to_1():
    client = FakeClient([FakeResponse(200, [{}])])
    assert supa.get_avatar_limit("uid-abc", _client=client) == 1


# ---------------------------------------------------------------------------
# insert_avatar
# ---------------------------------------------------------------------------

def test_insert_avatar_returns_row():
    record = {"job": "abc123", "user_id": "uid", "status": "queued"}
    returned = [{"id": "row-uuid", **record}]
    client = FakeClient([FakeResponse(201, returned)])
    result = supa.insert_avatar(record, _client=client)
    assert result["id"] == "row-uuid"


def test_insert_avatar_uses_prefer_header():
    record = {"job": "j", "user_id": "u", "status": "queued"}
    client = FakeClient([FakeResponse(201, [record])])
    supa.insert_avatar(record, _client=client)
    headers = client.calls[0]["headers"]
    assert headers.get("Prefer") == "return=representation"


def test_insert_avatar_empty_response_returns_input():
    record = {"job": "j", "user_id": "u"}
    client = FakeClient([FakeResponse(201, [])])
    result = supa.insert_avatar(record, _client=client)
    assert result == record


# ---------------------------------------------------------------------------
# update_avatar
# ---------------------------------------------------------------------------

def test_update_avatar_sends_patch():
    client = FakeClient([FakeResponse(204, None)])
    # 204 should not raise
    supa.update_avatar("job123", {"status": "done"}, _client=client)
    call = client.calls[0]
    assert call["method"] == "PATCH"
    assert call["params"] == {"job": "eq.job123"}
    assert call["json"] == {"status": "done"}


# ---------------------------------------------------------------------------
# get_avatar_by_job
# ---------------------------------------------------------------------------

def test_get_avatar_by_job_found():
    row = {"job": "j123", "status": "done"}
    client = FakeClient([FakeResponse(200, [row])])
    result = supa.get_avatar_by_job("j123", _client=client)
    assert result == row


def test_get_avatar_by_job_not_found():
    client = FakeClient([FakeResponse(200, [])])
    result = supa.get_avatar_by_job("missing", _client=client)
    assert result is None


# ---------------------------------------------------------------------------
# latest_done_for_user
# ---------------------------------------------------------------------------

def test_latest_done_for_user_returns_row():
    row = {"job": "j1", "user_id": "uid", "status": "done"}
    client = FakeClient([FakeResponse(200, [row])])
    result = supa.latest_done_for_user("uid", _client=client)
    assert result == row


def test_latest_done_for_user_none_when_empty():
    client = FakeClient([FakeResponse(200, [])])
    result = supa.latest_done_for_user("uid", _client=client)
    assert result is None


def test_latest_done_for_user_query_params():
    client = FakeClient([FakeResponse(200, [])])
    supa.latest_done_for_user("myuid", _client=client)
    params = client.calls[0]["params"]
    assert params["user_id"] == "eq.myuid"
    assert params["status"] == "eq.done"
    assert params["order"] == "created_at.desc"
    assert params["limit"] == "1"


# ---------------------------------------------------------------------------
# Account deletion helpers
# ---------------------------------------------------------------------------

def test_list_user_avatar_jobs_returns_job_ids():
    client = FakeClient([FakeResponse(200, [{"job": "job-a"}, {"job": "job-b"}, {"job": None}])])
    jobs = supa.list_user_avatar_jobs("uid-1", _client=client)
    assert jobs == ["job-a", "job-b"]
    assert client.calls[0]["params"]["user_id"] == "eq.uid-1"
    assert client.calls[0]["params"]["select"] == "job"


def test_delete_user_data_rows_hits_all_three_tables():
    client = FakeClient([FakeResponse(204, None), FakeResponse(204, None), FakeResponse(204, None)])
    supa.delete_user_data_rows("uid-9", _client=client)
    urls = [c["url"] for c in client.calls]
    assert urls == [
        "https://fake.supabase.co/rest/v1/checkins",
        "https://fake.supabase.co/rest/v1/avatars",
        "https://fake.supabase.co/rest/v1/profiles",
    ]
    # checkins/avatars scoped by user_id; profiles by id
    assert client.calls[0]["params"] == {"user_id": "eq.uid-9"}
    assert client.calls[2]["params"] == {"id": "eq.uid-9"}
    assert all(c["method"] == "DELETE" for c in client.calls)


def test_delete_auth_user_uses_admin_endpoint():
    client = FakeClient([FakeResponse(200, {})])
    supa.delete_auth_user("uid-7", _client=client)
    assert client.calls[0]["url"] == "https://fake.supabase.co/auth/v1/admin/users/uid-7"
    assert client.calls[0]["method"] == "DELETE"


def test_delete_auth_user_tolerates_404():
    client = FakeClient([FakeResponse(404, {"msg": "not found"})])
    # Should not raise — deleting an already-gone user is fine (idempotent).
    supa.delete_auth_user("ghost", _client=client)


# ---------------------------------------------------------------------------
# insert_workout_log
# ---------------------------------------------------------------------------

def test_insert_workout_log_returns_row():
    record = {"user_id": "uid-1", "note": "leg day"}
    returned = [{"id": "log-uuid", **record, "created_at": "2025-01-01T00:00:00Z"}]
    client = FakeClient([FakeResponse(201, returned)])
    result = supa.insert_workout_log(record, _client=client)
    assert result["id"] == "log-uuid"


def test_insert_workout_log_uses_prefer_header():
    record = {"user_id": "uid-1"}
    client = FakeClient([FakeResponse(201, [record])])
    supa.insert_workout_log(record, _client=client)
    assert client.calls[0]["headers"].get("Prefer") == "return=representation"


def test_insert_workout_log_empty_response_returns_input():
    record = {"user_id": "uid-1", "note": "hi"}
    client = FakeClient([FakeResponse(201, [])])
    result = supa.insert_workout_log(record, _client=client)
    assert result == record


# ---------------------------------------------------------------------------
# list_workout_logs
# ---------------------------------------------------------------------------

def test_list_workout_logs_basic():
    rows = [{"id": "l1", "user_id": "uid-1"}, {"id": "l2", "user_id": "uid-1"}]
    client = FakeClient([FakeResponse(200, rows)])
    result = supa.list_workout_logs("uid-1", _client=client)
    assert result == rows


def test_list_workout_logs_query_params():
    client = FakeClient([FakeResponse(200, [])])
    supa.list_workout_logs("uid-xyz", limit=20, _client=client)
    params = client.calls[0]["params"]
    assert params["user_id"] == "eq.uid-xyz"
    assert params["order"] == "created_at.desc"
    assert params["limit"] == "20"
    assert "created_at" not in params  # since_iso not provided


def test_list_workout_logs_with_since_iso():
    client = FakeClient([FakeResponse(200, [])])
    supa.list_workout_logs("uid-2", since_iso="2025-01-01T00:00:00Z", _client=client)
    params = client.calls[0]["params"]
    assert params["created_at"] == "gte.2025-01-01T00:00:00Z"


# ---------------------------------------------------------------------------
# delete_workout_log
# ---------------------------------------------------------------------------

def test_delete_workout_log_returns_true_when_row_deleted():
    row = {"id": "log-1", "user_id": "uid-1"}
    client = FakeClient([FakeResponse(200, [row])])
    result = supa.delete_workout_log("log-1", "uid-1", _client=client)
    assert result is True


def test_delete_workout_log_returns_false_when_no_row():
    client = FakeClient([FakeResponse(200, [])])
    result = supa.delete_workout_log("no-such", "uid-1", _client=client)
    assert result is False


def test_delete_workout_log_uses_both_id_and_user_id():
    client = FakeClient([FakeResponse(200, [])])
    supa.delete_workout_log("log-7", "uid-7", _client=client)
    params = client.calls[0]["params"]
    assert params["id"] == "eq.log-7"
    assert params["user_id"] == "eq.uid-7"


def test_delete_workout_log_uses_prefer_header():
    client = FakeClient([FakeResponse(200, [])])
    supa.delete_workout_log("log-8", "uid-8", _client=client)
    assert client.calls[0]["headers"].get("Prefer") == "return=representation"


# ---------------------------------------------------------------------------
# list_avatars_for_user
# ---------------------------------------------------------------------------

def test_list_avatars_for_user_sends_correct_params():
    client = FakeClient([FakeResponse(200, [])])
    supa.list_avatars_for_user("uid-av", limit=25, _client=client)
    params = client.calls[0]["params"]
    assert params["user_id"] == "eq.uid-av"
    assert params["status"] == "neq.failed"
    assert params["order"] == "created_at.desc"
    assert params["limit"] == "25"


def test_list_avatars_for_user_returns_rows():
    rows = [{"job": "j1"}, {"job": "j2"}]
    client = FakeClient([FakeResponse(200, rows)])
    result = supa.list_avatars_for_user("uid-av", _client=client)
    assert result == rows
