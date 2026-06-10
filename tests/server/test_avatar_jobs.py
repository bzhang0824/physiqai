"""TDD for server.avatar_jobs.AvatarJobStore.

All tests use a tmp_path fixture — no shared state, no real DB.
"""
from __future__ import annotations

import json
import pathlib
import sys
import time

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from server.avatar_jobs import AvatarJobStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _inputs():
    return dict(age=24, sex="M", height_in=72, weight_lb=192, bf_pct=11,
                goal="fat_loss", weeks=26)


def _store(tmp_path: pathlib.Path) -> AvatarJobStore:
    return AvatarJobStore(tmp_path / "media", tmp_path / "private")


# ---------------------------------------------------------------------------
# create / get roundtrip
# ---------------------------------------------------------------------------

def test_create_get_roundtrip(tmp_path):
    store = _store(tmp_path)
    meta = store.create("abc123", "user1", _inputs())
    got = store.get("abc123")
    assert got is not None
    assert got["job"] == "abc123"
    assert got["user"] == "user1"
    assert got["status"] == "queued"
    assert got["progress_pct"] == 0
    assert got["error"] is None
    assert got["projection"] is None
    assert got["frame_count"] is None
    assert got["inputs"] == _inputs()


def test_create_writes_meta_json_to_disk(tmp_path):
    store = _store(tmp_path)
    store.create("abc123", None, _inputs())
    p = store.private_dir("abc123") / "meta.json"
    assert p.exists()
    data = json.loads(p.read_text())
    assert data["job"] == "abc123"


def test_get_missing_returns_none(tmp_path):
    store = _store(tmp_path)
    assert store.get("nonexistent") is None


def test_create_with_null_user(tmp_path):
    store = _store(tmp_path)
    meta = store.create("job1", None, _inputs())
    assert meta["user"] is None
    assert store.get("job1")["user"] is None


def test_create_returns_initial_meta_dict(tmp_path):
    store = _store(tmp_path)
    meta = store.create("j1", "u1", _inputs())
    assert isinstance(meta, dict)
    assert meta["status"] == "queued"


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------

def test_update_merges_fields(tmp_path):
    store = _store(tmp_path)
    store.create("j1", "u1", _inputs())
    updated = store.update("j1", status="after_still", progress_pct=5)
    assert updated["status"] == "after_still"
    assert updated["progress_pct"] == 5
    assert updated["user"] == "u1"  # original field preserved


def test_update_bumps_updated_at(tmp_path):
    store = _store(tmp_path)
    meta = store.create("j1", "u1", _inputs())
    original_ts = meta["updated_at"]
    # Ensure at least 1 ms passes so timestamps differ
    time.sleep(0.01)
    updated = store.update("j1", status="orbiting")
    assert updated["updated_at"] > original_ts


def test_update_persists_to_disk(tmp_path):
    store = _store(tmp_path)
    store.create("j1", "u1", _inputs())
    store.update("j1", status="done", frame_count=96,
                 projection={"direction": "cut", "weight_after_lb": 180.0})
    on_disk = json.loads((store.private_dir("j1") / "meta.json").read_text())
    assert on_disk["status"] == "done"
    assert on_disk["frame_count"] == 96
    assert on_disk["projection"]["direction"] == "cut"


def test_update_missing_job_raises(tmp_path):
    store = _store(tmp_path)
    with pytest.raises(KeyError):
        store.update("does_not_exist", status="done")


def test_update_atomic_no_partial_write(tmp_path):
    """Verify the tmp+rename write: file must be valid JSON after update."""
    store = _store(tmp_path)
    store.create("j1", None, _inputs())
    for status in ["after_still", "orbiting", "matting", "extracting", "done"]:
        store.update("j1", status=status)
        raw = (store.private_dir("j1") / "meta.json").read_text()
        parsed = json.loads(raw)  # would raise if partial
        assert parsed["status"] == status


# ---------------------------------------------------------------------------
# latest_done_for_user
# ---------------------------------------------------------------------------

def test_latest_done_for_user_picks_newest_done(tmp_path):
    store = _store(tmp_path)
    store.create("j1", "alice", _inputs())
    time.sleep(0.02)
    store.create("j2", "alice", _inputs())

    store.update("j1", status="done")
    store.update("j2", status="done")

    latest = store.latest_done_for_user("alice")
    assert latest is not None
    assert latest["job"] == "j2"


def test_latest_done_ignores_non_done_jobs(tmp_path):
    store = _store(tmp_path)
    store.create("j1", "alice", _inputs())
    time.sleep(0.02)
    store.create("j2", "alice", _inputs())

    store.update("j1", status="done")
    store.update("j2", status="orbiting")   # not done

    latest = store.latest_done_for_user("alice")
    assert latest["job"] == "j1"


def test_latest_done_wrong_user_returns_none(tmp_path):
    store = _store(tmp_path)
    store.create("j1", "alice", _inputs())
    store.update("j1", status="done")

    assert store.latest_done_for_user("bob") is None


def test_latest_done_no_jobs_returns_none(tmp_path):
    store = _store(tmp_path)
    assert store.latest_done_for_user("alice") is None


def test_latest_done_filters_by_user(tmp_path):
    store = _store(tmp_path)
    store.create("j1", "alice", _inputs())
    store.create("j2", "bob", _inputs())
    store.update("j1", status="done")
    store.update("j2", status="done")

    alice_latest = store.latest_done_for_user("alice")
    assert alice_latest["job"] == "j1"

    bob_latest = store.latest_done_for_user("bob")
    assert bob_latest["job"] == "j2"


# ---------------------------------------------------------------------------
# job_dir
# ---------------------------------------------------------------------------

def test_job_dir_returns_correct_path(tmp_path):
    store = _store(tmp_path)
    store.create("myjob", None, _inputs())
    d = store.job_dir("myjob")
    assert d == tmp_path / "media" / "avatars" / "myjob"
    assert d.is_dir()


def test_job_dir_for_unknown_job_does_not_create_dir(tmp_path):
    store = _store(tmp_path)
    d = store.job_dir("ghost")
    assert not d.exists()


# ---------------------------------------------------------------------------
# edge cases
# ---------------------------------------------------------------------------

def test_multiple_jobs_do_not_interfere(tmp_path):
    store = _store(tmp_path)
    store.create("j1", "u1", dict(weeks=4))
    store.create("j2", "u2", dict(weeks=12))
    store.update("j1", status="done")

    assert store.get("j1")["status"] == "done"
    assert store.get("j2")["status"] == "queued"
    assert store.get("j2")["inputs"]["weeks"] == 12


def test_create_initialises_timestamps(tmp_path):
    store = _store(tmp_path)
    meta = store.create("j1", None, _inputs())
    assert "created_at" in meta
    assert "updated_at" in meta
    # Both should be recent ISO-8601 strings ending with +00:00
    assert meta["created_at"].endswith("+00:00")
    assert meta["created_at"] == meta["updated_at"]
