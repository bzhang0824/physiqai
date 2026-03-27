# PhysiqAI — Application Flow

*Updated: 2026-02-03 with BZ feedback*

## User Journey (MVP)

```
┌─────────────────────────────────────────────────────────────────┐
│                         LANDING PAGE                             │
│  "See your future physique"                                      │
│  [Get Started] button                                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      STEP 1: PHOTO UPLOAD                        │
│  • Drag & drop or click to upload                                │
│  • Any angle accepted (front, side, back)                        │
│  • Content moderation check (block explicit)                     │
│  • Preview with crop/adjust                                      │
│  • Guidance: "Clear photo, good lighting, body visible"          │
│  • [Continue] button                                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 2: BASIC INFO                            │
│  Demographics:                                                   │
│  • Age (number input)                                            │
│  • Gender (select: Male / Female / Other)                        │
│  • Ethnicity (select: for skin tone + genetic factors)           │
│                                                                  │
│  Physical Stats:                                                 │
│  • Height (ft/in or cm toggle)                                   │
│  • Weight (lbs or kg toggle)                                     │
│  • Body fat % (slider 5-50% OR "Let AI estimate")                │
│  • Training experience (Beginner / Intermediate / Advanced)      │
│                                                                  │
│  [Continue] button                                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   STEP 3: WORKOUT PLAN                           │
│  Current/Planned routine:                                        │
│  • Workout split (PPL / Bro Split / Upper-Lower / Full Body)     │
│  • Focus areas (multi-select: Chest, Back, Arms, Shoulders,      │
│                 Legs, Core, Glutes)                              │
│  • Weekly workout frequency (1-7 days slider)                    │
│  • Weekly cardio sessions (0-7 slider)                           │
│                                                                  │
│  Lifestyle:                                                      │
│  • Sleep quality (Poor / Average / Good)                         │
│  • Nutrition goal (Cut / Maintain / Bulk)                        │
│                                                                  │
│  [Continue] button                                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  STEP 4: TIME HORIZON                            │
│  "When do you want to see yourself?"                             │
│                                                                  │
│  Quick select (multi-select chips):                              │
│  [4 weeks] [8 weeks] [12 weeks] [6 months] [1 year]             │
│                                                                  │
│  User can select multiple for comparison                         │
│                                                                  │
│  [Generate My Transformation] button                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LOADING / PROCESSING                          │
│  • Progress indicator                                            │
│  • "Analyzing your physique..."                                  │
│  • "Calculating muscle growth trajectory..."                     │
│  • "Rendering your future self..."                               │
│  • Estimated time: 25-40 seconds per image                       │
│  • [Cancel] option available                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      RESULTS PAGE                                │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              SIDE-BY-SIDE COMPARISON                      │   │
│  │  ┌─────────────┐    ┌─────────────┐                      │   │
│  │  │   TODAY     │    │  [X] WEEKS  │  ← Tab for each      │   │
│  │  │  (original) │    │ (generated) │    horizon            │   │
│  │  └─────────────┘    └─────────────┘                      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              CONFIDENCE SCORE                             │   │
│  │  Confidence: HIGH ✅ (92/100)                             │   │
│  │  ✓ Photo quality: Excellent                               │   │
│  │  ✓ Lighting: Good                                         │   │
│  │  ⚠ Body fat: Auto-estimated                               │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              WHY THIS PROJECTION                          │   │
│  │                                                           │   │
│  │  Summary: Based on your profile, we project significant   │   │
│  │  progress in 12 weeks, particularly in chest and arms.    │   │
│  │                                                           │   │
│  │  ✅ Training Experience: Beginner                         │   │
│  │     → "Newbie gains" window: up to 2 lbs/month           │   │
│  │                                                           │   │
│  │  ✅ Frequency: 5x/week PPL                                │   │
│  │     → Optimal stimulus for muscle growth                  │   │
│  │                                                           │   │
│  │  ⚠️ Limiting Factor: Sleep (Average)                      │   │
│  │     → Reduces potential gains by ~10%                     │   │
│  │                                                           │   │
│  │  [Show More Details]                                      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  DEBUG PANEL (dev mode only, ?debug=true)                 │   │
│  │  Prompt used: "Keep the exact same face..."               │   │
│  │  Model: flux-kontext-pro                                  │   │
│  │  Steps: 38 | Guidance: 7.5 | Time: 34.2s                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  [Try Different Plan] [Start Over]                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Screen Inventory

| Screen | Route | Purpose |
|--------|-------|---------|
| Landing | `/` | Hook + CTA |
| Photo Upload | `/transform/photo` | Capture user image (any angle) |
| Basic Info | `/transform/info` | Demographics + physicals |
| Workout Plan | `/transform/plan` | Training details |
| Time Horizon | `/transform/timeline` | Select projection periods |
| Processing | `/transform/loading` | Generation in progress |
| Results | `/transform/results` | Display transformations + reasoning |

---

## State Management

### Session Data (no auth = localStorage/sessionStorage)
```typescript
interface TransformSession {
  photo: {
    file: File | null;
    preview: string; // base64 or blob URL
    detectedPose: 'front' | 'side-left' | 'side-right' | 'back' | 'three-quarter';
    moderationPassed: boolean;
  };
  demographics: {
    age: number;
    gender: 'male' | 'female' | 'other';
    ethnicity: string;
  };
  physique: {
    heightCm: number;
    weightKg: number;
    bodyFatPercent: number | 'auto';
    experienceLevel: 'beginner' | 'intermediate' | 'advanced';
  };
  plan: {
    split: 'ppl' | 'bro' | 'upper-lower' | 'full-body' | 'custom';
    focusAreas: string[];
    workoutsPerWeek: number;
    cardioPerWeek: number;
    sleepQuality: 'poor' | 'average' | 'good';
    nutritionGoal: 'cut' | 'maintain' | 'bulk';
  };
  horizons: number[]; // weeks: [4, 12, 52] etc.
  results: {
    [weeks: number]: {
      imageUrl: string;
      projections: {
        leanMassChangeKg: number;
        bodyFatChangePercent: number;
        regionalChanges: Record<string, number>;
      };
      confidence: {
        level: 'high' | 'medium' | 'low';
        score: number;
        factors: Array<{ name: string; status: string; note: string }>;
      };
      reasoning: {
        summary: string;
        factors: Array<{ factor: string; value: string; impact: string; explanation: string }>;
        limitingFactors: string[];
      };
      debug?: {
        promptUsed: string;
        modelParams: object;
        generationTimeMs: number;
      };
    };
  };
}
```

---

## Error States

| Scenario | Handling |
|----------|----------|
| Photo upload fails | Retry button, file size/type guidance |
| Explicit content detected | "Please upload an appropriate fitness photo" + guidance |
| Invalid inputs | Inline validation, can't proceed until fixed |
| Generation fails | Auto-retry with adjusted params, then show error with options |
| Generation timeout | "Taking longer than expected" + [Cancel] option |
| Face changed too much | Auto-retry silently, user doesn't see this |

---

## Edge Cases

- **Unusual pose:** Detect and adjust prompt accordingly
- **Poor lighting:** Warn but allow, note in confidence score
- **Extreme body fat inputs:** Cap at physiologically possible ranges
- **Multiple horizons:** Generate sequentially, show progress bar per horizon
- **Browser refresh during flow:** Restore from sessionStorage if available
- **Explicit content:** Block immediately with clear guidance
