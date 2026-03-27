# PhysiqAI — Backend Structure

## Overview

MVP backend is minimal — Next.js API routes handling:
1. Body analysis (extract info from photo)
2. Transformation generation (call Flux API)

No database, no auth, no persistence beyond browser storage.

---

## API Routes

```
src/app/api/
├── analyze/
│   └── route.ts      # POST: Analyze uploaded photo
└── generate/
    └── route.ts      # POST: Generate transformation
```

---

## Endpoint Specifications

### POST `/api/analyze`

Analyzes user photo to extract body composition estimates.

**Request:**
```typescript
// multipart/form-data
{
  photo: File;  // User's uploaded photo
}
```

**Response:**
```typescript
{
  success: boolean;
  data?: {
    estimatedBodyFat: number;      // 5-50%
    bodyType: 'ectomorph' | 'mesomorph' | 'endomorph';
    poseQuality: 'good' | 'acceptable' | 'poor';
    lightingQuality: 'good' | 'acceptable' | 'poor';
    suggestions?: string[];        // ["Try better lighting", etc.]
  };
  error?: string;
}
```

**Implementation:**
```typescript
// src/app/api/analyze/route.ts
import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const photo = formData.get('photo') as File;
    
    if (!photo) {
      return NextResponse.json(
        { success: false, error: 'No photo provided' },
        { status: 400 }
      );
    }

    // Convert to base64 for API call
    const bytes = await photo.arrayBuffer();
    const base64 = Buffer.from(bytes).toString('base64');

    // Use Gemini for analysis (free tier)
    const analysis = await analyzeWithGemini(base64);

    return NextResponse.json({ success: true, data: analysis });
  } catch (error) {
    console.error('Analysis error:', error);
    return NextResponse.json(
      { success: false, error: 'Analysis failed' },
      { status: 500 }
    );
  }
}
```

---

### POST `/api/generate`

Generates transformation image(s) for specified horizons.

**Request:**
```typescript
{
  photo: string;           // base64 encoded image
  demographics: {
    age: number;
    gender: 'male' | 'female' | 'other';
    ethnicity: string;
  };
  physique: {
    heightCm: number;
    weightKg: number;
    bodyFatPercent: number;
    experienceLevel: 'beginner' | 'intermediate' | 'advanced';
  };
  plan: {
    split: string;
    focusAreas: string[];
    workoutsPerWeek: number;
    cardioPerWeek: number;
    sleepQuality: 'poor' | 'average' | 'good';
    nutritionGoal: 'cut' | 'maintain' | 'bulk';
  };
  horizonWeeks: number;    // Single horizon per request
}
```

**Response:**
```typescript
{
  success: boolean;
  data?: {
    imageUrl: string;              // Generated image URL
    projections: {
      leanMassChangeKg: number;
      bodyFatChangePercent: number;
      estimatedNewWeight: number;
    };
    confidence: 'high' | 'medium' | 'low';
  };
  error?: string;
}
```

**Implementation:**
```typescript
// src/app/api/generate/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { calculateProjections } from '@/lib/physiology';
import { generateWithFlux } from '@/lib/flux';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    
    // Validate input
    const validated = generateRequestSchema.parse(body);

    // 1. Calculate physiological projections
    const projections = calculateProjections({
      ...validated.demographics,
      ...validated.physique,
      ...validated.plan,
      horizonWeeks: validated.horizonWeeks,
    });

    // 2. Build transformation prompt
    const prompt = buildTransformationPrompt(validated, projections);

    // 3. Generate with Flux Kontext Pro
    const imageUrl = await generateWithFlux(validated.photo, prompt);

    return NextResponse.json({
      success: true,
      data: {
        imageUrl,
        projections,
        confidence: calculateConfidence(validated),
      },
    });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { success: false, error: 'Invalid input', details: error.errors },
        { status: 400 }
      );
    }
    console.error('Generation error:', error);
    return NextResponse.json(
      { success: false, error: 'Generation failed' },
      { status: 500 }
    );
  }
}
```

---

## External API Integrations

### fal.ai (Flux Kontext Pro)

