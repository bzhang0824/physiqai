# PhysiqAI — Phase 0 Spike Findings (2026-05-29)

**Question the spike had to answer:** before building anything, can today's tools actually deliver
the core feature — *a realistic, identity-preserving, physiologically-honest future-physique image*?
**Answer: YES, on both tracks.** Total spend ≈ **$0.67** (budget was $20-50).

Verified with **eyes on real output** (10 real Reddit body photos), per the discipline the prior build skipped.

---

## Track B — Photo → 3D body (the moat's geometry layer): **PASS**

Tool: `fal-ai/sam-3/3d-body` ($0.02/photo, ~12s). Verified real (not a hallucinated endpoint).

- On genuine single-person photos, the 3D body reconstruction is **accurate** — faithfully captured a
  heavyset man's belly/proportions/posture (front + side) and a woman shot from behind (hips, legs, profile).
- **Returns the parametric shape parameters** (45 `shape_params` + 204 `mhr_model_params`) the morph
  engine needs — confirms the Anny-bridge input exists.
- "Multiple people detected" cases (4/10) were **collages + mirror reflections**, not model errors —
  each individual mesh was still good.
- **Free production guard:** the API returns `num_people` + per-person bounding boxes, so rejecting bad
  uploads / auto-selecting "the user" (largest, central body) is trivial.

→ Architecture B (geometry-governed transformation) is viable. The riskiest assumption is cleared.

## Track A — Identity-preserving photo edit (the MVP): **PASS (strong)**

Tools: real `BodyPredictor` (physiology engine) → bounded prompt → `fal-ai/nano-banana-pro/edit`
($0.15/img, ~25-30s). Ran **maskless**.

- **p06 (heavyset man, 6-mo fat loss):** engine said 232→215 lb, 31→25% BF (conf 0.95). Result: **same
  face, same bathroom, same phone/pose, realistically leaner — not a bodybuilder.** Exactly the product promise.
- **p02 (lean man, muscle gain, in a t-shirt):** identity/background perfect; change subtle — *you can't
  show recomposition under a t-shirt*.
- **p08 (woman, recomp, gym):** identity/background/pose perfect; change subtle (small delta).
- Identity + background + lighting + pose preservation was **excellent across all three, with no mask** —
  this was the prior build's #1 failure (BUG-005, "different person"), now solved by Nano Banana Pro.

→ Architecture A (the MVP) works today, and simpler than expected (masking optional, not required for v1).

---

## What we learned (feeds the build)

1. **The core feature is real and cheap.** ~$0.06-0.17 per generation, ~15-30s. Healthy margin at $7.99/mo.
2. **The physiology engine governs cleanly.** Conservative, realistic numbers → realistic prompt → no fantasy.
3. **Visible change depends on (a) magnitude and (b) clothing.** Fat-loss on a shirtless subject = dramatic
   and compelling; subtle recomp under clothing = barely visible. → **Onboarding must guide users to fitted/
   minimal clothing + good framing** (like body-scan apps). Most compelling results: weight-loss, longer horizons.
4. **Goal→engine-param mapping needs care.** `WorkoutType.MUSCLE_GAIN` assumes a calorie surplus (bulk), so a
   female "tone up / lose fat" intent produced a *bodyfat increase*. The app must map user goals to the right
   engine config (recomp/maintenance vs bulk vs cut).
5. **Input quality is the real gatekeeper.** The Reddit corpus is collage-heavy; SAM 3D Body's `num_people`
   gives us a free "one clear person, fitted clothing, full body" upload check to enforce.

## Gate decision
Both tracks pass → proceed per plan: **ship Architecture A as the MVP** (proven, maskless, simplest),
**build Architecture B as the moat** (geometry governor; mesh quality confirmed). The open R&D remains the
MHR→Anny morph bridge (Phase 2).

## Recommended next validations (not yet done)
- Render a SAM 3D Body GLB → depth map → `fal-ai/flux-pro/kontext` + depth-ControlNet (proves Arch B's
  appearance stage end-to-end).
- Test on **clean, fitted-clothing, full-body** photos (ideally Brian's own) for a truer identity read.
- Add `fal-ai/sam2/image` body masking and compare vs maskless (robustness on edge cases).

## Ground-truth validation (answers "how do we know the after is accurate?")

**Method:** the corpus has **665 real before/after posts with documented weight deltas**. We take the
REAL before, drive our pipeline with the person's ACTUAL documented weight change, generate our after,
and compare to their REAL after photo. This validates the *visual magnitude* against reality (the engine's
*numeric* accuracy was separately validated at r≈0.82 in the prior build). Artifacts: `spike/output/val/*_3panel.png`.

**Result on 2 real cases — a critical, decision-relevant finding:**
- **#1 (315→165 lb, −150 lb):** our generated image was only *modestly* slimmer (looked like ~−30 lb);
  the real after was dramatically slim. **Massive under-shoot.** (Loose dress also masked the change.)
- **#9 (240→176 lb, −64 lb):** our "−64 lb" looked like ~−15-20 lb; real after clearly far leaner. **Under-shoot.**

**Conclusion:** maskless prompt-driven Nano Banana Pro is **excellent at identity/background preservation
and realistic for SMALL/MODERATE changes** (e.g. the −17 lb p06 case looked great), but **systematically
UNDER-delivers the magnitude of LARGE changes** — the image model doesn't actually "know" what 64 or 150 lb
looks like, so it guesses conservatively. It's *honest-leaning* but *inaccurate at scale.*

**This is the empirical case FOR Architecture B (the moat):** morph a 3D mesh to the real target body, then
let the image model paint within that fixed silhouette — the magnitude is *forced by geometry*, not guessed
by the prompt. It also means the Arch-A MVP is most trustworthy for **shorter horizons / moderate changes**,
and we should validate every magnitude band against this 665-pair ground-truth set before shipping claims.

## Test on Brian's own photos (real subject, shirtless = high visibility)

- **Track B (mesh):** SAM 3D Body captured his lean V-taper build/poses accurately; 3/4 single-person
  (one picked up a mirror reflection). Works on a lean muscular subject.
- **Track A (edit):** muscle-gain transformation on shirtless shots — **identity, pose, background, clothing
  preserved perfectly**, believable natural muscle increase (`spike/output/bz_trackA/*_compare.png`).
- **Magnitude is unreliable in BOTH directions (confirms the core finding):** engine predicted only +3.6 lb
  lean over a year (realistic for an advanced lifter) but the image over-delivered the size. Earlier it
  *under*-delivered big losses. → image model can't be trusted on magnitude → **Architecture B (geometry
  governor) is the fix.**
- **Goal→mode mapping nuance:** `WorkoutType.MUSCLE_GAIN` assumed an aggressive bulk (158→169 lb but BF
  11%→16%). Need a **lean-bulk / recomp mode** for "add muscle, stay lean" intent.

## Artifacts (in `spike/`)
- `photos/` — 10 curated real test photos · `output/sam3d/` — meshes + visualizations + shape params
- `output/trackA/*_compare.png` — before/after edits · `output/sam3d_meshes.png` — mesh montage
