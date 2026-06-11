"""PhysiqAI backend (thin slice).

Wraps the proven pipeline so the mobile app can run the full loop:
  photo + stats  ->  engine projection + face-locked before/after image.

Reuses the smoke-tested path (generate_nano_banana + apply_facelock); the facenet
auto-gate / full orchestrator is deferred (needs torch). FAL_KEY is read server-side
only (os.getenv) and never leaves this process.

Run:  bash server/run.sh   (uvicorn on 0.0.0.0:8000)
"""
from __future__ import annotations

import logging
import os
import pathlib
import shutil
import sys
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import BackgroundTasks, Depends, FastAPI, Form, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image
from pydantic import BaseModel

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.avatar import build_default_avatar_stages, run_avatar_pipeline, should_rebake
from pipeline.engine_bridge import build_morph_spec
from pipeline.facelock import apply_facelock
from pipeline.imaging import load_rgb
from pipeline.prompt import build_prompt
from pipeline.stages import generate_nano_banana
from server.avatar_jobs import AvatarJobStore
from server.inputs import to_engine_inputs
from server.ratelimit import SlidingWindowLimiter, rate_limit_dependency
import server.supa as supa
import server.storage as storage

log = logging.getLogger(__name__)

SERVER_DIR = pathlib.Path(__file__).resolve().parent
OUTPUTS = SERVER_DIR / "outputs"
OUTPUTS.mkdir(exist_ok=True)
# Private job data (meta.json with health inputs + the raw uploaded photo) lives
# OUTSIDE the static mount — only generated media under OUTPUTS is web-served.
JOBS_PRIVATE = SERVER_DIR / "jobs"
JOBS_PRIVATE.mkdir(exist_ok=True)

# Module-level factory so tests can monkeypatch it.
AVATAR_STAGES_FACTORY = build_default_avatar_stages

# ---------------------------------------------------------------------------
# Progress / tamagotchi constants
# ---------------------------------------------------------------------------
# Minimum days between two automatic re-bakes (cost control).
REBAKE_COOLDOWN_DAYS = 5
# Maximum lifetime re-bakes a user may spend.
REBAKE_CAP = 8

# Watchdog: a normal avatar generation is ~5-7 min. If a stage hangs (e.g. a fal
# call that never returns — seen when the fal balance is exhausted), the job must
# not sit at "Sculpting 5%" forever. Past this deadline we abandon the attempt and
# mark the job failed so the user gets a clear retry instead of an eternal spinner.
AVATAR_JOB_TIMEOUT_S = int(os.getenv("AVATAR_JOB_TIMEOUT_S", str(12 * 60)))

# Per-IP rate limit on the unauthenticated, paid image-generation endpoint
# (/transform calls fal.ai). Tunable via env without a redeploy of code.
TRANSFORM_RATE_MAX = int(os.getenv("TRANSFORM_RATE_MAX", "10"))
TRANSFORM_RATE_WINDOW_S = int(os.getenv("TRANSFORM_RATE_WINDOW_S", "3600"))
_transform_limiter = SlidingWindowLimiter(TRANSFORM_RATE_MAX, TRANSFORM_RATE_WINDOW_S)
transform_rate_limit = rate_limit_dependency(_transform_limiter, "image-generation")

_job_store = AvatarJobStore(OUTPUTS, JOBS_PRIVATE)

app = FastAPI(title="PhysiqAI", version="0.7.0")

# CORS allowlist. Native apps send no Origin header (CORS is browser-only), so
# locking this down does not affect the iOS/Android app — it restricts which
# *web* origins may call the API from a browser. Set ALLOWED_ORIGINS (comma-
# separated) in the deploy env to add/override production web origin(s); the
# *.vercel.app regex also lets Vercel preview deploys through; the defaults
# cover the production web app + local Expo Web / dev.
_DEFAULT_ALLOWED_ORIGINS = [
    "https://dist-nine-kappa-20.vercel.app",  # production web app
    "http://localhost:8081",
    "http://localhost:8085",
    "http://localhost:19006",
    "http://localhost:3000",
]
_origins_env = os.getenv("ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS = [o.strip() for o in _origins_env.split(",") if o.strip()] or _DEFAULT_ALLOWED_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=True,
)
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS)), name="outputs")

_ALLOWED_PHOTO_TYPES = {"image/jpeg", "image/png", "image/webp"}
_MAX_PHOTO_BYTES = 20 * 1024 * 1024


def _validate_photo(photo: UploadFile) -> None:
    if photo.content_type not in _ALLOWED_PHOTO_TYPES:
        raise HTTPException(status_code=415,
                            detail=f"unsupported image type: {photo.content_type}; "
                                   "use JPEG, PNG, or WebP")
    if photo.size is not None and photo.size > _MAX_PHOTO_BYTES:
        raise HTTPException(status_code=413, detail="photo larger than 20 MB")