```typescript
// src/lib/flux.ts
import * as fal from '@fal-ai/serverless-client';

fal.config({
  credentials: process.env.FAL_KEY,
});

export async function generateWithFlux(
  sourceImage: string,
  prompt: string
): Promise<string> {
  const result = await fal.subscribe('fal-ai/flux-kontext-pro', {
    input: {
      image: `data:image/jpeg;base64,${sourceImage}`,
      prompt,
      guidance_scale: 7.5,
      num_inference_steps: 28,
      output_format: 'jpeg',
    },
    logs: true,
    onQueueUpdate: (update) => {
      if (update.status === 'IN_PROGRESS') {
        console.log('Generation progress:', update.logs);
      }
    },
  });

  return result.images[0].url;
}
```

### Gemini (Analysis)

```typescript
// src/lib/gemini.ts
const GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent';

export async function analyzeWithGemini(imageBase64: string) {
  const response = await fetch(`${GEMINI_API_URL}?key=${process.env.GOOGLE_AI_KEY}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      contents: [{
        parts: [
          {
            text: `Analyze this fitness photo. Estimate:
            1. Body fat percentage (number between 5-50)
            2. Body type (ectomorph/mesomorph/endomorph)
            3. Pose quality for transformation (good/acceptable/poor)
            4. Lighting quality (good/acceptable/poor)
            
            Respond in JSON format only.`
          },
          {
            inline_data: {
              mime_type: 'image/jpeg',
              data: imageBase64,
            },
          },
        ],
      }],
    }),
  });

  const data = await response.json();
  return JSON.parse(data.candidates[0].content.parts[0].text);
}
```

---

## Physiology Engine

```typescript
// src/lib/physiology.ts

interface ProjectionParams {
  age: number;
  gender: 'male' | 'female' | 'other';
  ethnicity: string;
  heightCm: number;
  weightKg: number;
  bodyFatPercent: number;
  experienceLevel: 'beginner' | 'intermediate' | 'advanced';
  workoutsPerWeek: number;
  cardioPerWeek: number;
  sleepQuality: 'poor' | 'average' | 'good';
  nutritionGoal: 'cut' | 'maintain' | 'bulk';
  focusAreas: string[];
  horizonWeeks: number;
}

interface Projections {
  leanMassChangeKg: number;
  bodyFatChangePercent: number;
  estimatedNewWeight: number;
  regionalChanges: Record<string, number>;  // e.g., { arms: 1.2, chest: 0.8 }
}

// Base monthly muscle gain rates (kg) by experience level
// Source: McDonald, Helms, et al. research
const BASE_GAIN_RATES = {
  beginner: 0.9,      // ~2 lbs/month
  intermediate: 0.45,  // ~1 lb/month
  advanced: 0.22,      // ~0.5 lbs/month
};

// Gender modifier
const GENDER_MODIFIERS = {
  male: 1.0,
  female: 0.5,  // Women gain muscle ~50% rate of men
  other: 0.75,
};

// Age modifier (peak at 20-25, decline after)
function getAgeModifier(age: number): number {
  if (age < 20) return 0.9;
  if (age <= 25) return 1.0;
  if (age <= 35) return 0.95;
  if (age <= 45) return 0.85;
  if (age <= 55) return 0.75;
  return 0.6;
}

// Training frequency modifier
function getTrainingModifier(workoutsPerWeek: number): number {
  // Diminishing returns after 4-5 days
  if (workoutsPerWeek <= 2) return 0.6;
  if (workoutsPerWeek === 3) return 0.8;
  if (workoutsPerWeek === 4) return 0.95;
  if (workoutsPerWeek === 5) return 1.0;
  return 1.0; // 6-7 doesn't help more (recovery limited)
}

// Sleep modifier
const SLEEP_MODIFIERS = {
  poor: 0.7,
  average: 0.9,
  good: 1.0,
};

// Nutrition modifier
const NUTRITION_MODIFIERS = {
  cut: 0.3,      // Hard to gain muscle in deficit
  maintain: 0.7,
  bulk: 1.0,
};

