# 3D Avatar — Handoff Notes (start here for the hyper-realistic 3D avatar work)

*For the separate session exploring the hyper-realistic, morphable 3D avatar (Arch B geometry + Arch C
"dynamic mirror"). Consolidates what we already proved/researched so you don't restart from zero.*

## The goal
A hyper-realistic 3D avatar of the user whose **physique morphs realistically based on inputs**, driven by
the **validated physiology engine** (`models/governor/`), keeping the user's **real face/identity**.

## What we ALREADY proved (don't re-litigate)
- **Photo → real 3D body works:** `fal-ai/sam-3/3d-body` ($0.02, ~12s) returns a rigged GLB mesh **+ shape
  parameters** (45 `shape_params`, 204 `mhr_model_params`) from a single casual photo. Validated on real
  photos incl. Brian's (outputs in `spike/output/sam3d/` and `spike/output/bz_sam3d/`).
- **Identity is solvable:** face-lock (keep the user's real face pixels; never let AI repaint them) —
  proven in `spike/output/morph/_facelock_3panel.png`. Production = SAM2 head segmentation + face-match retry.
- **The engine to drive the morph is DONE + validated** (7/7 literature, NHANES, Reddit). The avatar's shape
  changes MUST be driven by `models/governor/predictor.predict()` outputs (Δlean, Δfat, measurement deltas)
  — that's what keeps it honest.

## The recommended 3D stack (from the 16-agent SOTA survey)
| Layer | Tool | Notes |
|---|---|---|
| Photo → 3D body + shape params | **Meta SAM 3D Body** (fal.ai) | proven; no academic gate; $0.02 |
| Parametric morph (the slider) | **Anny** (Naver, Apache-2.0, free) | human-readable age/height/weight/**muscle** sliders → map engine deltas to these |
| Photoreal / face identity | **LHM** (Gaussian splatting) or mesh-texture + face-lock | LHM preserves face; needs self-host GPU |
| Dynamic video (the "mirror") | **Kling O3 Pro** (fal.ai) · **Higgsfield Soul ID** (MCP) | identity-locked image→video; Higgsfield has an MCP |
| Render → image (hybrid / Arch B) | mesh → depth/silhouette → **Flux depth-ControlNet** + inpaint | makes the photoreal result obey the 3D shape |

## The hard part (the real R&D)
**The bridge: SAM 3D Body's shape params → Anny's morphable params.** This is the novel work (~3–5 weeks):
fit Anny's body so it matches the user's reconstructed mesh, then apply the engine's numeric deltas
(+X kg lean to chest/shoulders, −Y% fat at waist) as Anny slider changes, re-render. A deterministic
least-squares mesh fit likely suffices (no heavy ML training).

## Other practical flags
- **macOS 3D tooling:** headless mesh rendering (depth maps) may need Blender CLI or pyrender/EGL setup —
  budget a little time for the render pipeline.
- **Two products from this:** (B) render the morphed mesh as a *control signal* for a photoreal image
  (fixes the magnitude problem we found), and (C) show the morphable mesh *itself* (rotatable + animatable).
- **Existing real SMPL assets** are in `models/smpl/` (full male/female/neutral) and `models/smpl_pipeline.py`
  (real mesh export) if you prefer SMPL over Anny — but Anny's commercial license + readable sliders are cleaner.

## Pointers
- `PROJECT_STATE.md` — overall state · `VISION.md` — Arch C "dynamic mirror" + wow features
- `docs/ENGINE_SPEC_DRAFT.md` — the governor that drives the morph · `models/governor/` — the engine code
- The full tool survey lived in the research workflow (Architecture B & C sections) — key picks captured above.
