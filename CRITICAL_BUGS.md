# CRITICAL BUGS - PhysiqAI Generation Pipeline

*Created: 2026-02-03 04:29 UTC*

---

## BUG-005: CRITICAL - Face/Identity Completely Changed
**Severity:** 🔴 CRITICAL (Product Breaking)  
**Status:** OPEN  

**Description:**
Generated image shows completely different facial features, jawline, and structure. This is a different person, not a transformation of the original person.

**Expected:** Same face, same person, just different muscle mass  
**Actual:** Different person entirely  

**Test to Write:**
```python
def test_face_identity_preservation():
    """Test that face remains identical after transformation"""
    original_face_embedding = extract_face_embedding(original_image)
    generated_face_embedding = extract_face_embedding(generated_image)
    similarity_score = cosine_similarity(original_face_embedding, generated_face_embedding)
    assert similarity_score > 0.90, f"Face similarity {similarity_score} below threshold"
```

**Root Cause:** Flux Kontext Pro model changing identity despite explicit constraints in prompt

---

## BUG-006: CRITICAL - Transformation Unrealistically Dramatic  
**Severity:** 🔴 CRITICAL (Science Accuracy)  
**Status:** OPEN  

**Description:**
6-month bulk projection shows extreme muscle development that would take 3-5 years naturally. The transformation looks like elite genetics + perfect conditions + possible enhancement.

**Expected:** Realistic 6-month gains (~6-12 lbs muscle max for intermediate)  
**Actual:** 30+ lbs muscle appearance, fitness model physique  

**Test to Write:**
```python
def test_realistic_muscle_gain_bounds():
    """Test that projections don't exceed scientific maximums"""
    projected_muscle_gain = estimate_visual_muscle_gain(original, generated)
    max_natural_gain = calculate_max_gain(profile, horizon_weeks)
    assert projected_muscle_gain <= max_natural_gain * 1.2, "Visual gains exceed physiological limits"
```

**Root Cause:** Model ignoring quantified muscle gain amounts, defaulting to "generic muscular look"

---

## BUG-007: HIGH - Generated Image Looks AI/Synthetic
**Severity:** 🟡 HIGH (User Trust)  
**Status:** OPEN  

**Description:**
Result has "AI generated" appearance - too perfect, too symmetrical, uncanny valley effect.

**Expected:** Natural-looking transformation photo  
**Actual:** Obviously AI-generated fitness model  

**Test to Write:**
```python
def test_natural_appearance():
    """Test that generated image looks natural, not AI-synthetic"""
    ai_detection_score = detectron_ai_classifier(generated_image)
    assert ai_detection_score < 0.7, "Image detected as AI-generated"
```

**Root Cause:** Model producing "ideal" bodies instead of "your body improved"

---

## BUG-008: HIGH - Lighting/Environment Changes
**Severity:** 🟡 HIGH (Comparison Difficulty)  
**Status:** OPEN  

**Description:**
Generated image has different lighting direction, intensity, or color temperature making before/after comparison difficult.

**Expected:** Identical lighting and shadows  
**Actual:** Different lighting conditions  

**Test to Write:**
```python
def test_lighting_preservation():
    """Test that lighting conditions remain identical"""
    original_lighting = analyze_lighting_direction(original_image)
    generated_lighting = analyze_lighting_direction(generated_image)
    difference = lighting_difference(original_lighting, generated_lighting)
    assert difference < 15, "Lighting changed significantly"
```

**Root Cause:** Model not maintaining environmental conditions

---

# SOLUTIONS TO RESEARCH

## Immediate Fixes to Test

1. **Lower Guidance Scale** - Try 4.0-5.0 instead of 7.5 (less dramatic changes)
2. **Simpler Prompts** - Remove anatomy details that might confuse model
3. **Seed Control** - Use fixed seeds for consistent results
4. **Generation Settings** - Higher steps (50) for more precise control

## Multi-Model Pipeline Implementation

From brainstorm document, implement:

### Pipeline Option A: Identity + Body Separate

```
Original Image
    ↓
1. Extract Face (IP-Adapter-FaceID embedding)
    ↓
2. Generate Body Changes (Flux with face embedding constraint)
    ↓
3. Composite Result (ensure face embedding preserved)
```

### Pipeline Option B: ControlNet + Inpainting

```
Original Image
    ↓
1. Use ControlNet to lock pose+face
    ↓
2. Use SAM to segment body regions only
    ↓
3. Inpaint body changes while preserving everything else
```

### Pipeline Option C: Multi-Generation Selection

```
Generate 3 variants with different settings
    ↓
Automated quality checks (face similarity, realism)
    ↓
Return best result OR let user choose
```

## Alternative Models to Research

| Model | Strength | Availability | Cost |
|-------|----------|--------------|------|
| IP-Adapter-FaceID | Identity preservation | Replicate/HF | ~$0.02 |
| ControlNet OpenPose | Pose locking | Local/Remote | Variable |
| Stable Video Diffusion | Controlled changes | Replicate | ~$0.08 |
| InstantID | Face consistency | Replicate | ~$0.03 |

## Research Questions

1. **IP-Adapter Integration**: Can we layer IP-Adapter-FaceID on Flux?
2. **ControlNet Approach**: Use pose/depth control for body-only changes?
3. **Inpainting Strategy**: SAM segment + targeted body modifications?
4. **Quality Metrics**: Automated face similarity + realism scoring?

---

# ACTION PLAN

## Phase 1: Quick Fixes (Test Immediately)
- [ ] Lower guidance_scale to 4.5
- [ ] Add negative prompting ("DO NOT change face structure")
- [ ] Test with simpler prompt (remove anatomy details)

## Phase 2: Alternative Model Research
- [ ] Test IP-Adapter-FaceID for identity preservation
- [ ] Test ControlNet + Flux combination  
- [ ] Research InstantID capabilities

## Phase 3: Pipeline Implementation
- [ ] Build multi-model generation system
- [ ] Add automated quality checks
- [ ] Implement fallback strategies

---

*Next: Write the bug reproduction tests, then systematically fix each issue*