# PhysiqAI Lessons Learned

## Research Phase

### Image Generation Models (2026-02-02)
- **Flux Kontext Pro** is the best option for body editing with identity preservation
- Gemini 2.5 Flash Image works but transformations are too subtle
- Identity preservation is the hardest part — most models make "ideal" bodies, not YOUR body transformed
- Recommend hybrid approach: SMPL-X for physiological guidance + Flux for rendering

### API Providers
- **fal.ai** — Fast, reliable, good Flux support (~$0.04/image)
- **Replicate** — Works but slower queue times
- **Google AI** — Free tier generous for Gemini, good for analysis tasks

## Product Decisions

### MVP Scope (2026-02-03)
- Start with web only (no mobile app)
- Single front-facing photo (expand later)
- No auth — just testing functionality
- No watermarks — internal use
- User-selectable time horizons (4wk to 1yr)

### Key Differentiator
The "moat" is the **Living Avatar** concept:
- Avatar improves when workouts logged
- Avatar regresses when workouts missed
- Creates accountability loop
- Generic AI = fantasy; PhysiqAI = YOUR trajectory

### User Inputs Needed
Demographics: age, gender, ethnicity (skin tone + genetics)
Physical: height, weight, body fat %, training experience
Plan: workout split, focus areas, frequency, cardio, sleep quality, nutrition goal

## Technical Learnings

### Voice/Audio Processing
- Gemini 2.0 Flash handles audio well via File API
- For large files (>500KB), upload first then reference by URI
- Base64 inline works for smaller files but hits argument limits

---

*Add learnings as you build!*
