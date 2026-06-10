"""Persistent job store for avatar generation jobs.

Storage layout — two roots, deliberately separate:
  <media_root>/avatars/<job>/     after.jpg, orbit.mp4, master.webm, frames/, frames_mobile/
                                  (publicly served by the /outputs StaticFiles mount)
  <private_root>/avatars/<job>/   meta.json (health inputs + user key) and before.jpg
                                  (the user's raw uploaded photo) — must NEVER be web-served

Writes are atomic: write to a temp file then rename, so readers never see a
partial JSON (same guarantees as a single-file "database").
"""
from __future__ import annotations

import json
import pathlib
import tempfile
from datetime import datetime, timezone
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AvatarJobStore:
    def __init__(self, media_root: pathlib.Path, private_root: pathlib.Path) -> None:
        self._media = media_root / "avatars"
        self._private = private_root / "avatars"
        self._media.mkdir(parents=True, exist_ok=True)
        self._private.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    def job_dir(self, job: str) -> pathlib.Path:
        """Public media dir for a job (served via the static mount)."""
        return self._media / job

    def private_dir(self, job: str) -> pathlib.Path:
        """Private dir for a job: meta.json + the raw uploaded photo."""
        return self._private / job

    # ------------------------------------------------------------------
    def create(self, job: str, user: Optional[str], inputs: dict) -> dict:
        """Create a new job with status=queued and write meta.json."""
        now = _now_iso()
        meta: dict = {
            "job": job,
            "user": user,
            "status": "queued",
            "progress_pct": 0,
            "error": None,
            "created_at": now,
            "updated_at": now,
            "inputs": inputs,
            "projection": None,
            "frame_count": None,
        }
        self.job_dir(job).mkdir(parents=True, exist_ok=True)
        d = self.private_dir(job)
        d.mkdir(parents=True, exist_ok=True)
        self._write(d / "meta.json", meta)
        return meta

    # ------------------------------------------------------------------
    def update(self, job: str, **fields) -> dict:
        """Merge fields into the existing meta and persist atomically."""
        existing = self.get(job)
        if existing is None:
            raise KeyError(f"job not found: {job}")
        existing.update(fields)
        existing["updated_at"] = _now_iso()
        self._write(self.private_dir(job) / "meta.json", existing)
        return existing

    # ------------------------------------------------------------------
    def get(self, job: str) -> Optional[dict]:
        """Return the meta dict for a job, or None if it doesn't exist."""
        p = self.private_dir(job) / "meta.json"
        if not p.exists():
            return None
        return json.loads(p.read_text())

    # ------------------------------------------------------------------
    def latest_done_for_user(self, user: str) -> Optional[dict]:
        """Return the newest job with status=='done' for the given user key."""
        candidates = []
        for meta_path in self._private.glob("*/meta.json"):
            try:
                meta = json.loads(meta_path.read_text())
            except (json.JSONDecodeError, OSError):
                continue
            if meta.get("status") == "done" and meta.get("user") == user:
                candidates.append(meta)
        if not candidates:
            return None
        return max(candidates, key=lambda m: m.get("created_at", ""))

    # ------------------------------------------------------------------
    @staticmethod
    def _write(path: pathlib.Path, data: dict) -> None:
        """Atomic write: write to a sibling temp file then rename."""
        path.parent.mkdir(parents=True, exist_ok=True)
        # Write into the same directory as the target so os.rename is atomic
        # (same filesystem, no cross-device move).
        fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
        try:
            with open(fd, "w") as fh:
                json.dump(data, fh, indent=2)
            pathlib.Path(tmp_path).rename(path)
        except Exception:
            try:
                pathlib.Path(tmp_path).unlink()
            except OSError:
                pass
            raise
