# PhysiqAI Avatar Research - Findings

**Date:** 2026-02-02
**Status:** Initial feasibility testing complete

---

## Summary

We tested Google's Gemini 2.5 Flash Image model for body transformation capabilities.

### What Works
- ✅ **Photorealistic generation** — Quality is excellent
- ✅ **Identity preservation** — Same face across transformations
- ✅ **Composition preservation** — Pose, background, clothing maintained
- ✅ **API reliability** — Google AI Studio works, has free tier

### What Needs Work
- ⚠️ **Transformation magnitude** — Changes are too subtle
- ⚠️ **Specific muscle targeting** — Hard to change just one body part
- ⚠️ **Bi-directional control** — Making someone MORE or LESS muscular equally limited

---

## Test Results

### Test 1: Stock Photo Transformation
- **Input:** Man with dumbbells (forearms visible)
- **Prompt:** "Make arms more muscular"
- **Result:** Very subtle change, barely noticeable

### Test 2: Personal Trainer Photo
- **Input:** Man doing pushups with trainer
- **Prompt:** "6 months of bodybuilding"
- **Result:** Noticeable shoulder/arm improvement, face preserved

### Test 3: Generated Image Modification  
- **Input:** AI-generated muscular man (double bicep pose)
- **Prompts:** Make leaner, smaller arms, bulkier
- **Result:** Minimal visible changes, face perfectly preserved

---

## Technical Notes

### API Used
```
Model: gemini-2.5-flash-image
Endpoint: generativelanguage.googleapis.com/v1beta
Method: generateContent with IMAGE + TEXT parts
```

### Cost
- Google AI Studio: Free tier available
- fal.ai: Needs credits (account exhausted)
- Replicate: Needs credits (account exhausted)

---

## Recommended Next Steps

### Short Term (This Week)
1. **Test stronger prompts** — Use percentage-based instructions ("increase arm size by 30%")
2. **Test inpainting** — Mask body parts, regenerate just those regions
3. **Top up fal.ai/Replicate** — Test Flux 2, SDXL with ControlNet

### Medium Term (2-4 Weeks)
1. **Build segmentation pipeline** — Use SAM to create body part masks
2. **Test multi-pass transformation** — Run same image through 3-5x to accumulate changes
3. **Research fine-tuned models** — Look for fitness/body transformation LoRAs on Civitai

### Long Term (If Above Fail)
1. **Custom LoRA training** — Collect before/after photos, fine-tune
2. **3D body model approach** — SMPL-X mesh modification + neural rendering
3. **Partner with existing solution** — Find startups already doing this (BODDY, etc.)

---

## Files Generated

All test outputs in `projects/physiqai/research/`:
- `gemini-flash-output-0.png` — Text-to-image generated muscular male
- `face-body-*.png` — Transformation tests on pushup photo
- `generated-*.png` — Reverse tests (muscular → less muscular)
- `test-*.js` — Node.js test scripts

---

## Verdict

**Feasibility: PARTIAL**

The technology exists and works for identity preservation, but getting DRAMATIC body changes requires more sophisticated approaches than simple prompting. 

Recommendation: Continue prototyping with inpainting/segmentation approach before committing to full app development.
