# PhysiqAI — Frontend Guidelines

## Design Principles

1. **Mobile-first responsive** — Design for phone, scale up
2. **Dark mode default** — Fitness apps look better dark
3. **Minimal friction** — Every unnecessary click loses users
4. **Progress visibility** — Always show where user is in the flow
5. **Trust signals** — "Science-based", "Personalized", "Your data stays private"

---

## Component Architecture

```
src/
├── app/                    # Next.js App Router
│   ├── page.tsx           # Landing page
│   ├── transform/
│   │   ├── layout.tsx     # Shared transform flow layout
│   │   ├── photo/page.tsx
│   │   ├── info/page.tsx
│   │   ├── plan/page.tsx
│   │   ├── timeline/page.tsx
│   │   ├── loading/page.tsx
│   │   └── results/page.tsx
│   └── api/
│       ├── analyze/route.ts    # Body analysis endpoint
│       └── generate/route.ts   # Transformation generation
│
├── components/
│   ├── ui/                # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── select.tsx
│   │   ├── slider.tsx
│   │   ├── card.tsx
│   │   └── ...
│   │
│   ├── transform/         # Feature-specific components
│   │   ├── photo-upload.tsx
│   │   ├── step-indicator.tsx
│   │   ├── info-form.tsx
│   │   ├── plan-form.tsx
│   │   ├── horizon-select.tsx
│   │   ├── loading-state.tsx
│   │   └── result-comparison.tsx
│   │
│   └── layout/
│       ├── header.tsx
│       └── footer.tsx
│
├── lib/
│   ├── store.ts           # Zustand store
│   ├── schemas.ts         # Zod validation schemas
│   ├── physiology.ts      # Calculation functions
│   └── utils.ts           # Helpers
│
├── hooks/
│   ├── use-transform-session.ts
│   └── use-generation.ts
│
└── styles/
    └── globals.css        # Tailwind + custom vars
```

---

## Styling Guidelines

### Colors (Dark Theme)
```css
:root {
  --background: 0 0% 7%;        /* Near black */
  --foreground: 0 0% 98%;       /* Off white */
  --card: 0 0% 10%;             /* Slightly lighter */
  --primary: 142 76% 46%;       /* Green (growth/health) */
  --primary-foreground: 0 0% 100%;
  --secondary: 217 91% 60%;     /* Blue (trust) */
  --accent: 38 92% 50%;         /* Gold (achievement) */
  --muted: 0 0% 40%;
  --destructive: 0 84% 60%;     /* Red (errors) */
}
```

### Typography
```css
/* Use system fonts for speed, or add Inter */
--font-sans: 'Inter', system-ui, sans-serif;
--font-mono: 'JetBrains Mono', monospace;

/* Scale */
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */
--text-3xl: 1.875rem;  /* 30px */
```

### Spacing
Use Tailwind's default scale: `p-4` = 1rem, `p-8` = 2rem, etc.

---

## Component Patterns

### Form Steps
```tsx
// Each step follows this pattern
export default function StepPage() {
  const { data, setData, canProceed } = useTransformSession();
  const router = useRouter();

  const handleContinue = () => {
    if (canProceed) {
      router.push('/transform/next-step');
    }
  };

  return (
    <div className="flex flex-col min-h-screen">
      <StepIndicator current={2} total={5} />
      
      <main className="flex-1 p-4 max-w-md mx-auto">
        {/* Step content */}
      </main>

      <footer className="p-4 border-t">
        <Button 
          onClick={handleContinue} 
          disabled={!canProceed}
          className="w-full"
        >
          Continue
        </Button>
      </footer>
    </div>
  );
}
```

### Photo Upload
```tsx
// Drag & drop + click to upload
<PhotoUpload
  onUpload={(file) => setPhoto(file)}
  preview={photoPreview}
  maxSizeMb={10}
  acceptedTypes={['image/jpeg', 'image/png', 'image/webp']}
  guidance="Front-facing, arms slightly away from body, good lighting"
/>
```

