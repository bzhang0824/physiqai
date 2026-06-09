"""PhysiqAI backend (thin slice).

Wraps the proven pipeline so the mobile app can run the full loop:
  photo + stats  ->  engine projection + face-locked before/after image.

Reuses the smoke-tested path (generate_nano_banana + apply_facelock); the facenet
auto-gate / full orchestrator is deferred (needs torch). FAL_KEY is read server-side
only (os.getenv) and never leaves this process.

Run:  bash server/run.sh   (uvicorn on 0.0.0.0:8000)
"""
from __future__ import annotations

import pathlib
import sys
import time
import uuid

import numpy as np
from fastapi import FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.engine_bridge import build_morph_spec
from pipeline.facelock import apply_facelock
from pipeline.prompt import build_prompt
from pipeline.stages import generate_nano_banana
from server.inputs import to_engine_inputs

OUTPUTS = pathlib.Path(__file__).resolve().parent / "outputs"
OUTPUTS.mkdir(exist_ok=True)

app = FastAPI(title="PhysiqAI", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                   allow_headers=["*"])
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS)), name="outputs")


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


@app.post("/transform")
def transform(
    request: Request,
    photo: UploadFile,
    age: str = Form(...),
    sex: str = Form(...),
    height_in: str = Form(...),
    weight_lb: str = Form(...),
    bf_pct: str = Form(...),
    experience: str = Form("intermediate"),
    goal: str = Form(...),
    weeks: str = Form(...),
):
    payload = dict(age=age, sex=sex, height_in=height_in, weight_lb=weight_lb,
                   bf_pct=bf_pct, experience=experience, goal=goal, weeks=weeks)
    try:
        profile, goal_spec, nutrition, training, n_weeks = to_engine_inputs(payload)
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=422, detail=f"invalid inputs: {e}")

    job = uuid.uuid4().hex[:12]
    job_dir = OUTPUTS / job
    job_dir.mkdir(parents=True, exist_ok=True)
    before_path = job_dir / "before.jpg"
    Image.open(photo.file).convert("RGB").save(before_path)

    spec = build_morph_spec(profile, goal_spec, nutrition, training, n_weeks)
    prompt = build_prompt(spec)

    t = time.time()
    try:
        after = generate_nano_banana(str(before_path), prompt, None)
    except Exception as e:  # surface fal/network errors as 502, not 500
        raise HTTPException(status_code=502, detail=f"generation failed: {e}")
    locked, locked_flag = apply_facelock(np.array(Image.open(before_path)), after)
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
