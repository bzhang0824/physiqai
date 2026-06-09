# PhysiqAI — Photoreal Rotatable Avatar Spike (2026-06-01)

**Question:** Can we let a user **rotate a photoreal 3D avatar of their future physique**
and view it from any angle — *without* the GPU/CUDA/multi-view-capture burden of the
Gaussian-Splatting avatar repos (3DGS-Avatar, SplattingAvatar, GaussianAvatar)?

**Answer: YES — decisively, and far more cheaply than expected (~$0.46 total spend).**
Verified eyes-on, on a real photo (Brian's own `bz02` Arch-A "after" still).

The Gaussian-Splatting repos are the **wrong tool** (multi-view video + per-user GPU
training, and splats can't be morphed by the physiology engine). The 2026-06 model
re-survey surfaced a cleaner path that **didn't exist** when the original plan was written:
**single-image → textured 3D**.

---

## What was tested

Input for both: an existing engine-governed Arch-A "after" image
(`output/bz_trackA/bz02_IMG_7520_after.jpg`) — i.e. the physiology engine already
governed the body; these tests only add the *rotation*.

### Path A — single image → textured 3D mesh  ✅ STRONG PASS
- **Tool:** `fal-ai/hunyuan-3d/v3.1/pro/image-to-3d` (`generate_type: "Normal"`), ~$0.375, **129 s**.
- **Output:** a real **28 MB textured GLB** (282k verts, 500k faces) — a genuine 3D object.
- **Rendered turntable** (8 azimuths, `model-viewer` + headless Chromium):
  `output/spin/turntable_sheet.png`, `output/spin/turntable.gif`.
- **Result:** a coherent, fully rotatable textured human across all 360°. **No holes, no
  melting, zero flicker.** The muscular physique is faithfully preserved from every angle;
  the **back was plausibly reconstructed** (lats, spine, waistband) from a front-only photo;
  it sensibly re-posed the "hands-behind-head" input into a neutral stance.
- **The key win:** because it's **one mesh**, multi-view consistency is **free** — the exact
  problem (frame-to-frame identity/skin drift) that would have plagued the old
  "mesh → depth → paint each angle" plan simply does not exist here.

### Path B — multi-angle 2D generation  ✅ PASS (more photoreal per-frame)
- **Tool:** `fal-ai/flux-2-lora-gallery/multiple-angles`, ~$0.02/img, 9–17 s each; azimuth 0/90/180/270.
- **Output:** `output/spin/bz02_IMG_7520_after_angles_sheet.png`.
- **Result:** each angle looks like a **real photo** of the same person in the **same locker
  room** from a new viewpoint — more photographic than the mesh, and it **preserves the
  background**. Identity/build/skin-tone reasonably consistent across the 4 angles.
- **Trade-off:** these are **discrete, independently-generated** angles, not a free-rotate
  object. Making it "rotatable" means generating many angles (e.g. every 15° = 24 frames)
  and risks subtle frame-to-frame jitter at fine steps (not observable at 4 angles, unproven at 24).

---

## Honest weak points (both paths)

1. **Face / identity is the weak link.** Identity preservation is PhysiqAI's #1 requirement,
   and the face is exactly where image-to-3D is softest (small, generic, not a sharp likeness).
   This is the single biggest open risk for the 3D feature.
2. **Mesh skin reads as "high-end game character," not indistinguishable-from-photo.** Path B is
   more photoreal per-frame; Path A is more *controllable/rotatable*.
3. **The back/sides are invented** (front-only input). Acceptable for a body projection, not "true."
4. Hair is blobby in the mesh.

---

## Recommended architecture (the synthesis)

The two paths are **complementary**, and the strongest product path combines them:

1. **Engine governs the still** — Arch A (already validated) produces the physiologically-honest
   photoreal "future self" front image. *Magnitude stays governed upstream; the moat is intact.*
2. **FLUX multi-angle synthesizes clean side + back + a good face view** (photoreal, identity-locked).
3. **Feed those as multi-view input to Hunyuan3D Pro** (it accepts back/left/right/45° views) →
   a textured GLB with a **much better back and face** → a **true free-rotate 3D object** in a
   `model-viewer` / three.js viewer.
   - *Fallback if true free-rotate isn't needed for v1:* just present the FLUX multi-angle frames
     as a scrubbable turntable (simplest, most photoreal, no 3D pipeline).

This is **mostly an integration problem**, not research — no CUDA, no GPU servers, no SMPL
academic license, ~$0.4–0.5 per avatar, ~2–3 min. Renders in any browser/mobile via WebGL.

**Identity is the one real R&D risk to burn down next** (multi-view input + a face-fidelity /
face-restore pass), before committing to build.

---

## Go / No-Go

| Path | Verdict |
|---|---|
| Gaussian-Splatting avatar repos | **NO** — wrong tool, GPU/capture burden, not engine-morphable |
| Path A: image-to-3D textured mesh (Hunyuan3D Pro) | **GO** — true rotatable, consistency free; weak face |
| Path B: FLUX multi-angle 2D | **GO** — most photoreal; discrete angles, jitter unproven at fine steps |
| **Recommended: A+B hybrid (engine → FLUX multi-view → Hunyuan3D)** | **GO**, pending an identity-fidelity validation |

**This remains feasibility, not a build.** Next cheap validation before any app work:
the A+B hybrid on 3–5 clean full-body photos, scored specifically on **face identity** across angles.

---

## Artifacts (`spike/output/spin/`)
- `bz02_IMG_7520_after.glb` — the textured 3D mesh
- `turntable_sheet.png`, `turntable.gif` — Path A 360° render
- `bz02_thumbnail.png` — fal's own preview render of the mesh
- `bz02_IMG_7520_after_angles_sheet.png` — Path B multi-angle photoreal views
- `bz02_IMG_7520_after_mesh_raw.json` — raw Hunyuan3D response

Repro: `spike/spin.py` (fal calls), `spike/render_turntable.js` (GLB → turntable).

---

## UPDATE 2026-06-06 — the three deferred items were run. Verdict changed.

Brian's priority: **hyper-realistic + personalized face**. Ran all three follow-ups eyes-on.

### Hybrid mesh (multi-view Hunyuan) — modest win, still CGI
FLUX-synthesized back/left/right/45° views fed into Hunyuan Pro's multi-view slots
(`back_image_url` etc.) + `enable_pbr` + `face_count=1M` → `spike/output/spin/*_hybrid.glb`
(60 MB). Better hair, real back, PBR skin — **but still reads as a game character, and the
face is generic-smooth, not unmistakably the user.** Conclusion: **don't bake identity into a mesh.**

### Dense 12-frame FLUX turntable — photoreal per-frame, but DRIFTS
`spike/output/spin/dense/` (every 30°, fixed seed). Each frame is photoreal, but
independently generated → **framing jumps, background changes, face/body drift frame-to-frame.**
A spin made of these flickers. Proves you need a consistency anchor.

### ★ Video-orbit (Seedance 2.0 i2v) — THE WINNER
`bytedance/seedance-2.0/image-to-video`, 720p/8s/portrait, turntable prompt, ~$1.
→ `spike/output/spin/*_orbit.mp4`. **Photoreal, smooth, identity- and background-stable
all the way around** (front→side→back→front; same physique, same shorts, same locker room).
The video model's temporal coherence kills the 2D drift. **Tradeoff: a fixed clip, not free-drag.**

### Revised recommendation
- **Near-term wow (ship-able):** **video-orbit turntable** from the engine-governed Arch-A still.
  Photoreal + smooth + you, no GPU, ~$1/clip. Best realism-per-effort by far.
- **Interactive free-rotate (later):** the **mesh** is the only true drag-anywhere option, but
  needs the geometry-locked photoreal paint + face-lock to stop looking like a game character.
- **Identity:** keep the face in the 2D/video layer (face-locked), never baked into mesh texture.
- **More photos** (real back/side) materially improve any mesh path — a real product lever
  (1-photo low-friction vs 3–5-photo high-fidelity).

Interactive comparison of all three: `spike/viewer/index.html` (served at :8731).
Repro: `spike/hybrid.py`, `spike/dense_spin.py`, `spike/orbit.py`.
