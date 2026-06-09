# PhysiqAI — Where We Are (read this first)

*Plain-English walkthrough of everything built & decided. Updated 2026-06-01.*

---

## 1. What we're building (the one-liner)
Upload a photo + your stats + your plan → see a **hyper-realistic, science-honest picture of your future
body**, keeping your real face. The wedge: every competitor makes **fantasy** ("not me / fake" in reviews).
Ours is **believable + "it's really you" + defensible by real science.** Believability is the moat.

## 2. What we did this round (and proved) — total spend ~$2
- **Audited the old build.** Kept the gold (physiology math, science docs, SMPL files, data). Threw out the
  fakes (hash-based "body fitter", cylinder "3D avatar", 3 half-built apps).
- **Surveyed 2026 SOTA tools** (16-agent research) → picked a stack reachable through one hub (fal.ai).
- **Proved the core works on REAL photos** (the thing that *never worked* before):
  - `SAM 3D Body` → accurate 3D body from a casual selfie ($0.02). ✓
  - `Nano Banana Pro` → identity-preserving morph, even on your own photos. ✓
  - Validated against **real before/after pairs** — which revealed the key truth ↓
- **The key truth we learned:** identity preservation is solid; **magnitude (how much you change) is the
  unreliable part** — the image model under-shoots big losses, over-shoots small gains. → that's *why* the
  physiology engine (as a governor) and Arch B (3D geometry) matter.
- **Proved the face-drift fix** (face-lock): keep your real face pixels, never let AI repaint them. ✓

## 3. The physiology engine — "the governor" (the heart of it)
Think of it as **the rulebook for how a body realistically changes.** It's the moat competitors lack.

- **Inputs:** your stats + goal + plan + time horizon (full list in `docs/ONBOARDING_SPEC.md`).
- **What it does:** energy balance → splits change into lean vs fat (P-ratio) → simulates **week by week**
  with a real **body-fat floor** (can't promise impossible leanness), a **natural muscle ceiling** (FFMI),
  and **honest ranges** (not fake precision) → outputs body + measurement changes + a confidence %.
- **3 bugs we fixed:** (1) it used to predict impossible 5% body fat → now floors realistically;
  (2) "muscle gain" used to pile on fat → now lean-bulk ≠ dirty bulk; (3) fake confidence → now a
  principled range.
- **Built test-first: 34 passing tests, every number cited** (McDonald, Helms, Aragon, Kouri, Schoenfeld...).
- **Triple-validated against reality:**
  1. Published RCT meta-analyses (~3,800 subjects) → **7/7 scenarios defensible**
  2. 10,799 real DXA body scans (NHANES) → floors & muscle ceiling **confirmed**
  3. 473 real Reddit transformations → weight-change MAE 9.8 lb (noise explained)
- **Verdict:** scientifically defensible. (`docs/ENGINE_SPEC_DRAFT.md`, `docs/VALIDATION_*`, `models/governor/`)

## 4. How the whole app works (the architecture)
**Separate the TRUTH from the LOOK** — that's the core insight:
- **Geometry / magnitude = the truth layer** → the physiology engine (+ later, a morphable 3D body) decides
  *how much* you change. Keeps it honest.
- **Appearance / identity = the look layer** → the image model paints a realistic result; **face-lock** keeps
  it unmistakably *you*.

Three versions, in order:
- **A — Realistic photo edit (MVP):** mask body → engine-bounded prompt → Nano Banana Pro → face-lock. Works now.
- **B — 3D-governed (the deeper moat):** morph a 3D body by the engine's numbers → forces correct magnitude.
- **C — Dynamic 3D mirror (V2):** rotatable avatar + transformation video + the living/accountability loop.

## 5. What you can touch right now
- **Dashboard** (all test results in one place): `bash spike/dash.sh`
- **Poke the engine** (instant, free): `bash spike/numbers.sh <goal> <weeks> <pref>`
- **Generate a morph** (~$0.15): `bash spike/morphit.sh <goal> <weeks> <pref>`
- **Key docs:** `VISION.md` (the wow) · `docs/ENGINE_SPEC_DRAFT.md` (the engine) ·
  `docs/ONBOARDING_SPEC.md` (the questions we ask users) · `docs/VALIDATION_MANIFEST.md` (the science) ·
  `spike/FINDINGS.md` (what the spike proved) · `_MASTER_CONTEXT.md` (original honest brief)

## 6. The roadmap
- ✅ **Done:** core proven · physiology engine built + triple-validated · identity fix proven · dashboard
- ✅ **Done:** **production generation pipeline (Arch A)** — TDD'd package in `pipeline/` (27 tests):
  `engine_bridge` (profile→MorphSpec) → `prompt` (bounded, identity-locked) → `generate`
  (Nano Banana Pro) → `facelock` (real-face composite, OpenCV) → `identity` gate + `run` orchestrator
  (retry→fallback→pick-best). Live E2E smoke on Brian's photo passed all gates (identity restored,
  magnitude bounded, background untouched, ~$0.15/gen ~28s). See `spike/output/pipeline/*_3panel.png`.
  Pending wiring: facenet auto-gate (`pipeline/identity_score.py`, needs `pip install torch facenet-pytorch`)
  and Florence2+SAM2 body-mask inpaint (an Arch-B hardening step).
- ✅ **Done:** **app shell — thin vertical slice (works end-to-end).** On branch `app-shell`.
  - **Backend** `server/` (FastAPI): `POST /transform` (multipart photo + stats) → `to_engine_inputs`
    (TDD, 12 tests) → engine → `generate_nano_banana` → `apply_facelock` → returns before/after URLs +
    projection JSON. `GET /health`. Run: `bash server/run.sh` (uvicorn :8000). Reuses `pipeline/`+engine.
  - **Mobile** `mobile/` (Expo SDK 56, expo-router, TS): Welcome → Photo (expo-image-picker) → Stats →
    Horizon → Loading → Results (before/after + confidence + "why"). Dark theme per guidelines.
  - **Verified end-to-end** via Playwright on Expo Web (no iOS Simulator installed): full flow, zero
    console errors, real face-locked before/after rendered, engine numbers correct. Screens in `mobile/e2e/`.
  - **Note:** no full Xcode → use Expo Web / real iPhone (Expo Go) to view; `app.json` `extra.apiUrl`
    switches localhost↔LAN IP. Next: expand to full 22-input onboarding + polished results.
- ⏭️ **Next:** full onboarding (`docs/ONBOARDING_SPEC.md`) + polished results · then B2C essentials
  (moderation, legal/BIPA, paywall via RevenueCat, Supabase persistence) · then Arch B + the 3D avatar
  (separate session) plugging in via a `/avatar` route. See the plan: `~/.claude/plans/ok-this-is-a-dapper-shell.md`.
- 🔮 **The data flywheel:** the best calibration data is your future users' real before/after + outcomes —
  we build the app to capture it so the engine self-improves on exactly our audience.

## 7. Open decisions waiting on you
- Platform for the app shell (mobile/Expo is the stated goal; could ship web first to validate).
- When to add Arch B (now for max accuracy, or after an MVP ships).
- Any tools/budget for the generation-pipeline build (still just fal.ai; ~$0.06–0.17 per generation).