export function calculateProjections(params: ProjectionParams): Projections {
  const {
    age, gender, experienceLevel, workoutsPerWeek,
    sleepQuality, nutritionGoal, bodyFatPercent, weightKg,
    focusAreas, horizonWeeks,
  } = params;

  // Calculate monthly lean mass gain
  const baseRate = BASE_GAIN_RATES[experienceLevel];
  const monthlyGain = baseRate
    * GENDER_MODIFIERS[gender]
    * getAgeModifier(age)
    * getTrainingModifier(workoutsPerWeek)
    * SLEEP_MODIFIERS[sleepQuality]
    * NUTRITION_MODIFIERS[nutritionGoal];

  const months = horizonWeeks / 4;
  const leanMassChangeKg = monthlyGain * months;

  // Body fat change depends on nutrition goal
  let bodyFatChangePercent = 0;
  if (nutritionGoal === 'cut') {
    // Lose ~0.5-1% body fat per week if aggressive
    bodyFatChangePercent = -0.5 * (horizonWeeks / 4);
  } else if (nutritionGoal === 'bulk') {
    // Might gain slight fat while bulking
    bodyFatChangePercent = 0.2 * (horizonWeeks / 4);
  }

  // Regional distribution based on focus areas
  const regionalChanges: Record<string, number> = {};
  const baseRegionalGain = leanMassChangeKg / focusAreas.length;
  
  for (const area of focusAreas) {
    // Focused areas get more development
    regionalChanges[area] = baseRegionalGain * 1.3;
  }

  // Estimate new weight
  const currentLeanMass = weightKg * (1 - bodyFatPercent / 100);
  const newLeanMass = currentLeanMass + leanMassChangeKg;
  const newBodyFatPercent = bodyFatPercent + bodyFatChangePercent;
  const estimatedNewWeight = newLeanMass / (1 - newBodyFatPercent / 100);

  return {
    leanMassChangeKg: Math.round(leanMassChangeKg * 10) / 10,
    bodyFatChangePercent: Math.round(bodyFatChangePercent * 10) / 10,
    estimatedNewWeight: Math.round(estimatedNewWeight * 10) / 10,
    regionalChanges,
  };
}
```

---

## Prompt Engineering

```typescript
// src/lib/prompts.ts

export function buildTransformationPrompt(
  input: GenerateRequest,
  projections: Projections
): string {
  const { demographics, physique, plan, horizonWeeks } = input;
  
  const timeDescription = horizonWeeks <= 12 
    ? `${horizonWeeks} weeks` 
    : `${Math.round(horizonWeeks / 4)} months`;

  const changeDescription = buildChangeDescription(projections, plan.focusAreas);
  
  return `Transform this person's physique to show realistic ${timeDescription} of consistent training progress.

Changes to apply:
${changeDescription}

Important constraints:
- Maintain exact same face, skin tone, and identity
- Keep the same pose, angle, and lighting
- Changes must be subtle and realistic, not dramatic
- Focus muscle development on: ${plan.focusAreas.join(', ')}
- ${plan.nutritionGoal === 'cut' ? 'Show more muscle definition and vascularity' : ''}
- ${plan.nutritionGoal === 'bulk' ? 'Show fuller muscles with slightly less definition' : ''}

The result should look like a realistic "after" photo, not an idealized fantasy.`;
}

function buildChangeDescription(
  projections: Projections,
  focusAreas: string[]
): string {
  const lines = [];
  
  if (projections.leanMassChangeKg > 0) {
    lines.push(`- Add approximately ${projections.leanMassChangeKg}kg of lean muscle`);
  }
  
  if (projections.bodyFatChangePercent < 0) {
    lines.push(`- Reduce body fat by approximately ${Math.abs(projections.bodyFatChangePercent)}%`);
    lines.push(`- Increase muscle definition and vascularity`);
  }

  for (const area of focusAreas) {
    const growth = projections.regionalChanges[area];
    if (growth) {
      lines.push(`- Emphasize ${area} development (${Math.round(growth * 100) / 100}kg growth)`);
    }
  }

  return lines.join('\n');
}
```

---

## Error Handling

```typescript
// src/lib/errors.ts

export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode: number = 500,
    public code?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export class RateLimitError extends ApiError {
  constructor() {
    super('Rate limit exceeded. Please try again later.', 429, 'RATE_LIMIT');
  }
}

export class GenerationError extends ApiError {
  constructor(message: string = 'Image generation failed') {
    super(message, 500, 'GENERATION_FAILED');
  }
}
```

---

## Future: Database Schema (Post-MVP)

When we add persistence:

```sql
-- Users (via Clerk, just store reference)
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clerk_id TEXT UNIQUE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Transformations
CREATE TABLE transformations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  source_image_url TEXT NOT NULL,
  generated_image_url TEXT NOT NULL,
  input_data JSONB NOT NULL,
  projections JSONB NOT NULL,
  horizon_weeks INTEGER NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Workout logs (for deflation mechanic)
CREATE TABLE workout_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  logged_at TIMESTAMPTZ DEFAULT NOW(),
  workout_type TEXT,
  duration_minutes INTEGER,
  notes TEXT
);
```
