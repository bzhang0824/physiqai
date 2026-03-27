# PhysiqAI — Technology Stack

## Overview

```
┌──────────────────────────────────────────────────────────────┐
│                         FRONTEND                              │
│  Next.js 14 (App Router) + TypeScript + Tailwind + shadcn/ui │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                      API LAYER                                │
│  Next.js API Routes (serverless functions)                    │
└──────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
┌─────────────────────────┐  ┌─────────────────────────┐
│   TRANSFORMATION ENGINE │  │      STORAGE            │
│   • Flux Kontext Pro    │  │   • Vercel Blob (images)│
│     (via fal.ai)        │  │   • localStorage (MVP)  │
│   • SMPL-X (optional)   │  │                         │
└─────────────────────────┘  └─────────────────────────┘
```

---

## Frontend

| Technology | Purpose | Why |
|------------|---------|-----|
| **Next.js 14** | Framework | App Router, RSC, API routes in one. Vercel deploy = zero config |
| **TypeScript** | Type safety | Catch errors early, better DX |
| **Tailwind CSS** | Styling | Utility-first, fast iteration |
| **shadcn/ui** | Components | Copy-paste components, fully customizable, not a dependency |
| **React Hook Form** | Forms | Multi-step form state management |
| **Zod** | Validation | Schema validation for inputs |
| **Zustand** | State | Lightweight, simple global state for session data |

### Why Not:
- **Create React App:** Dead, no SSR
- **Vite + React:** Good but need separate backend
- **Vue/Svelte:** BZ's existing projects use React patterns

---

## Backend

| Technology | Purpose | Why |
|------------|---------|-----|
| **Next.js API Routes** | API endpoints | Colocated with frontend, serverless |
| **Vercel** | Hosting | Free tier generous, instant deploys |
| **Vercel Blob** | Image storage | Simple, cheap, integrated with Vercel |

### Why Not:
- **Separate Express/Node server:** Overkill for MVP
- **Supabase/Firebase:** Not needed until we add auth

---

## AI / Image Generation

| Technology | Purpose | Why |
|------------|---------|-----|
| **Flux Kontext Pro** | Primary image gen | Best identity preservation + editing quality (per research) |
| **fal.ai** | Flux API provider | Fast, reliable, good pricing |
| **Gemini 2.5 Flash** | Backup / analysis | Free tier, good for body analysis |

### Generation Pipeline
```
User Photo → Body Analysis → Transformation Prompt → Flux Kontext Pro → Result
     │              │                   │
     │              │                   └── Dynamic prompt based on:
     │              │                       • Time horizon
     │              │                       • Workout plan
     │              │                       • Focus areas
     │              │                       • Nutrition goal
     │              │
     │              └── Extract:
     │                  • Current body composition estimate
     │                  • Pose/angle
     │                  • Lighting conditions
     │
     └── Preprocessing:
         • Resize to optimal dimensions
         • Quality check
```

### Pricing Estimates (fal.ai Flux Kontext Pro)
- ~$0.04 per image
- 5 horizons × $0.04 = $0.20 per full generation
- 1000 users × $0.20 = $200/month at scale

---

## Physiology Engine (Calculation Layer)

| Approach | Implementation |
|----------|----------------|
| **Muscle growth models** | Research-based formulas (McDonald, Helms, etc.) |
| **Body recomposition** | Caloric balance + training stimulus calculations |
| **Genetic factors** | Modifier coefficients based on ethnicity/age/gender |
| **Diminishing returns** | Experience level affects rate of gains |

This lives as TypeScript utility functions — no external service needed.

### Key Calculations
```typescript
// Simplified example
function projectMuscleGain(params: PhysiqueParams): ProjectedChanges {
  const baseRate = getBaseGainRate(params.experienceLevel); // lbs/month
  const geneticModifier = getGeneticModifier(params.ethnicity, params.gender);
  const ageModifier = getAgeModifier(params.age);
  const trainingModifier = getTrainingModifier(params.workoutsPerWeek, params.split);
  const nutritionModifier = getNutritionModifier(params.nutritionGoal);
  const sleepModifier = getSleepModifier(params.sleepQuality);
  
  const monthlyGain = baseRate * geneticModifier * ageModifier * 
                      trainingModifier * nutritionModifier * sleepModifier;
  
  return {
    leanMassChange: monthlyGain * (params.horizonWeeks / 4),
    bodyFatChange: calculateFatChange(params),
    // Regional distribution based on focus areas
  };
}
```

---

## Development Tools

| Tool | Purpose |
|------|---------|
| **pnpm** | Package manager (fast, efficient) |
| **ESLint + Prettier** | Code quality |
| **Git** | Version control |
| **VS Code** | Editor (BZ's Mac) |

---

## Environment Variables

```bash
# .env.local
FAL_KEY=               # fal.ai API key for Flux
GOOGLE_AI_KEY=         # Gemini API (backup/analysis)
REPLICATE_API_TOKEN=   # Replicate (alternative models)

# Future (post-MVP)
DATABASE_URL=          # When we add persistence
CLERK_SECRET_KEY=      # When we add auth
```

---

## Infrastructure (MVP)

```
GitHub Repo
    │
    ▼
Vercel (auto-deploy on push)
    │
    ├── Frontend (Edge)
    ├── API Routes (Serverless Functions)
    └── Blob Storage (Generated Images)
```

### Costs (MVP)
- Vercel: Free tier (100GB bandwidth, 100hrs compute)
- fal.ai: Pay-per-use (~$0.04/image)
- Domain: ~$12/year (optional for MVP)

**Total MVP cost: ~$0 until meaningful usage**

---

## Future Considerations

| When | Addition |
|------|----------|
| Need auth | Add Clerk (5min integration with Next.js) |
| Need database | Add Supabase or PlanetScale |
| Need background jobs | Add Inngest or QStash |
| High traffic | Upgrade Vercel plan, add caching |
| Mobile apps | React Native or Expo (share logic) |
