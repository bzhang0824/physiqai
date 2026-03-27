# PhysiqAI Founder Dashboard

A testing and debugging interface for the founder to see everything happening under the hood.

## Quick Start

```bash
cd dashboard
npm start
```

Then open: http://localhost:3456

## What You'll See

### 1. Upload Test Image
Drop or select any fitness/body photo

### 2. Profile Settings
- Age, gender, weight
- Body fat %
- Experience level (beginner/intermediate/advanced)
- Workout frequency
- Sleep quality
- Nutrition goal (cut/maintain/bulk)
- Focus areas (multi-select)
- Time horizon (4wk to 1yr)

### 3. Generate Transformation
Click button → wait 25-40 seconds → see result

### 4. Debug Information (RIGHT PANEL)

**Projection Calculations:**
- Step-by-step breakdown of how we calculated muscle gain
- Each step shows the formula AND the research source (with PMID)

**Prompt Used:**
- The exact prompt sent to the AI model
- Full text, nothing hidden

**Generation Stats:**
- Time taken (seconds)
- Cost ($ per generation)
- Model used
- Confidence score

**Bug Reporting:**
- Describe what went wrong
- System captures context automatically

**Generation History:**
- Last 5 generations with thumbnails

---

## How It Works (Step by Step)

### Step 1: Image Upload
```
User drops image
    ↓
Browser converts to base64
    ↓
Image stored in memory (not uploaded until generate)
```

### Step 2: Profile Collection
```
User fills form
    ↓
All values collected into profile object
    ↓
Focus areas from multi-select chips
```

### Step 3: Generate Button Clicked
```
POST /api/generate
    ↓
Server receives: { image, profile, horizonWeeks }
```

### Step 4: Projection Calculation
```
profile → calculateProjections()
    ↓
Step 1: Base rate from Aragon/Helms model
        - Beginner: 1.25% bodyweight/month
        - Intermediate: 0.75%
        - Advanced: 0.375%
    ↓
Step 2: Apply gender modifier (Roberts 2020)
        - Male: 1.0x
        - Female: 0.5x
    ↓
Step 3: Apply age modifier (Feldman 2002)
        - Under 30: 1.0x
        - Each year over 30: -1%
    ↓
Step 4: Apply sleep modifier (Lamon 2021)
        - Good: 1.0x
        - Average: 0.91x
        - Poor: 0.82x (18% reduction)
    ↓
Step 5: Apply frequency modifier (Schoenfeld 2016)
        - 4+ days: 1.0x
        - 3 days: 0.95x
        - 2 days: 0.85x
    ↓
Step 6: Apply nutrition modifier
        - Bulk: 1.0x
        - Maintain: 0.7x
        - Cut: 0.3x
    ↓
Step 7: Calculate final projection
        base × all_modifiers × months = total_gain
```

### Step 5: Prompt Generation
```
projections → buildPrompt()
    ↓
Template filled with:
    - Time description ("12 weeks")
    - Muscle gain amount ("5.4 lbs")
    - Focus areas ("chest, arms")
    - Nutrition-specific instructions
    - Identity preservation constraints
```

### Step 6: Image Generation
```
prompt + image → fal.ai API
    ↓
Submit to queue → get request_id
    ↓
Poll every 2 seconds for completion
    ↓
Receive generated image URL
    ↓
~25-40 seconds total
```

### Step 7: Logging
```
All data saved to ./logs/
    ↓
generations.json: Full generation records
costs.json: Running cost total
bugs.json: Reported bugs
YYYY-MM-DD.log: Daily activity log
```

### Step 8: Display Results
```
Server returns full result object
    ↓
Browser displays:
    - Side-by-side images
    - Calculation steps with sources
    - Full prompt
    - Stats (time, cost, confidence)
```

---

## File Structure

```
dashboard/
├── server.js          # Node.js backend
├── index.html         # Frontend dashboard
├── package.json       # Dependencies
├── README.md          # This file
└── logs/              # All logs stored here
    ├── generations.json
    ├── costs.json
    ├── bugs.json
    └── YYYY-MM-DD.log
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | / | Serve dashboard HTML |
| GET | /api/health | Check server status + API keys |
| GET | /api/logs | Get all generations, costs, bugs |
| POST | /api/generate | Run transformation |
| POST | /api/bugs | Report a bug |

---

## Bug Workflow

When you report a bug:

1. Bug saved to `logs/bugs.json`
2. Bug gets ID like `BUG-1234567890`
3. Status set to "open"
4. Context captured (last generation, profile, etc.)

**Next step (per BZ's instructions):**
- Don't fix immediately
- Write a test that reproduces the bug
- Have sub-agent fix and prove with passing test

---

## Costs

| Model | Cost |
|-------|------|
| fal.ai Flux Kontext Pro | ~$0.04/image |

Dashboard tracks total cost in `logs/costs.json`

---

## Environment Variables

Required in `../.env`:
```
FAL_KEY=your_fal_ai_key
GOOGLE_AI_KEY=your_google_key
```

---

## Troubleshooting

**Server won't start:**
- Check if port 3456 is in use
- Verify `.env` file exists with API keys

**Generation fails:**
- Check FAL_KEY is valid
- Look at logs for error details

**Image doesn't change:**
- Try different prompt settings
- Check if image is clear enough

---

*Last updated: 2026-02-03*