def require_user(authorization: Optional[str] = Header(None)) -> dict:
    """FastAPI dependency: validate Bearer token, return {"id", "email"}.

    Raises 401 if the header is missing, malformed, or the token is rejected
    by Supabase.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing or invalid Authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="missing or invalid Authorization header")
    user = supa.verify_token(token)
    if user is None:
        raise HTTPException(status_code=401, detail="invalid or expired token")
    return user


@app.get("/health")
def health():
    return {"ok": True, "service": "physiqai", "version": app.version}


def _projection(spec) -> dict:
    return {
        "direction": spec.direction,
        "months": spec.months,
        "weight_before_lb": round(spec.weight_before_lb, 1),
        "weight_after_lb": round(spec.weight_after_lb, 1),
        "weight_delta_lb": round(spec.weight_delta_lb, 1),
        "bf_before": round(spec.bf_before, 1),
        "bf_after": round(spec.bf_after, 1),
        "bf_delta": round(spec.bf_delta, 1),
        "lean_delta_lb": round(spec.lean_delta_lb, 1),
        "confidence_score": round(spec.confidence_score, 2),
        "confidence_lo_lb": round(spec.confidence_lo_lb, 1),
        "confidence_hi_lb": round(spec.confidence_hi_lb, 1),
        "measurements_cm": {k: round(v, 1) for k, v in spec.measurements_cm.items()},
        "warnings": spec.warnings,
        "insights": spec.insights,
    }


@app.post("/transform", dependencies=[Depends(transform_rate_limit)])
def transform(
    request: Request,
    photo: UploadFile,
    age: str = Form(...),
    sex: str = Form(...),
    height_in: str = Form(...),
    weight_lb: str = Form(...),
    bf_pct: str = Form(...),
    goal: str = Form(...),
    weeks: str = Form(...),
    # core / back-compat
    experience: str = Form("intermediate"),
    # full onboarding (all optional; defaults keep older clients working)
    years_training: Optional[str] = Form(None),
    bf_method: Optional[str] = Form(None),
    sleep_hrs: Optional[str] = Form(None),
    stress: Optional[str] = Form(None),
    genetic_potential: Optional[str] = Form(None),
    lean_preference: Optional[str] = Form(None),
    daily_calories: Optional[str] = Form(None),
    protein_g: Optional[str] = Form(None),
    protein_level: Optional[str] = Form(None),
    tracking_method: Optional[str] = Form(None),
    volume: Optional[str] = Form(None),
    intensity: Optional[str] = Form(None),
    days_per_week: Optional[str] = Form(None),
    cardio_days: Optional[str] = Form(None),
    focus_muscle_groups: Optional[str] = Form(None),
):
    payload = dict(
        age=age, sex=sex, height_in=height_in, weight_lb=weight_lb, bf_pct=bf_pct,
        experience=experience, goal=goal, weeks=weeks,
        years_training=years_training, bf_method=bf_method, sleep_hrs=sleep_hrs,
        stress=stress, genetic_potential=genetic_potential, lean_preference=lean_preference,
        daily_calories=daily_calories, protein_g=protein_g, protein_level=protein_level,
        tracking_method=tracking_method, volume=volume, intensity=intensity,
        days_per_week=days_per_week, cardio_days=cardio_days,
        focus_muscle_groups=focus_muscle_groups,
    )
    try:
        profile, goal_spec, nutrition, training, n_weeks = to_engine_inputs(payload)
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=422, detail=f"invalid inputs: {e}")
    _validate_photo(photo)

    job = uuid.uuid4().hex[:12]
    job_dir = OUTPUTS / job
    job_dir.mkdir(parents=True, exist_ok=True)
    before_path = job_dir / "before.jpg"
    # Normalize EXIF orientation up front; the saved before.jpg (uprighted, no EXIF) is
    # what gets sent to generation + face-lock, so the whole pipeline stays upright.
    before_arr = load_rgb(photo.file)
    Image.fromarray(before_arr).save(before_path)

    spec = build_morph_spec(profile, goal_spec, nutrition, training, n_weeks)
    prompt = build_prompt(spec)

    t = time.time()
    try:
        after = generate_nano_banana(str(before_path), prompt, None)
    except Exception as e:  # surface fal/network errors as 502, not 500
        raise HTTPException(status_code=502, detail=f"generation failed: {e}")
    locked, locked_flag = apply_facelock(before_arr, after)
    Image.fromarray(locked).save(job_dir / "after.jpg")
    seconds = round(time.time() - t, 1)

    base = str(request.base_url).rstrip("/")
    return {
        "job": job,
        "before_url": f"{base}/outputs/{job}/before.jpg",
        "after_url": f"{base}/outputs/{job}/after.jpg",
        "projection": _projection(spec),
        "face_locked": locked_flag,
        "seconds": seconds,
        "prompt": prompt,
    }


# ---------------------------------------------------------------------------
# Avatar helpers
# ---------------------------------------------------------------------------

# FastAPI resolves Form parameters by parameter name, so the routes below must
# each declare the full 22-field signature; they share _build_avatar_payload()
# to keep the payload dict consistent.
def _build_avatar_payload(
    age, sex, height_in, weight_lb, bf_pct, goal, weeks, experience,
    years_training, bf_method, sleep_hrs, stress, genetic_potential,
    lean_preference, daily_calories, protein_g, protein_level,
    tracking_method, volume, intensity, days_per_week, cardio_days,
    focus_muscle_groups,
) -> dict:
    return dict(
        age=age, sex=sex, height_in=height_in, weight_lb=weight_lb, bf_pct=bf_pct,
        experience=experience, goal=goal, weeks=weeks,
        years_training=years_training, bf_method=bf_method, sleep_hrs=sleep_hrs,
        stress=stress, genetic_potential=genetic_potential,
        lean_preference=lean_preference, daily_calories=daily_calories,
        protein_g=protein_g, protein_level=protein_level,
        tracking_method=tracking_method, volume=volume, intensity=intensity,
        days_per_week=days_per_week, cardio_days=cardio_days,
        focus_muscle_groups=focus_muscle_groups,
    )


def _supa_update_safe(job: str, fields: dict) -> None:
    """Mirror a status update to Supabase; log and swallow errors so they
    never crash the background runner."""
    try:
        supa.update_avatar(job, fields)
    except Exception as exc:  # noqa: BLE001
        log.warning("Supabase mirror update failed for job %s: %s", job, exc)


def ensure_local_before_photo(job: str) -> str:
    """Return the local path to private_dir(job)/before.jpg.

    If the file is missing and Supabase Storage is enabled, attempts to
    download it from the private bucket before returning. Raises if the file
    is still absent after the download attempt.
    """
    path = _job_store.private_dir(job) / "before.jpg"
    if not path.exists() and storage.storage_enabled():
        log.info("before.jpg missing locally for job %s; downloading from Storage", job)
        storage.download_to(storage.PRIVATE_BUCKET, f"{job}/before.jpg", path)
    return str(path)


def _persist_media(job: str, out_dir: pathlib.Path, private_dir: pathlib.Path) -> dict:
    """Upload generated media to Supabase Storage and return public URL dict.

    Uploads:
      - every out_dir/frames_mobile/*.webp  -> MEDIA_BUCKET  "{job}/frames_mobile/{name}.webp"
      - out_dir/master.webm (if exists)     -> MEDIA_BUCKET  "{job}/master.webm"
      - out_dir/after.jpg (if exists)       -> MEDIA_BUCKET  "{job}/after.jpg"
      - private_dir/before.jpg (if exists)  -> PRIVATE_BUCKET "{job}/before.jpg"

    Returns a dict with frame_base_url, after_url, master_url.
    """
    frames_mobile_dir = out_dir / "frames_mobile"
    if frames_mobile_dir.exists():
        for webp in sorted(frames_mobile_dir.glob("*.webp")):
            storage.upload_file(
                storage.MEDIA_BUCKET,
                f"{job}/frames_mobile/{webp.name}",
                webp,
                "image/webp",
            )

    # Full-res frames (1280px PNG) for desktop/share viewers — the phone app uses
    # the smaller webp set, but the high-res spin is what makes the share land.
    frames_dir = out_dir / "frames"
    if frames_dir.exists():
        for png in sorted(frames_dir.glob("*.png")):
            storage.upload_file(
                storage.MEDIA_BUCKET,
                f"{job}/frames/{png.name}",
                png,
                "image/png",
            )

    master_webm = out_dir / "master.webm"
    if master_webm.exists():
        storage.upload_file(
            storage.MEDIA_BUCKET,
            f"{job}/master.webm",
            master_webm,
            "video/webm",
        )

    after_jpg = out_dir / "after.jpg"
    if after_jpg.exists():
        storage.upload_file(
            storage.MEDIA_BUCKET,
            f"{job}/after.jpg",
            after_jpg,
            "image/jpeg",
        )

    before_jpg = private_dir / "before.jpg"
    if before_jpg.exists():
        storage.upload_file(
            storage.PRIVATE_BUCKET,
            f"{job}/before.jpg",
            before_jpg,
            "image/jpeg",
        )

    # NOTE: only columns that exist on the avatars table may go here — this dict
    # is spread into the Supabase row update. The full-res frame base is NOT
    # stored (no column); it's derivable as frame_base_url with /frames_mobile
    # -> /frames (see _full_frame_base) for any desktop/share viewer.
    return {
        "frame_base_url": storage.public_url(storage.MEDIA_BUCKET, f"{job}/frames_mobile"),
        "after_url": storage.public_url(storage.MEDIA_BUCKET, f"{job}/after.jpg"),
        "master_url": storage.public_url(storage.MEDIA_BUCKET, f"{job}/master.webm"),
    }


def _full_frame_base(frame_base_url: str) -> str:
    """Full-res (1280px PNG) frame base, derived from the mobile webp base.

    Both sets are uploaded to Storage under the same job prefix; only the mobile
    base is persisted on the row, so derive the full-res one when a caller wants
    the higher-quality frames."""
    return frame_base_url.replace("/frames_mobile", "/frames")


def _run_avatar_job(job: str) -> None:
    """Sync background runner executed in a threadpool by BackgroundTasks.

    Everything is wrapped: an exception escaping here would be swallowed by
    BackgroundTasks and leave the job stuck in 'queued' forever.
    """
    meta = _job_store.get(job)
    if meta is None:
        return
    out_dir = _job_store.job_dir(job)
    try:
        photo_path = ensure_local_before_photo(job)
    except Exception as e:
        _job_store.update(job, status="failed", error=f"before photo unavailable: {e}")
        _supa_update_safe(job, {"status": "failed", "error": f"before photo unavailable: {e}"})
        return

    def _on_status(status: str, pct: int) -> None:
        # 'done' is written below in ONE atomic update together with
        # frame_count — writing it here first would open a window where
        # clients see status=done with frames=null.
        if status == "done":
            return
        _job_store.update(job, status=status, progress_pct=pct)
        _supa_update_safe(job, {"status": status, "progress_pct": pct})

    # Run the pipeline under a watchdog thread. A hung stage (e.g. a fal call that
    # never returns) is abandoned at the deadline so the user isn't stuck forever.
    # A CLEAN error is retried once (transient fal blips); a TIMEOUT is NOT retried
    # — a hang would just hang again, so we fail fast and let the user retry.
    result = None
    last_err: Optional[Exception] = None
    for attempt in (1, 2):
        holder: dict = {}

        def _work(_h=holder):
            try:
                profile, goal_spec, nutrition, training, n_weeks = to_engine_inputs(meta["inputs"])
                spec = build_morph_spec(profile, goal_spec, nutrition, training, n_weeks)
                stages = AVATAR_STAGES_FACTORY(out_dir)
                _h["result"] = run_avatar_pipeline(
                    photo_path=photo_path,
                    spec=spec,
                    out_dir=out_dir,
                    stages=stages,
                    on_status=_on_status,
                )
            except Exception as e:  # noqa: BLE001 — surfaced via holder below
                _h["error"] = e

        worker = threading.Thread(target=_work, name=f"avatar-{job}-try{attempt}", daemon=True)
        worker.start()
        worker.join(timeout=AVATAR_JOB_TIMEOUT_S)

        if worker.is_alive():
            log.error("Avatar job %s timed out after %ss (stage hung) — failing", job, AVATAR_JOB_TIMEOUT_S)
            _job_store.update(job, status="failed", error="generation timed out")
            _supa_update_safe(job, {"status": "failed",
                                    "error": "generation timed out — please try again"})
            return
        if "error" in holder:
            last_err = holder["error"]
            log.warning("Avatar job %s attempt %d failed: %s", job, attempt, last_err)
            continue  # retry once on a clean error
        result = holder["result"]
        break

    if result is None:
        _job_store.update(job, status="failed", error=f"pipeline error: {last_err}")
        _supa_update_safe(job, {"status": "failed", "error": f"pipeline error: {last_err}"})
        return

    if result.ok:
        storage_urls: dict = {}
        if storage.storage_enabled():
            try:
                storage_urls = _persist_media(
                    job,
                    out_dir,
                    _job_store.private_dir(job),
                )
            except Exception as exc:
                log.warning(
                    "Storage upload failed for job %s (falling back to local URLs): %s",
                    job, exc,
                )
        _job_store.update(job, status="done", progress_pct=100,
                          frame_count=result.frame_count, **storage_urls)
        _supa_update_safe(job, {
            "status": "done",
            "progress_pct": 100,
            "frame_count": result.frame_count,
            **storage_urls,
        })
    else:
        _job_store.update(job, status="failed", error=result.error or "unknown error")
        _supa_update_safe(job, {
            "status": "failed",
            "error": result.error or "unknown error",
        })


def _avatar_response(meta: dict, base: str) -> dict:
    """Build the GET /avatar/{job} response dict from stored meta + base URL.

    When the meta contains a truthy "frame_base_url" (set after a successful
    Supabase Storage upload), media URLs are served from Storage.  Otherwise
    falls back to local /outputs paths so dev / no-Supabase envs keep working.
    """
    job = meta["job"]
    out_dir = _job_store.job_dir(job)

    use_storage = bool(meta.get("frame_base_url"))

    if use_storage:
        after_url = meta.get("after_url") or None
        master_url = meta.get("master_url") or None
        frame_count = meta.get("frame_count")
        frames = None
        if meta.get("status") == "done" and frame_count:
            frames = {
                "count": frame_count,
                "base_url": meta["frame_base_url"],
                "ext": "webp",
            }
    else:
        after_url = None
        if (out_dir / "after.jpg").exists():
            after_url = f"{base}/outputs/avatars/{job}/after.jpg"

        frames = None
        frame_count = meta.get("frame_count")
        if meta.get("status") == "done" and frame_count:
            frames = {
                "count": frame_count,
                "base_url": f"{base}/outputs/avatars/{job}/frames_mobile",
                "ext": "webp",
            }

        master_url = None
        if (out_dir / "master.webm").exists():
            master_url = f"{base}/outputs/avatars/{job}/master.webm"

    return {
        "job": job,
        "status": meta["status"],
        "progress_pct": meta.get("progress_pct", 0),
        "error": meta.get("error"),
        "projection": meta.get("projection"),
        "after_url": after_url,
        "frames": frames,
        "master_url": master_url,
        "created_at": meta.get("created_at"),
    }


# ---------------------------------------------------------------------------
# POST /avatar
# ---------------------------------------------------------------------------

@app.post("/avatar", status_code=202)
def create_avatar(
    request: Request,
    background_tasks: BackgroundTasks,
    photo: UploadFile,
    age: str = Form(...),
    sex: str = Form(...),
    height_in: str = Form(...),
    weight_lb: str = Form(...),
    bf_pct: str = Form(...),
    goal: str = Form(...),
    weeks: str = Form(...),
    experience: str = Form("intermediate"),
    years_training: Optional[str] = Form(None),
    bf_method: Optional[str] = Form(None),
    sleep_hrs: Optional[str] = Form(None),
    stress: Optional[str] = Form(None),
    genetic_potential: Optional[str] = Form(None),
    lean_preference: Optional[str] = Form(None),
    daily_calories: Optional[str] = Form(None),
    protein_g: Optional[str] = Form(None),
    protein_level: Optional[str] = Form(None),
    tracking_method: Optional[str] = Form(None),
    volume: Optional[str] = Form(None),
    intensity: Optional[str] = Form(None),
    days_per_week: Optional[str] = Form(None),
    cardio_days: Optional[str] = Form(None),
    focus_muscle_groups: Optional[str] = Form(None),
    current_user: dict = Depends(require_user),
):
    payload = _build_avatar_payload(
        age=age, sex=sex, height_in=height_in, weight_lb=weight_lb, bf_pct=bf_pct,
        goal=goal, weeks=weeks, experience=experience,
        years_training=years_training, bf_method=bf_method, sleep_hrs=sleep_hrs,
        stress=stress, genetic_potential=genetic_potential, lean_preference=lean_preference,
        daily_calories=daily_calories, protein_g=protein_g, protein_level=protein_level,
        tracking_method=tracking_method, volume=volume, intensity=intensity,
        days_per_week=days_per_week, cardio_days=cardio_days,
        focus_muscle_groups=focus_muscle_groups,
    )
    try:
        profile, goal_spec, nutrition, training, n_weeks = to_engine_inputs(payload)
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=422, detail=f"invalid inputs: {e}")
    _validate_photo(photo)

    user_id = current_user["id"]

    # Enforce beta spend cap — must succeed before we start generating.
    try:
        count = supa.count_user_avatars(user_id)
        limit = supa.get_avatar_limit(user_id)
    except Exception as exc:
        log.error("Supabase unreachable during limit check: %s", exc)
        raise HTTPException(status_code=503, detail="avatar service temporarily unavailable")
    if count >= limit:
        raise HTTPException(status_code=403, detail="avatar limit reached for this account")

    spec = build_morph_spec(profile, goal_spec, nutrition, training, n_weeks)
    projection = _projection(spec)

    job = uuid.uuid4().hex[:12]

    # Insert into Supabase BEFORE creating the local job — if Supabase is down
    # we hard-fail (can't enforce the cap otherwise).
    try:
        supa.insert_avatar({
            "user_id": user_id,
            "job": job,
            "status": "queued",
            "progress_pct": 0,
            "inputs": payload,
            "projection": projection,
        })
    except Exception as exc:
        log.error("Supabase insert failed, aborting avatar creation: %s", exc)
        raise HTTPException(status_code=503, detail="avatar service temporarily unavailable")

    # Store user_id (not the old freeform "user" string) in local meta.
    _job_store.create(job, user=user_id, inputs=payload)

    # The raw uploaded photo is private — it lives next to meta.json, never
    # under the static mount.
    before_arr = load_rgb(photo.file)
    Image.fromarray(before_arr).save(_job_store.private_dir(job) / "before.jpg")
    _job_store.update(job, projection=projection)

    background_tasks.add_task(_run_avatar_job, job)

    base = str(request.base_url).rstrip("/")
    return {"job": job, "status_url": f"{base}/avatar/{job}"}


# ---------------------------------------------------------------------------
# GET /avatar/latest  (must be declared BEFORE /avatar/{job} to avoid routing clash)
# ---------------------------------------------------------------------------

@app.get("/avatar/latest")
def avatar_latest(request: Request, current_user: dict = Depends(require_user)):
    user_id = current_user["id"]
    base = str(request.base_url).rstrip("/")
    # The newest done row in Supabase is the durable source of truth.
    supa_row = supa.latest_done_for_user(user_id)
    if supa_row is None:
        raise HTTPException(status_code=404, detail="no completed avatar for this user")
    job = supa_row["job"]
    meta = _job_store.get(job)
    if meta is not None:
        return _avatar_response(meta, base)
    # Local files are gone (ephemeral disk wiped on redeploy) — build straight
    # from the Supabase row, which carries the Storage media URLs.
    if supa_row.get("frame_base_url"):
        return _avatar_response(supa_row, base)
    # Last resort: scan local disk (dev / no-Supabase).
    meta = _job_store.latest_done_for_user(user_id)
    if meta is None:
        raise HTTPException(status_code=404, detail="no completed avatar for this user")
    return _avatar_response(meta, base)


# ---------------------------------------------------------------------------
# GET /avatar/{job}
# ---------------------------------------------------------------------------

@app.get("/avatar/{job}")
def get_avatar(job: str, request: Request, current_user: dict = Depends(require_user)):
    base = str(request.base_url).rstrip("/")
    meta = _job_store.get(job)
    if meta is not None:
        # Ownership check: the job's stored user_id must match the caller.
        if meta.get("user") != current_user["id"]:
            raise HTTPException(status_code=403, detail="forbidden")
        return _avatar_response(meta, base)
    # Local disk is ephemeral (a redeploy wipes it). The Supabase row is the
    # durable source of truth and carries the Storage media URLs — serve from it.
    row = supa.get_avatar_by_job(job)
    if row is None:
        raise HTTPException(status_code=404, detail="job not found")
    if row.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="forbidden")
    return _avatar_response(row, base)


# ---------------------------------------------------------------------------
# POST /avatar/refresh
# ---------------------------------------------------------------------------

@app.post("/avatar/refresh")
def avatar_refresh(
    age: str = Form(...),
    sex: str = Form(...),
    height_in: str = Form(...),
    weight_lb: str = Form(...),
    bf_pct: str = Form(...),
    goal: str = Form(...),
    weeks: str = Form(...),
    experience: str = Form("intermediate"),
    years_training: Optional[str] = Form(None),
    bf_method: Optional[str] = Form(None),
    sleep_hrs: Optional[str] = Form(None),
    stress: Optional[str] = Form(None),
    genetic_potential: Optional[str] = Form(None),
    lean_preference: Optional[str] = Form(None),
    daily_calories: Optional[str] = Form(None),
    protein_g: Optional[str] = Form(None),
    protein_level: Optional[str] = Form(None),
    tracking_method: Optional[str] = Form(None),
    volume: Optional[str] = Form(None),
    intensity: Optional[str] = Form(None),
    days_per_week: Optional[str] = Form(None),
    cardio_days: Optional[str] = Form(None),
    focus_muscle_groups: Optional[str] = Form(None),
    job: str = Form(...),
    current_user: dict = Depends(require_user),
):
    meta = _job_store.get(job)
    if meta is None:
        raise HTTPException(status_code=404, detail="job not found")
    # Ownership check
    if meta.get("user") != current_user["id"]:
        raise HTTPException(status_code=403, detail="forbidden")

    payload = _build_avatar_payload(
        age=age, sex=sex, height_in=height_in, weight_lb=weight_lb, bf_pct=bf_pct,
        goal=goal, weeks=weeks, experience=experience,
        years_training=years_training, bf_method=bf_method, sleep_hrs=sleep_hrs,
        stress=stress, genetic_potential=genetic_potential, lean_preference=lean_preference,
        daily_calories=daily_calories, protein_g=protein_g, protein_level=protein_level,
        tracking_method=tracking_method, volume=volume, intensity=intensity,
        days_per_week=days_per_week, cardio_days=cardio_days,
        focus_muscle_groups=focus_muscle_groups,
    )
    try:
        profile, goal_spec, nutrition, training, n_weeks = to_engine_inputs(payload)
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=422, detail=f"invalid inputs: {e}")

    spec = build_morph_spec(profile, goal_spec, nutrition, training, n_weeks)
    current_projection = _projection(spec)
    baked_projection = meta.get("projection") or {}

    rebake, reasons = should_rebake(baked_projection, current_projection)
    return {
        "rebake_recommended": rebake,
        "reasons": reasons,
        "current_projection": current_projection,
        "baked_projection": baked_projection,
    }


# ---------------------------------------------------------------------------
# Progress / tamagotchi helpers
# ---------------------------------------------------------------------------

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _progress_state(baked: dict, current: dict, rebake_triggered: bool) -> str:
    """Heuristic label for how the user is tracking vs their baked avatar.

    Compares current projected bf_after vs the baked one (a cut means
    lower bf_after is better). Also handles weight-gain direction.
    """
    if rebake_triggered:
        return "evolving"
    baked_bf = float(baked.get("bf_after", 0))
    current_bf = float(current.get("bf_after", 0))
    direction = current.get("direction", baked.get("direction", ""))
    diff = current_bf - baked_bf  # negative = leaner than projected
    if abs(diff) <= 0.5:
        return "on_track"
    if direction == "gain":
        # for a gain, compare projected weight_after_lb
        baked_w = float(baked.get("weight_after_lb", 0))
        current_w = float(current.get("weight_after_lb", 0))
        return "ahead" if current_w > baked_w else "behind"
    # cut / recomp: leaner is ahead
    return "ahead" if diff < 0 else "behind"


class CheckInBody(BaseModel):
    weight_lb: Optional[float] = None
    bf_pct: Optional[float] = None
    workouts_done: int = 0
    note: Optional[str] = None


# ---------------------------------------------------------------------------
# POST /progress
# ---------------------------------------------------------------------------

@app.post("/progress")
def post_progress(
    body: CheckInBody,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_user),
):
    user_id = current_user["id"]

    # 1. Find the basis avatar (any status — we just need the inputs + projection).
    basis = supa.latest_avatar_for_user(user_id)
    if basis is None:
        raise HTTPException(status_code=409, detail="generate your avatar first")

    # 2. Recompute projection from current stats merged into the basis inputs.
    payload = dict(basis.get("inputs") or {})
    if body.weight_lb is not None:
        payload["weight_lb"] = str(body.weight_lb)
    if body.bf_pct is not None:
        payload["bf_pct"] = str(body.bf_pct)
    try:
        profile, goal_spec, nutrition, training, n_weeks = to_engine_inputs(payload)
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=422, detail=f"invalid inputs: {e}")
    spec = build_morph_spec(profile, goal_spec, nutrition, training, n_weeks)
    current = _projection(spec)

    # 3. Insert the check-in row.
    checkin_record: dict = {
        "user_id": user_id,
        "workouts_done": body.workouts_done,
        "projection": current,
    }
    if body.weight_lb is not None:
        checkin_record["weight_lb"] = body.weight_lb
    if body.bf_pct is not None:
        checkin_record["bf_pct"] = body.bf_pct
    if body.note is not None:
        checkin_record["note"] = body.note
    checkin_row = supa.insert_checkin(checkin_record)

    # 4. Update streak on the profile.
    prof = supa.get_profile(user_id) or {}
    now_iso = _now_utc().isoformat()
    last_str = prof.get("last_checkin_at")
    if last_str:
        try:
            last_dt = datetime.fromisoformat(last_str.replace("Z", "+00:00"))
            streak = (prof.get("streak_weeks") or 0) + 1 if (_now_utc() - last_dt) <= timedelta(days=10) else 1
        except (ValueError, TypeError):
            streak = 1
    else:
        streak = 1
    profile_update: dict = {
        "streak_weeks": streak,
        "last_checkin_at": now_iso,
    }
    if body.weight_lb is not None:
        profile_update["current_weight_lb"] = body.weight_lb
    if body.bf_pct is not None:
        profile_update["current_bf_pct"] = body.bf_pct
    supa.update_profile(user_id, profile_update)

    # 5. Evaluate re-bake threshold.
    baked = basis.get("projection") or {}
    rebake_recommended, reasons = should_rebake(baked, current)

    # 6. Re-bake gate (cost control).
    rebake_triggered = False
    rebake_job_id: Optional[str] = None

    if rebake_recommended:
        rebakes_used = prof.get("rebakes_used") or 0
        basis_created_at_str = basis.get("created_at") or ""
        cooldown_ok = False
        if basis_created_at_str:
            try:
                basis_dt = datetime.fromisoformat(basis_created_at_str.replace("Z", "+00:00"))
                cooldown_ok = (_now_utc() - basis_dt) > timedelta(days=REBAKE_COOLDOWN_DAYS)
            except (ValueError, TypeError):
                cooldown_ok = True  # can't parse — don't block the rebake
        else:
            cooldown_ok = True

        cap_ok = rebakes_used < REBAKE_CAP

        if cooldown_ok and cap_ok:
            # Ensure the basis before.jpg is available locally (may need to
            # pull it from Storage if the Railway disk was recycled).
            basis_job_id = basis["job"]
            src_photo = _job_store.private_dir(basis_job_id) / "before.jpg"
            if not src_photo.exists() and storage.storage_enabled():
                try:
                    storage.download_to(
                        storage.PRIVATE_BUCKET,
                        f"{basis_job_id}/before.jpg",
                        src_photo,
                    )
                except Exception as exc:
                    log.warning(
                        "Could not retrieve before.jpg from Storage for basis job %s: %s",
                        basis_job_id, exc,
                    )
            if src_photo.exists():
                new_job = uuid.uuid4().hex[:12]
                new_inputs = dict(payload)
                _job_store.create(new_job, user=user_id, inputs=new_inputs)
                dst_photo = _job_store.private_dir(new_job) / "before.jpg"
                shutil.copy2(src_photo, dst_photo)
                _job_store.update(new_job, projection=current)
                supa.insert_avatar({
                    "user_id": user_id,
                    "job": new_job,
                    "status": "queued",
                    "progress_pct": 0,
                    "inputs": new_inputs,
                    "projection": current,
                })
                background_tasks.add_task(_run_avatar_job, new_job)
                supa.update_profile(user_id, {"rebakes_used": rebakes_used + 1})
                # Update the checkin row to record the rebake.
                checkin_id = checkin_row.get("id")
                if checkin_id:
                    try:
                        supa.update_checkin(checkin_id, {
                            "rebake_triggered": True,
                            "rebake_job": new_job,
                        })
                    except Exception as exc:
                        log.warning("Failed to update checkin with rebake info: %s", exc)
                rebake_triggered = True
                rebake_job_id = new_job
                reasons_after_rebake = reasons
            else:
                log.warning(
                    "Re-bake skipped for job %s: before.jpg missing at %s",
                    basis_job_id, src_photo,
                )
                reasons = reasons + ["source photo missing; re-upload to rebake"]

    state = _progress_state(baked, current, rebake_triggered)

    return {
        "projection": current,
        "baked_projection": baked,
        "rebake_recommended": rebake_recommended,
        "reasons": reasons,
        "rebake_triggered": rebake_triggered,
        "rebake_job": rebake_job_id,
        "streak_weeks": streak,
        "state": state,
    }


# ---------------------------------------------------------------------------
# GET /progress
# ---------------------------------------------------------------------------

@app.get("/progress")
def get_progress(current_user: dict = Depends(require_user)):
    user_id = current_user["id"]
    prof = supa.get_profile(user_id) or {}
    checkins = supa.list_checkins(user_id)

    # Latest avatar — any status.
    latest_supa = supa.latest_avatar_for_user(user_id)
    latest_avatar = None
    if latest_supa:
        meta = _job_store.get(latest_supa["job"])
        status = (meta or {}).get("status") or latest_supa.get("status")
        frames = None
        if status == "done":
            frame_count = (meta or {}).get("frame_count") or latest_supa.get("frame_count")
            if frame_count:
                frames = {"count": frame_count}
        latest_avatar = {
            "job": latest_supa["job"],
            "status": status,
            "frames": frames,
        }

    return {
        "streak_weeks": prof.get("streak_weeks") or 0,
        "last_checkin_at": prof.get("last_checkin_at"),
        "current_weight_lb": prof.get("current_weight_lb"),
        "current_bf_pct": prof.get("current_bf_pct"),
        "rebakes_used": prof.get("rebakes_used") or 0,
        "checkins": checkins,
        "latest_avatar": latest_avatar,
    }


def _delete_user_media(user_id: str) -> None:
    """Best-effort removal of a user's avatar media from Supabase Storage.

    Storage is keyed by avatar `job`, so we delete each job's folder in both
    buckets. Failures here must not block identity/data deletion — they only
    leave orphaned media with no PII link, which we log and move on from.
    """
    if not storage.storage_enabled():
        return
    for job in supa.list_user_avatar_jobs(user_id):
        try:
            media_keys = storage.list_objects(storage.MEDIA_BUCKET, f"{job}/frames_mobile")
            media_keys += [f"{job}/after.jpg", f"{job}/master.webm"]
            storage.remove_objects(storage.MEDIA_BUCKET, media_keys)
            storage.remove_objects(storage.PRIVATE_BUCKET, [f"{job}/before.jpg"])
        except Exception as exc:  # noqa: BLE001 — best-effort cleanup
            log.warning("Storage cleanup failed for job %s: %s", job, exc)


@app.delete("/account")
def delete_account(current_user: dict = Depends(require_user)):
    """Delete the authenticated user's account and all their data.

    Required for App Store §5.1.1 (in-app account deletion). Order: media →
    data rows → auth user. Storage is best-effort; the data rows and the auth
    user are the compliance-critical parts.
    """
    user_id = current_user["id"]
    _delete_user_media(user_id)
    supa.delete_user_data_rows(user_id)
    supa.delete_auth_user(user_id)
    return {"success": True}
