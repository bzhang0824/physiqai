# PhysiqAI — Product Requirements Document

*Updated: 2026-02-03 with BZ feedback*

## Vision
An AI "Virtual Mirror" that shows users their realistic future physique based on their workout plan, genetics, and consistency — creating accountability through visualization.

## Problem Statement
Fitness motivation dies when results feel distant. Generic transformation photos show what's *possible*, not what's *probable for you*. Users lack a personalized, science-based preview of their trajectory.

## Solution
PhysiqAI generates hyper-realistic body transformation images based on:
- User's current physique (photo from any angle)
- Their specific workout plan
- Physiological factors (age, genetics, experience)
- Time horizon selected

**Key differentiator:** Every transformation includes a personalized explanation of WHY we predicted those specific changes.

---

## Target User
**"Results-Seeking Intermediate"**
- Age: 18-45 (core demographic)
- Already goes to the gym but struggles with consistency
- Wants to see if their current plan will actually work
- Motivated by visual progress, not just metrics

---

## MVP Scope (Alpha)

### Core Flow
1. User uploads photo (any angle — front, side, back)
2. User enters physique + plan inputs
3. User selects time horizon(s)
4. System generates side-by-side transformation image(s)
5. **System explains WHY it made those predictions**

### User Inputs (MVP)

| Category | Inputs |
|----------|--------|
| **Demographics** | Age, Gender, Race/Ethnicity (for skin tone + genetic factors) |
| **Physical** | Height, Weight, Body fat % (estimate or AI-detected) |
| **Experience** | Training experience level (beginner/intermediate/advanced) |
| **Plan** | Workout split, Focus areas (muscle groups), Weekly frequency, Cardio frequency |
| **Lifestyle** | Sleep quality (poor/average/good), Nutrition approach (cut/maintain/bulk) |

### Time Horizons
- **Short-term:** 4 weeks, 8 weeks, 12 weeks
- **Long-term:** 6 months, 1 year

### Output
- Side-by-side image: Current (uploaded photo) | Projected (AI-generated)
- **Confidence score** with breakdown (high/medium/low)
- **Personalized reasoning** explaining the prediction
- Multiple horizons shown if selected
- Debug panel showing prompt (dev mode only)

### Content Moderation
- Accept: Shirtless, athletic wear, swimwear, gym clothes
- Block: Explicit content, nudity in genital areas
- Clear error message guiding user to appropriate photos

### Multi-Angle Support
- Front-facing
- Side profile (left/right)
- Back
- Three-quarter angles
- System detects pose and adjusts generation accordingly

### Excluded from MVP
- User accounts / authentication
- Workout tracking integration
- Avatar deflation mechanic (requires tracking)
- Mobile apps (web only)
- Watermarks
- Download/share features
- Slider/morph animation

---

## Personalized Reasoning Feature

Every transformation includes:

### Summary
1-2 sentence overview of the projection

### Factors Considered
For each input, explain:
- What the user entered
- How it impacts results
- Why (educational)

### Limiting Factors
What's holding back optimal results:
- Sleep quality issues
- Training frequency
- Nutrition approach
- Age considerations

### Confidence Explanation
Why confidence is high/medium/low based on:
- Photo quality
- Lighting
- Body visibility
- Input completeness

**Example:**
```
📊 Why This Projection

Based on your profile, we project significant visible progress 
in 12 weeks, particularly in your focus areas (chest, arms).

✅ Training Experience: Beginner
   → You're in the "newbie gains" window — up to 2 lbs/month

⚠️ Limiting Factor: Sleep (Average)
   → Reduces potential gains by ~10%

Confidence: HIGH ✅
```

---

## Post-MVP Features (Roadmap)

### Phase 2: Workout Tracking
- Log workouts manually or integrate (Apple Health, Strava, etc.)
- Avatar updates based on actual adherence
- **Deflation mechanic:** Missed workouts cause avatar to regress
- Weekly/monthly progress snapshots

### Phase 3: Engagement
- Social sharing with watermark
- Progress time-lapse video generation
- Comparison against "optimal" trajectory
- Community challenges

### Phase 4: Monetization
- Free: 1 transformation per month
- Pro: Unlimited + tracking + time-lapse ($9.99/mo)
- Trainer tier: Client management ($29.99/mo)

---

## Success Metrics (Alpha)
- Users complete full input → generation flow (conversion rate)
- Subjective realism score (user feedback)
- Return visits within 7 days
- Qualitative: "Does this look like ME, just fitter?"
- Reasoning helpfulness rating

---

## Constraints
- Must be physiologically plausible (no fantasy bodies)
- Must preserve user identity (face, skin tone, distinguishing features)
- Must show region-specific changes (train arms → arms grow, not everything)
- Generation time: Quality over speed (25-40 seconds acceptable)
- Must block explicit content appropriately

---

## Open Questions (to resolve during build)
- How to handle users with very high or very low starting body fat?
- Should we show "realistic" vs "optimistic" projections?
- How to communicate uncertainty in predictions?
