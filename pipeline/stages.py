"""Real, fal/OpenCV-backed implementations of the pipeline Stages (the I/O edges).

Pure logic lives in engine_bridge / prompt / identity / facelock and is unit-tested.
This module is the glue to external models; it's verified by the live smoke test.
"""
from __future__ import annotations

import io
import os
import pathlib
import urllib.request

import numpy as np
from PIL import Image

from .facelock import apply_facelock
from .imaging import load_rgb
from .run import Stages

NANO_BANANA = "fal-ai/nano-banana-pro/edit"
SEEDEDIT = "fal-ai/bytedance/seededit/v3/edit-image"  # cheaper identity-preserving fallback


def _ensure_fal_key() -> None:
    if os.getenv("FAL_KEY"):
        return
    env = pathlib.Path(__file__).resolve().parents[1] / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("FAL_KEY="):
                os.environ["FAL_KEY"] = line.split("=", 1)[1].strip().strip('"').strip("'")


def _load_rgb(path: str) -> np.ndarray:
    return load_rgb(path)  # applies EXIF orientation


def _download_rgb(url: str) -> np.ndarray:
    with urllib.request.urlopen(url) as r:
        return np.array(Image.open(io.BytesIO(r.read())).convert("RGB"))


def body_mask(photo: str):
    """Passthrough for Arch A.

    Nano Banana Pro is a prompt-based edit (no mask input) and already preserves
    background/pose; face-lock protects identity. A true Florence2+SAM2 body mask
    feeding a depth-ControlNet inpaint is the Arch B hardening step, not wired here.
    """
    return None


def _generate(photo: str, prompt: str, mask, endpoint: str) -> np.ndarray:
    import fal_client

    _ensure_fal_key()
    url = fal_client.upload_file(photo)
    res = fal_client.subscribe(endpoint, arguments={"image_urls": [url], "prompt": prompt},
                               with_logs=False)
    out_url = (res.get("images") or [{}])[0].get("url")
    if not out_url:
        raise RuntimeError(f"{endpoint} returned no image: {res}")
    return _download_rgb(out_url)


def generate_nano_banana(photo: str, prompt: str, mask) -> np.ndarray:
    return _generate(photo, prompt, mask, NANO_BANANA)


def generate_seededit(photo: str, prompt: str, mask) -> np.ndarray:
    return _generate(photo, prompt, mask, SEEDEDIT)


def facelock_stage(photo: str, generated: np.ndarray) -> np.ndarray:
    original = _load_rgb(photo)
    locked, _ = apply_facelock(original, generated)
    return locked


def identity_score(photo: str, candidate: np.ndarray) -> float:
    """Facenet cosine identity score. Requires facenet-pytorch (optional dep)."""
    from .identity_score import face_cosine

    original = _load_rgb(photo)
    return face_cosine(original, candidate)


def build_default_stages() -> Stages:
    return Stages(
        mask=body_mask,
        generate=generate_nano_banana,
        facelock=facelock_stage,
        score=identity_score,
        generate_fallback=generate_seededit,
    )
