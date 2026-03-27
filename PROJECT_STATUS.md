# PhysiqAI Project Status & Handoff

*Status as of 2026-02-03 17:34 UTC*

---

## Where You Left Off

### Current State
- ✅ **MVP Dashboard built** - Testing interface with image upload, calculations, generation
- ❌ **InstantID timeout issues** - Need to debug API calls
- ✅ **Comprehensive research completed** - Data sources, specialized models identified
- ✅ **Scientific foundation solid** - 15+ peer-reviewed sources integrated

### Last Testing Results
- **Problem 1:** Flux added tattoos that weren't in original (identity failure)
- **Problem 2:** Face completely changed between before/after
- **Problem 3:** Transformations too dramatic (looked like 3+ years not 6 months)
- **Solution attempted:** Switched to InstantID for better identity preservation

### Files on Your Mac

```
~/Documents/physiqai/
├── .env                           # API keys (FAL, Replicate, Google)
├── README.md                      # Project overview
├── 
├── docs/                          # All documentation
│   ├── PRD.md                     # Product requirements  
│   ├── APP_FLOW.md                # User journey
│   ├── TECH_STACK.md              # Technology choices
│   ├── FRONTEND_GUIDELINES.md     # React/Next.js patterns
│   ├── BACKEND_STRUCTURE.md       # API design
│   ├── IMPLEMENTATION_PLAN.md     # Build phases
│   ├── PHYSIOLOGY_SOURCES.md      # Research citations (912 lines)
│   ├── NUTRITION_RESEARCH.md      # Nutrition impact on gains
│   ├── VALIDATION_RESEARCH.md     # Market validation
│   ├── DEEP_BRAINSTORM.md         # Advanced techniques (24KB)
│   ├── IMAGE_GENERATION_DEEP_DIVE.md # Detailed prompt engineering
│   ├── OVERNIGHT_RESEARCH.md      # Advanced model research
│   └── TRAINING_DATA_SOURCES.md   # Dataset sourcing options
│   
├── dashboard/                     # Current testing interface
│   ├── server.js                  # Node.js backend with InstantID
│   ├── index.html                 # Dashboard UI
│   ├── package.json               # Dependencies
│   ├── logs/                      # Generation history, costs, bugs
│   └── tests/                     # Organized test inputs/outputs
│   
├── experimental/                  # Research prototypes
│   ├── quality_pipeline.py        # Automated quality assessment
│   └── smpl_predictor.py           # 3D body model integration
│   
└── research/                      # Historical research files
    ├── DEEP-RESEARCH.md
    ├── various test scripts
    └── sample outputs
```

---

## Technical State

### Current Architecture
- **Frontend:** HTML dashboard (temporary for testing)
- **Backend:** Node.js server with InstantID API
- **Model:** Replicate InstantID (identity preservation + body editing)
- **Calculations:** Science-based physiology engine with 15+ research citations

### API Keys Configured
- ✅ FAL_KEY (Flux Kontext Pro backup)
- ✅ REPLICATE_API_TOKEN (InstantID primary)
- ✅ GOOGLE_AI_KEY (body analysis)

### Known Issues
1. **InstantID timeout** - API calls failing after 120s
2. **Prompt optimization needed** - Balance detail vs model understanding
3. **Quality inconsistency** - Need automated quality checks

---

## Research Findings Summary

### Training Data Opportunities
- **r/progresspics:** 1.7M transformation posts (scrapeable)
- **Academic datasets:** SMPL, Human3.6M, AGORA for body modeling
- **Partnership targets:** MyFitnessPal, Strong app, gym chains
- **Budget:** $25K for POC, $100K for production dataset

### Model Options Identified
1. **InstantID** (current) - Zero-shot identity preservation
2. **SMPL + ControlNet** - 3D body model control
3. **Custom LoRA training** - Fitness-specific fine-tuning
4. **Multi-model pipeline** - Specialized models per task

### Competitive Intelligence
- **Gap identified:** No science-based transformation tools exist
- **Opportunity:** Be first with research-backed predictions
- **Differentiation:** Citations, confidence scores, realistic timelines

---

## Immediate Next Steps

### 1. Fix Dashboard (VSCode)
```bash
cd ~/Documents/physiqai/dashboard
npm install
npm start
```

### 2. Debug InstantID API
- Check Replicate API format
- Add proper error handling
- Test with minimal prompts first

### 3. Alternative Approaches
- Conservative Flux settings as backup
- Explore SMPL-based control
- Implement multi-model pipeline

### 4. Build Production App
- Next.js 14 setup (docs ready)
- Component architecture planned
- API endpoints designed

---

## Development Setup for VSCode

### Required Extensions
- TypeScript
- Prettier
- ESLint
- REST Client (for API testing)

### Folder Structure Ready
- All documentation in `docs/`
- Testing dashboard in `dashboard/`
- Future Next.js app goes in `src/`
- Experimental code in `experimental/`

---

## Key Insights from Research

1. **No fitness-specific transformation models exist** - We'd be first
2. **Identity preservation is the hardest challenge** - InstantID best current solution
3. **Training data is scarce but obtainable** - Reddit, partnerships, synthetic generation
4. **Scientific backing is our moat** - Competitors use fantasy, we use research

---

*Ready for local development in VSCode. All tools and documentation prepared.*