"""Avatar 3D pipeline: still -> orbit -> matte -> extract frames.

Stages are injected via AvatarStages so the control flow is testable without any
fal/network/ffmpeg calls (same pattern as pipeline.run / pipeline.stages).

Public surface for Agent C (server routes):
  AvatarStages, AvatarResult, run_avatar_pipeline,
  build_default_avatar_stages, should_rebake
"""
from __future__ import annotations

import pathlib
import shutil
import subprocess
import tempfile
import urllib.request
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

import numpy as np
from PIL import Image


# ---------------------------------------------------------------------------
# Turntable prompt (generalised from spike/orbit.py — "the person" not "the
# muscular man" so it works for any subject and sex)
# ---------------------------------------------------------------------------
TURNTABLE_PROMPT = (
    "Smooth cinematic turntable. The camera slowly orbits a full circle around the "
    "person, revealing their physique from the front, then the side, then the back, "
    "and continuing around to the front again. They stand completely still in a relaxed "
    "neutral standing pose with arms at their sides. Their face, hair, skin, body shape "
    "and the background stay perfectly consistent the entire time. "
    "Photorealistic, steady continuous rotation, no warping, no morphing."
)


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class AvatarStages:
    still: Callable     # (photo_path: str, spec: MorphSpec) -> np.ndarray  RGB
    orbit: Callable     # (after_jpg_path: str) -> str  path to orbit.mp4
    matte: Callable     # (orbit_mp4_path: str) -> str  path to master.webm
    extract: Callable   # (webm_path: str, n: int) -> int  frame count


@dataclass
class AvatarResult:
    ok: bool
    frame_count: int
    error: Optional[str]
    after_path: Optional[str]
    orbit_path: Optional[str]
    master_path: Optional[str]


# ---------------------------------------------------------------------------
# Pure helper: compute union alpha bounding box across a list of RGBA arrays.
# Factored out so tests can drive it with tiny synthetic arrays.
# ---------------------------------------------------------------------------

def extract_crop_box(
    frames: List[np.ndarray],
    pad_x_frac: float = 0.06,
    pad_y_frac: float = 0.04,
) -> Tuple[int, int, int, int]:
    """Return (x0, y0, x1, y1) crop box that tightly wraps all non-transparent
    pixels across every frame, with a small pad to avoid edge clipping.

    Alpha threshold: >12 (same as spike/matte.py — weeds out near-invisible fringe).
    If every frame is fully transparent, returns (0, 0, W, H) to avoid a crash.
    """
    if not frames:
        raise ValueError("extract_crop_box requires at least one frame")
    H, W = frames[0].shape[:2]
    ux0 = W; uy0 = H; ux1 = 0; uy1 = 0
    found_any = False
    for arr in frames:
        alpha = arr[:, :, 3]
        ys, xs = np.where(alpha > 12)
        if len(xs):
            found_any = True
            ux0 = min(ux0, int(xs.min()))
            ux1 = max(ux1, int(xs.max()))
            uy0 = min(uy0, int(ys.min()))
            uy1 = max(uy1, int(ys.max()))

    if not found_any:
        return 0, 0, W, H

    # np.where maxima are inclusive pixel indices; PIL crop's x1/y1 are
    # exclusive, so +1 or the outermost opaque row/column gets clipped.
    ux1 += 1
    uy1 += 1

    bw = ux1 - ux0
    bh = uy1 - uy0
    padx = int(bw * pad_x_frac)
    pady = int(bh * pad_y_frac)
    ux0 = max(0, ux0 - padx)
    uy0 = max(0, uy0 - pady)
    ux1 = min(W, ux1 + padx)
    uy1 = min(H, uy1 + pady)
    return ux0, uy0, ux1, uy1


