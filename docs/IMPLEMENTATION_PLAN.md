# PhysiqAI — Implementation Plan

## Overview

Build order optimized for fastest path to testable prototype.

**Total estimated time:** 8-12 hours of focused work

---

## Phase 0: Project Setup (30 min)

### Tasks
- [ ] Initialize Next.js 14 project with TypeScript
- [ ] Install dependencies (Tailwind, shadcn/ui, zustand, zod, fal-ai)
- [ ] Set up folder structure per FRONTEND_GUIDELINES.md
- [ ] Configure environment variables
- [ ] Verify fal.ai API key works

### Commands
```bash
npx create-next-app@latest physiqai --typescript --tailwind --eslint --app --src-dir
cd physiqai
pnpm add zustand zod @fal-ai/serverless-client
pnpm add -D @types/node
npx shadcn-ui@latest init
```

### Deliverable
- Running Next.js app at localhost:3000
- All env vars configured

---

## Phase 1: Core UI Shell (2 hours)

### Tasks
- [ ] Create layout with step indicator
- [ ] Build landing page with CTA
- [ ] Create all 6 route pages (empty shells)
- [ ] Add navigation between steps
- [ ] Set up Zustand store with types
- [ ] Implement sessionStorage persistence

### Deliverable
- Complete navigation flow (can click through all steps)
- Store persists across page refreshes

---

## Phase 2: Input Forms (2-3 hours)

### Tasks
- [ ] **Photo Upload** (`/transform/photo`)
  - [ ] Drag & drop zone
  - [ ] File validation (size, type)
  - [ ] Preview with remove option
  - [ ] Guidance text

- [ ] **Basic Info** (`/transform/info`)
  - [ ] Age input (number)
  - [ ] Gender select
  - [ ] Ethnicity select
  - [ ] Height input (with unit toggle)
  - [ ] Weight input (with unit toggle)
  - [ ] Body fat slider OR "auto detect" checkbox
  - [ ] Experience level select

- [ ] **Workout Plan** (`/transform/plan`)
  - [ ] Split select (PPL, Bro, etc.)
  - [ ] Focus areas multi-select chips
  - [ ] Workout frequency slider
  - [ ] Cardio frequency slider
  - [ ] Sleep quality select
  - [ ] Nutrition goal select

- [ ] **Time Horizons** (`/transform/timeline`)
  - [ ] Chip multi-select for horizons
  - [ ] At least 1 required validation

### Deliverable
- All forms functional
- Data flows to Zustand store
- Validation prevents proceeding with incomplete data

---

## Phase 3: Physiology Engine (1-2 hours)

### Tasks
- [ ] Implement `calculateProjections()` function
- [ ] Add all modifier functions (age, training, sleep, etc.)
- [ ] Build regional distribution logic
- [ ] Write unit tests for edge cases
- [ ] Add confidence score calculation

### Deliverable
- Given inputs, returns realistic projections
- Handles edge cases (very high/low body fat, etc.)

---

## Phase 4: Generation Pipeline (2-3 hours)

### Tasks
- [ ] **Analysis endpoint** (`/api/analyze`)
  - [ ] Accept photo upload
  - [ ] Call Gemini for body analysis
  - [ ] Return structured data

- [ ] **Generation endpoint** (`/api/generate`)
  - [ ] Accept all inputs + photo
  - [ ] Call physiology engine
  - [ ] Build transformation prompt
  - [ ] Call fal.ai Flux Kontext Pro
  - [ ] Return generated image URL

- [ ] **Prompt engineering**
  - [ ] Create base prompt template
  - [ ] Add dynamic sections based on inputs
  - [ ] Test and iterate on quality

### Deliverable
- Can call `/api/generate` with test data
- Returns transformed image

---

## Phase 5: Results Page (1-2 hours)

### Tasks
- [ ] Side-by-side image comparison component
- [ ] Tab/toggle for multiple horizons
- [ ] Projection summary card
- [ ] Loading state with progress messages
- [ ] Error state with retry option
- [ ] "Try Different Plan" and "Start Over" buttons

### Deliverable
- Full end-to-end flow works
- User can see transformed image

---

## Phase 6: Polish & Testing (1-2 hours)

### Tasks
- [ ] Mobile responsiveness pass
- [ ] Loading state refinements
- [ ] Error handling for all edge cases
- [ ] Manual QA of full flow
- [ ] Performance check (Lighthouse)
- [ ] Fix any obvious bugs

### Deliverable
- Production-ready MVP
- Works well on mobile

---

## Deployment

### Vercel Setup
```bash
# Install Vercel CLI
pnpm add -g vercel

# Deploy
vercel

# Set environment variables in Vercel dashboard
# FAL_KEY, GOOGLE_AI_KEY
```

### Post-Deploy Checklist
- [ ] Verify all env vars are set
- [ ] Test full flow on production URL
- [ ] Check error logging (Vercel logs)

---

## File Checklist

After implementation, these files should exist:

```
physiqai/
├── src/
│   ├── app/
│   │   ├── page.tsx                    # Landing
│   │   ├── layout.tsx                  # Root layout
│   │   ├── transform/
│   │   │   ├── layout.tsx              # Transform flow layout
│   │   │   ├── photo/page.tsx
│   │   │   ├── info/page.tsx
│   │   │   ├── plan/page.tsx
│   │   │   ├── timeline/page.tsx
│   │   │   ├── loading/page.tsx
│   │   │   └── results/page.tsx
│   │   └── api/
│   │       ├── analyze/route.ts
│   │       └── generate/route.ts
│   ├── components/
│   │   ├── ui/                         # shadcn components
│   │   ├── transform/
│   │   │   ├── photo-upload.tsx
│   │   │   ├── step-indicator.tsx
│   │   │   ├── info-form.tsx
│   │   │   ├── plan-form.tsx
│   │   │   ├── horizon-select.tsx
│   │   │   ├── loading-state.tsx
│   │   │   └── result-comparison.tsx
│   │   └── layout/
│   │       └── header.tsx
│   ├── lib/
│   │   ├── store.ts                    # Zustand
│   │   ├── schemas.ts                  # Zod
│   │   ├── physiology.ts               # Calculations
│   │   ├── flux.ts                     # fal.ai integration
│   │   ├── gemini.ts                   # Analysis
│   │   ├── prompts.ts                  # Prompt building
│   │   └── utils.ts
│   └── styles/
│       └── globals.css
├── .env.local                          # API keys
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.js
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Flux output quality varies | Iterate on prompts, add quality checks |
| Generation too slow | Show progress, add timeout handling |
| Photo poses vary widely | Add pose guidance, handle gracefully |
| Body fat estimation inaccurate | Allow manual override, show confidence |

---

## Success Criteria

MVP is complete when:
1. ✅ User can upload photo and fill all inputs
2. ✅ System generates realistic transformation image
3. ✅ Multiple time horizons work
4. ✅ Works on mobile
5. ✅ No critical bugs in happy path
6. ✅ Generation completes in < 60 seconds