### Multi-Select Chips
```tsx
// For focus areas
<ChipSelect
  options={[
    { value: 'chest', label: 'Chest' },
    { value: 'back', label: 'Back' },
    { value: 'arms', label: 'Arms' },
    // ...
  ]}
  selected={focusAreas}
  onChange={setFocusAreas}
  max={5}
/>
```

---

## State Management

### Zustand Store
```typescript
// lib/store.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface TransformStore {
  // Photo
  photoFile: File | null;
  photoPreview: string | null;
  setPhoto: (file: File) => void;

  // Demographics
  age: number | null;
  gender: 'male' | 'female' | 'other' | null;
  ethnicity: string | null;
  setDemographics: (data: Partial<Demographics>) => void;

  // Physique
  heightCm: number | null;
  weightKg: number | null;
  bodyFatPercent: number | 'auto' | null;
  experienceLevel: ExperienceLevel | null;
  setPhysique: (data: Partial<Physique>) => void;

  // Plan
  split: WorkoutSplit | null;
  focusAreas: string[];
  workoutsPerWeek: number;
  cardioPerWeek: number;
  sleepQuality: SleepQuality | null;
  nutritionGoal: NutritionGoal | null;
  setPlan: (data: Partial<Plan>) => void;

  // Horizons
  selectedHorizons: number[];
  toggleHorizon: (weeks: number) => void;

  // Results
  results: Record<number, GenerationResult>;
  setResult: (weeks: number, result: GenerationResult) => void;

  // Actions
  reset: () => void;
}

export const useTransformStore = create<TransformStore>()(
  persist(
    (set) => ({
      // ... implementation
    }),
    {
      name: 'physiqai-transform',
      partialize: (state) => ({
        // Don't persist File objects
        age: state.age,
        gender: state.gender,
        // ... other serializable fields
      }),
    }
  )
);
```

---

## Validation

### Zod Schemas
```typescript
// lib/schemas.ts
import { z } from 'zod';

export const demographicsSchema = z.object({
  age: z.number().min(13).max(100),
  gender: z.enum(['male', 'female', 'other']),
  ethnicity: z.string().min(1),
});

export const physiqueSchema = z.object({
  heightCm: z.number().min(100).max(250),
  weightKg: z.number().min(30).max(300),
  bodyFatPercent: z.union([
    z.number().min(3).max(50),
    z.literal('auto'),
  ]),
  experienceLevel: z.enum(['beginner', 'intermediate', 'advanced']),
});

export const planSchema = z.object({
  split: z.enum(['ppl', 'bro', 'upper-lower', 'full-body', 'custom']),
  focusAreas: z.array(z.string()).min(1).max(5),
  workoutsPerWeek: z.number().min(1).max(7),
  cardioPerWeek: z.number().min(0).max(7),
  sleepQuality: z.enum(['poor', 'average', 'good']),
  nutritionGoal: z.enum(['cut', 'maintain', 'bulk']),
});
```

---

## Accessibility

- All interactive elements must be keyboard accessible
- Use semantic HTML (`<button>`, `<form>`, `<label>`)
- Provide `aria-label` for icon-only buttons
- Ensure sufficient color contrast (4.5:1 minimum)
- Support reduced motion preferences

---

## Performance

- Use `next/image` for all images (automatic optimization)
- Lazy load below-the-fold content
- Prefetch next step in flow: `<Link prefetch>`
- Keep bundle size minimal — no heavy libraries
- Use Suspense boundaries for loading states

---

## Error Handling

```tsx
// Wrap async operations
try {
  const result = await generateTransformation(data);
  setResult(result);
} catch (error) {
  if (error instanceof ApiError) {
    toast.error(error.message);
  } else {
    toast.error('Something went wrong. Please try again.');
    console.error(error);
  }
}
```

---

## Testing (Post-MVP)

- **Unit:** Vitest for utility functions
- **Component:** React Testing Library
- **E2E:** Playwright for critical flows