def write_frame_pair(
    img: Image.Image,
    crop_box: Tuple[int, int, int, int],
    index: int,
    frames_dir: pathlib.Path,
    frames_mobile_dir: pathlib.Path,
) -> None:
    """Crop, resize to 1280 and 800, write PNG + WebP for one frame.

    Factored out so tests can call it with synthetic PIL Images without needing
    ffmpeg on the machine.
    """
    x0, y0, x1, y1 = crop_box
    c = img.crop((x0, y0, x1, y1))
    bh = y1 - y0

    # Full-res: height 1280
    target_h = 1280
    w_full = max(1, round(c.width * target_h / c.height))
    full = c.resize((w_full, target_h), Image.LANCZOS)
    full.save(frames_dir / f"f{index:03d}.png")

    # Mobile: height 800, WebP quality 80
    target_h_mob = 800
    w_mob = max(1, round(c.width * target_h_mob / c.height))
    mob = c.resize((w_mob, target_h_mob), Image.LANCZOS)
    mob.save(frames_mobile_dir / f"f{index:03d}.webp", format="WEBP", quality=80)


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def run_avatar_pipeline(
    photo_path: str,
    spec,
    out_dir: pathlib.Path,
    stages: AvatarStages,
    on_status: Optional[Callable[[str, int], None]] = None,
    n_frames: int = 96,
) -> AvatarResult:
    """Run all four stages in order, saving artefacts under out_dir.

    Emits on_status callbacks:
      ("after_still", 5) -> ("orbiting", 25) -> ("matting", 60)
      -> ("extracting", 80) -> ("done", 100)
    On any stage exception: emits ("failed", current_pct) and returns
    AvatarResult(ok=False, error=...).
    """
    def _notify(status: str, pct: int) -> None:
        if on_status is not None:
            on_status(status, pct)

    after_path: Optional[str] = None
    orbit_path: Optional[str] = None
    master_path: Optional[str] = None
    current_pct = 0

    # --- stage 1: still (face-locked after image) ---
    try:
        after_arr = stages.still(photo_path, spec)
        after_jpg = out_dir / "after.jpg"
        Image.fromarray(after_arr).save(after_jpg)
        after_path = str(after_jpg)
        current_pct = 5
        _notify("after_still", current_pct)
    except Exception as exc:
        _notify("failed", current_pct)
        return AvatarResult(ok=False, frame_count=0, error=str(exc),
                            after_path=None, orbit_path=None, master_path=None)

    # --- stage 2: orbit ---
    try:
        orbit_path = stages.orbit(after_path)
        current_pct = 25
        _notify("orbiting", current_pct)
    except Exception as exc:
        _notify("failed", current_pct)
        return AvatarResult(ok=False, frame_count=0, error=str(exc),
                            after_path=after_path, orbit_path=None, master_path=None)

    # --- stage 3: matte ---
    try:
        master_path = stages.matte(orbit_path)
        current_pct = 60
        _notify("matting", current_pct)
    except Exception as exc:
        _notify("failed", current_pct)
        return AvatarResult(ok=False, frame_count=0, error=str(exc),
                            after_path=after_path, orbit_path=orbit_path, master_path=None)

    # --- stage 4: extract frames ---
    try:
        count = stages.extract(master_path, n_frames)
        current_pct = 80
        _notify("extracting", current_pct)
    except Exception as exc:
        _notify("failed", current_pct)
        return AvatarResult(ok=False, frame_count=0, error=str(exc),
                            after_path=after_path, orbit_path=orbit_path, master_path=master_path)

    _notify("done", 100)
    return AvatarResult(
        ok=True, frame_count=count, error=None,
        after_path=after_path, orbit_path=orbit_path, master_path=master_path,
    )


# ---------------------------------------------------------------------------
# Rebake logic
# ---------------------------------------------------------------------------

def should_rebake(
    baked_projection: dict,
    current_projection: dict,
) -> Tuple[bool, List[str]]:
    """Compare a new engine projection against the one baked into the avatar.

    Returns (True, [reasons]) if any threshold is exceeded:
      - |weight_after_lb diff| >= 2.0 lb
      - |bf_after diff| >= 1.0 %
      - direction changed

    All three are evaluated independently so multiple reasons can accumulate.
    """
    reasons: List[str] = []

    baked_w = float(baked_projection.get("weight_after_lb", 0))
    current_w = float(current_projection.get("weight_after_lb", 0))
    diff_w = abs(current_w - baked_w)
    if diff_w >= 2.0:
        reasons.append(f"projected weight moved {diff_w:.1f} lb")

    baked_bf = float(baked_projection.get("bf_after", 0))
    current_bf = float(current_projection.get("bf_after", 0))
    diff_bf = abs(current_bf - baked_bf)
    if diff_bf >= 1.0:
        reasons.append(f"projected body fat moved {diff_bf:.1f}%")

    baked_dir = baked_projection.get("direction", "")
    current_dir = current_projection.get("direction", "")
    if baked_dir and current_dir and baked_dir != current_dir:
        reasons.append(f"transformation direction changed from {baked_dir!r} to {current_dir!r}")

    return bool(reasons), reasons


# ---------------------------------------------------------------------------
# Real fal-backed stage implementations
# ---------------------------------------------------------------------------

def _orbit_stage(after_jpg_path: str, out_dir: pathlib.Path) -> str:
    import fal_client
    from .stages import _ensure_fal_key
    _ensure_fal_key()
    url = fal_client.upload_file(after_jpg_path)
    res = fal_client.subscribe(
        "bytedance/seedance-2.0/image-to-video",
        arguments={
            "prompt": TURNTABLE_PROMPT,
            "image_url": url,
            "resolution": "1080p",
            "duration": "8",
            "aspect_ratio": "9:16",
            "generate_audio": False,
            "seed": 777,
        },
        with_logs=False,
    )
    video_url = (res.get("video") or {}).get("url")
    if not video_url:
        raise RuntimeError(f"seedance returned no video: {res}")
    dest = out_dir / "orbit.mp4"
    urllib.request.urlretrieve(video_url, dest)
    return str(dest)


def _matte_stage(orbit_mp4_path: str, out_dir: pathlib.Path) -> str:
    import fal_client
    from .stages import _ensure_fal_key
    _ensure_fal_key()
    url = fal_client.upload_file(orbit_mp4_path)
    res = fal_client.subscribe(
        "bria/video/background-removal",
        arguments={
            "video_url": url,
            "background_color": "Transparent",
            "output_container_and_codec": "webm_vp9",
            "preserve_audio": False,
        },
        with_logs=False,
    )
    video_url = (res.get("video") or {}).get("url")
    if not video_url:
        raise RuntimeError(f"bria/video/background-removal returned no video: {res}")
    dest = out_dir / "master.webm"
    urllib.request.urlretrieve(video_url, dest)
    return str(dest)


def _extract_stage(webm_path: str, n: int, out_dir: pathlib.Path) -> int:
    import imageio_ffmpeg

    ff = imageio_ffmpeg.get_ffmpeg_exe()
    tmp = pathlib.Path(tempfile.mkdtemp())
    try:
        # CRITICAL: -c:v libvpx-vp9 MUST come BEFORE -i or the alpha plane is
        # silently dropped by the default decoder (hard-won spike lesson).
        subprocess.run(
            [ff, "-y", "-loglevel", "error",
             "-c:v", "libvpx-vp9",
             "-i", webm_path,
             "-pix_fmt", "rgba",
             str(tmp / "raw_%04d.png")],
            check=True,
        )
        raw = sorted(tmp.glob("raw_*.png"))
        if not raw:
            raise RuntimeError("ffmpeg produced no frames from webm")

        step = max(1, round(len(raw) / n))
        picks = raw[::step][:n]

        # Load all picked frames as RGBA numpy arrays for bbox computation
        frames_np: List[np.ndarray] = []
        frames_pil: List[Image.Image] = []
        for p in picks:
            im = Image.open(p).convert("RGBA")
            frames_pil.append(im)
            frames_np.append(np.asarray(im))

        crop_box = extract_crop_box(frames_np)

        frames_dir = out_dir / "frames"
        frames_mobile_dir = out_dir / "frames_mobile"
        frames_dir.mkdir(parents=True, exist_ok=True)
        frames_mobile_dir.mkdir(parents=True, exist_ok=True)

        for i, im in enumerate(frames_pil):
            write_frame_pair(im, crop_box, i, frames_dir, frames_mobile_dir)

        return len(frames_pil)

    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def build_default_avatar_stages(out_dir: pathlib.Path) -> AvatarStages:
    """Return real fal-backed stages, each closed over out_dir."""
    from .run import run_transformation
    from .stages import build_default_stages

    def still_stage(photo_path: str, spec) -> np.ndarray:
        result = run_transformation(photo_path, spec, build_default_stages())
        return result.image

    def orbit_stage(after_jpg_path: str) -> str:
        return _orbit_stage(after_jpg_path, out_dir)

    def matte_stage(orbit_mp4_path: str) -> str:
        return _matte_stage(orbit_mp4_path, out_dir)

    def extract_stage(webm_path: str, n: int) -> int:
        return _extract_stage(webm_path, n, out_dir)

    return AvatarStages(
        still=still_stage,
        orbit=orbit_stage,
        matte=matte_stage,
        extract=extract_stage,
    )
