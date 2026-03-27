# PhysiqAI MVP Execution Plan - Option 2 (2.5D Avatar)

**Budget:** $1,000
**Timeline:** 6 weeks (42 days)
**Goal:** Working 2.5D morphing avatar MVP with 10 beta users

---

## 🎯 Project Overview

### What We're Building
1. **Photo Upload & Analysis** - AI extracts body measurements from photos
2. **2.5D Avatar Generator** - Creates interactive pseudo-3D avatar
3. **Workout Logger** - Track exercises, nutrition, progress
4. **Daily Morphing Engine** - Avatar updates every morning based on science
5. **Progress Tracking** - Before/after comparison, timeline view

### Success Metrics
- [ ] 10 beta users signed up
- [ ] 70%+ daily active usage (users check daily)
- [ ] Avg session time >2 minutes
- [ ] 5+ user testimonials

---

## 📋 Tools & Resources Needed

### APIs & Services (Set up Week 1)
| Service | Purpose | Cost | Login Required |
|---------|---------|------|----------------|
| **Google Gemini 2.5 Flash** | Body analysis from photos | ~$10/mo | ✅ BZ has key |
| **Replicate** | Backup image processing | ~$20/mo | ✅ BZ has key |
| **Vercel** | Frontend hosting | Free | Need signup |
| **Supabase** | Database + Auth | Free | Need signup |
| **Cloudflare R2** | Image storage | ~$5/mo | Need signup |
| **Posthog** | Analytics | Free | Need signup |

**Total monthly cost:** ~$35/mo

### Development Tools
- **VSCode** - Already have
- **GitHub** - Version control & backups
- **Cursor/Claude Code** - AI coding assistant (you already use this)
- **Postman** - API testing

### Data Collection
- **PRAW** (Reddit API) - Python library, free
- **Reddit account** - For API access (you have this)
- **Storage** - Local storage on Mac for scraped data

---

## 📊 Project Tracking System

### Daily Tracking
**Location:** `~/Documents/physiqai/DAILY_LOG.md`

**Format:**
```markdown
## 2026-02-12 - Day 1
**Status:** ✅ On track / ⚠️ Delayed / 🔴 Blocked
**Hours:** 4h
**Completed:**
- [ ] Task 1
- [ ] Task 2
**Blockers:** None
**Tomorrow:** Task 3, Task 4
```

### Weekly Review
**Location:** `~/Documents/physiqai/WEEKLY_PROGRESS.md`

**Format:**
```markdown
## Week 1 - Data Collection
**Milestone:** ✅/❌ Collected 500 transformations
**Deliverable:** Dataset with before/after pairs
**Hours:** 20h / 20h planned
**Issues:** List any problems
**Next Week:** Focus areas
```

### File Organization
```
~/Documents/physiqai/
├── EXECUTION_PLAN.md          # This file (master plan)
├── DAILY_LOG.md              # Daily progress tracking
├── WEEKLY_PROGRESS.md        # Weekly milestone tracking
├── SPRINT_BOARD.md           # Current week's tasks (Kanban style)
├── data/
│   ├── reddit_scrapes/       # Raw scraped data
│   ├── processed/            # Cleaned transformation pairs
│   └── metadata.json         # Dataset statistics
├── src/                      # Next.js app code
├── scripts/                  # Data collection scripts
└── docs/                     # All planning docs
```

---

## 🗓️ WEEK 1: Data Collection & Foundation

**Milestone:** 500 verified transformation pairs + project setup
**Deliverable:** Working scraper + cleaned dataset + GitHub repo

### Monday, Feb 12 (Day 1) - 4 hours
**Goal:** Reddit scraper prototype working

- [ ] **9:00 AM** - Set up project structure on Mac
  - Create folder structure above
  - Initialize Git repo
  - Create DAILY_LOG.md and SPRINT_BOARD.md
  
- [ ] **10:00 AM** - Reddit API setup
  - Install PRAW: `pip install praw`
  - Create Reddit app at https://www.reddit.com/prefs/apps
  - Get API credentials (client_id, client_secret)
  - Test connection with simple script
  
- [ ] **11:00 AM** - Build basic scraper (v1)
  - Script: `scripts/scrape_progresspics.py`
  - Features: Pull top 100 posts from r/progresspics
  - Save: Post title, image URLs, submission text
  - Output: JSON file with metadata
  
- [ ] **12:00 PM** - Test & validate
  - Run scraper on 10 posts
  - Verify images download correctly
  - Check data quality

**End of Day:** Scraper pulls 10 posts successfully

---

### Tuesday, Feb 13 (Day 2) - 5 hours
**Goal:** Enhanced scraper with filtering + 100 posts collected

- [ ] **9:00 AM** - Improve scraper with filters
  - Filter: Only posts with "M" or "F" in title (gender)
  - Filter: Only posts with before/after images
  - Filter: Only posts with timeline mentioned (e.g., "6 months")
  - Add: Image download to `data/reddit_scrapes/images/`
  
- [ ] **11:00 AM** - Metadata extraction
  - Parse titles for: Age, gender, height, weight (before/after), timeline
  - Example: "M/25/6'0" [210lbs > 180lbs = 30lbs] (6 months)"
  - Create structured JSON output
  
- [ ] **1:00 PM** - Batch collection
  - Run scraper for top 1000 posts
  - Let it run in background (2-3 hours)
  
- [ ] **3:00 PM** - Quality check
  - Review 20 random samples
  - Document common issues
  - Calculate success rate (% with good data)

**End of Day:** 100-200 posts collected with metadata

---

### Wednesday, Feb 14 (Day 3) - 5 hours
**Goal:** 500 total posts + data cleaning pipeline

- [ ] **9:00 AM** - Continue scraping
  - Expand to more subreddits: r/Brogress, r/fitness, r/loseit
  - Run parallel scrapers
  
- [ ] **11:00 AM** - Build data cleaning script
  - Script: `scripts/clean_dataset.py`
  - Remove: Duplicate posts, broken images, missing metadata
  - Validate: Image dimensions, file sizes
  - Standardize: Units (lbs to kg, inches to cm)
  
- [ ] **1:00 PM** - Manual review & labeling
  - Create: `data/processed/verified_transformations.json`
  - Label quality: 1-5 stars (lighting, pose, clarity)
  - Note: Workout type mentioned (if any)
  
- [ ] **3:00 PM** - Dataset statistics
  - Count: Total transformations by timeline (3mo, 6mo, 1yr, 2yr)
  - Breakdown: Male vs female, age ranges
  - Create: `data/metadata.json` with stats

**End of Day:** 500 verified transformations, cleaned dataset

---

### Thursday, Feb 15 (Day 4) - 6 hours
**Goal:** Project setup (Vercel, Supabase, GitHub)

- [ ] **9:00 AM** - Service signups
  - Create Vercel account (vercel.com)
  - Create Supabase account (supabase.com)
  - Create Cloudflare account (cloudflare.com)
  - Save all credentials in `.env.local`
  
- [ ] **10:00 AM** - GitHub repository
  - Create repo: `physiqai-mvp`
  - Push existing code
  - Set up `.gitignore` (exclude API keys, large files)
  - Add README with setup instructions
  
- [ ] **11:00 AM** - Supabase database setup
  - Create tables:
    - `users` (id, email, created_at, etc.)
    - `avatars` (user_id, photo_url, measurements, created_at)
    - `workouts` (user_id, date, exercises, duration)
    - `progress` (user_id, date, body_measurements, avatar_version)
  - Set up Row Level Security (RLS) policies
  
- [ ] **1:00 PM** - Cloudflare R2 setup
  - Create bucket: `physiqai-images`
  - Set up public access for avatars
  - Test upload/download
  
- [ ] **3:00 PM** - Next.js project initialization
  - Create new Next.js 14 app: `npx create-next-app@latest`
  - Install dependencies: Supabase, Three.js, TailwindCSS
  - Set up folder structure
  - Deploy hello world to Vercel (test deployment)

**End of Day:** All services connected, app deploys to Vercel

---

### Friday, Feb 16 (Day 5) - 6 hours
**Goal:** Body measurement extraction working (AI vision)

- [ ] **9:00 AM** - Gemini Vision integration
  - Create: `src/lib/bodyAnalysis.ts`
  - Function: `extractMeasurements(imageUrl)`
  - Prompt: Analyze photo and estimate body measurements
  - Returns: Chest, waist, hips, shoulders, arms, legs (estimated)
  
- [ ] **10:30 AM** - Test with scraped data
  - Run body analysis on 20 Reddit transformations
  - Compare AI estimates with user-reported measurements
  - Calculate accuracy rate
  
- [ ] **12:00 PM** - Improve prompts
  - Add: Reference points (head size for scale)
  - Add: Gender-specific analysis
  - Add: Body fat % estimation
  - Add: Muscle definition scoring (1-10)
  
- [ ] **2:00 PM** - Create API endpoint
  - Route: `app/api/analyze-body/route.ts`
  - Upload image → Analyze → Return structured JSON
  - Handle errors, rate limiting
  
- [ ] **3:30 PM** - Build simple test UI
  - Page: Upload image → See extracted measurements
  - Debug tool for testing accuracy

**End of Day:** AI body analysis working with 70%+ accuracy

---

### Weekend, Feb 17-18 (Days 6-7) - 8 hours
**Goal:** Morphing algorithm prototype + documentation

- [ ] **Saturday - 4 hours**
  - Research morphing techniques (OpenCV, linear interpolation)
  - Create: `scripts/prototype_morph.py`
  - Test: Morph between two Reddit transformation images
  - Goal: Smooth transition over 180 frames (6 months = 180 days)
  
- [ ] **Sunday - 4 hours**
  - Write WEEK 1 REVIEW in WEEKLY_PROGRESS.md
  - Update EXECUTION_PLAN.md with any learnings
  - Plan Week 2 tasks in detail
  - Organize all files, commit to GitHub

**End of Week 1:** ✅ Data ready, services setup, body analysis working

---

## 🗓️ WEEK 2: Avatar Generation & Morphing

**Milestone:** 2.5D avatar generator working
**Deliverable:** Upload photo → See interactive avatar

### Monday, Feb 19 (Day 8) - 6 hours
**Goal:** Three.js 2.5D avatar renderer

- [ ] **9:00 AM** - Three.js setup
  - Install: `@react-three/fiber`, `@react-three/drei`
  - Create: `src/components/Avatar3D.tsx`
  - Render: Basic plane with user photo as texture
  
- [ ] **11:00 AM** - Pseudo-3D effect
  - Add: Parallax layers (front body, background)
  - Add: Mouse tracking for rotation effect
  - Add: Lighting effects for depth perception
  
- [ ] **1:00 PM** - Body mesh overlay
  - Create: Simple 3D mesh matching body proportions
  - Map: User measurements to mesh scale
  - Layer: Photo texture on mesh
  
- [ ] **3:30 PM** - Interactive controls
  - Add: Rotate left/right buttons
  - Add: Zoom in/out
  - Add: Reset view button

**End of Day:** Interactive 2.5D avatar that feels 3D

---

### Tuesday, Feb 20 (Day 9) - 6 hours
**Goal:** Morphing engine integrated

- [ ] **9:00 AM** - Physiology calculations
  - Port research formulas to TypeScript
  - Function: `calculateProgression(startMeasurements, workouts, days)`
  - Returns: Predicted measurements for any future date
  
- [ ] **11:00 AM** - Visual morphing
  - Create: `src/lib/morphAvatar.ts`
  - Input: Current avatar, target measurements
  - Output: Morphed avatar with smooth transitions
  - Method: Interpolate mesh scale, adjust texture slightly
  
- [ ] **1:00 PM** - Timeline scrubber
  - UI: Slider from Day 0 to Day 180
  - Live preview: Avatar morphs as you drag slider
  - Show: Predicted measurements at each point
  
- [ ] **3:30 PM** - Animation system
  - Auto-play: Morph from start to end over 10 seconds
  - Loop: Can replay transformation
  - Pause/play controls

**End of Day:** Morphing avatar working smoothly

---

### Wednesday, Feb 21 (Day 10) - 6 hours
**Goal:** Workout logger UI complete

- [ ] **9:00 AM** - Design workout logger
  - Page: `/dashboard/workouts`
  - Form: Exercise name, sets, reps, weight
  - Quick add: Pre-populated exercises (bench press, squat, etc.)
  
- [ ] **11:00 AM** - Database integration
  - Save workouts to Supabase
  - Load workout history
  - Display: Calendar view of logged workouts
  
- [ ] **1:00 PM** - Nutrition tracker (optional)
  - Simple: Protein, carbs, fats, calories
  - Quick entry: Pre-set meals
  - Daily total tracker
  
- [ ] **3:30 PM** - Progress metrics
  - Calculate: Total volume lifted
  - Calculate: Workout frequency (days/week)
  - Display: Weekly summary

**End of Day:** Fully functional workout logger

---

### Thursday, Feb 22 (Day 11) - 6 hours
**Goal:** Daily update system working

- [ ] **9:00 AM** - Morning update logic
  - Cron job: Run daily at 6 AM user timezone
  - Function: Fetch yesterday's workouts
  - Function: Calculate new avatar measurements
  - Function: Generate updated avatar
  
- [ ] **11:00 AM** - Avatar versioning
  - Save: Daily avatar snapshot
  - Table: `avatar_history` (date, measurements, image_url)
  - Load: Historical avatars for comparison
  
- [ ] **1:00 PM** - Notification system
  - Trigger: "Your avatar updated!"
  - Show: Side-by-side yesterday vs today
  - Show: What changed (e.g., "+0.1 inch biceps")
  
- [ ] **3:30 PM** - Before/after comparison
  - UI: Slider to compare Day 1 vs Today
  - Show: Measurements delta
  - Show: Days elapsed, workouts completed

**End of Day:** Avatar updates automatically each morning

---

### Friday, Feb 23 (Day 12) - 6 hours
**Goal:** Onboarding flow polished

- [ ] **9:00 AM** - Onboarding screens
  - Step 1: Welcome + value proposition
  - Step 2: Photo upload (front + side)
  - Step 3: Basic info (age, gender, height, weight)
  - Step 4: Goals (gain muscle, lose fat, both)
  - Step 5: Avatar preview + "Start Tracking"
  
- [ ] **11:00 AM** - Photo upload UX
  - Guidance: Show proper pose examples
  - Validation: Check photo quality before accepting
  - Crop tool: Center body in frame
  
- [ ] **1:00 PM** - Goal setting
  - Target measurements or target weight
  - Timeline: 3mo, 6mo, 1yr
  - Show: "Here's what you could look like" preview
  
- [ ] **3:30 PM** - Authentication
  - Supabase Auth: Email signup
  - Magic link: Passwordless login
  - Profile setup

**End of Day:** Smooth onboarding, new user to avatar in <3 min

---

### Weekend, Feb 24-25 (Days 13-14) - 8 hours
**Goal:** Testing, bug fixes, polish

- [ ] **Saturday - 4 hours**
  - End-to-end testing
  - Fix bugs from testing
  - Optimize performance
  - Mobile responsive tweaks
  
- [ ] **Sunday - 4 hours**
  - WEEK 2 REVIEW
  - Record demo video
  - Write beta tester recruitment post
  - Plan Week 3 outreach

**End of Week 2:** ✅ Full MVP working, ready for beta users

---

## 🗓️ WEEK 3: Beta User Acquisition

**Milestone:** 10 beta users signed up and using app
**Deliverable:** User feedback collected, testimonials

### Monday, Feb 26 (Day 15) - 4 hours
**Goal:** Launch prep + marketing assets

- [ ] **9:00 AM** - Create landing page
  - Headline: "See Your Future Physique Transform Daily"
  - Demo video: Show avatar morphing
  - CTA: "Join Beta Waitlist"
  
- [ ] **11:00 AM** - Beta signup form
  - Typeform or Supabase form
  - Collect: Email, fitness level, goals
  - Auto-email: Beta access instructions
  
- [ ] **1:00 PM** - Social posts
  - Reddit: r/fitness, r/Brogress (read rules first!)
  - Twitter/X: Demo video + link
  - ProductHunt: Prepare launch

**End of Day:** Marketing assets ready, posted on Reddit

---

### Tuesday-Thursday, Feb 27-Mar 1 (Days 16-18) - 12 hours
**Goal:** User outreach, onboarding, support

- [ ] **Daily 9:00 AM** - Check signups
  - Email beta access codes
  - Answer questions
  - Help with setup issues
  
- [ ] **Daily 11:00 AM** - User support
  - Monitor Telegram/email for issues
  - Fix bugs immediately
  - Update docs based on confusion
  
- [ ] **Daily 1:00 PM** - Engagement tracking
  - Check Posthog: Daily active users
  - Check Supabase: Workout logs created
  - Reach out to inactive users
  
- [ ] **Daily 3:00 PM** - Feedback calls
  - Schedule 15-min calls with 2-3 users
  - Ask: What's confusing? What's exciting?
  - Record: Testimonials (with permission)

**End of Period:** 10 beta users actively using app

---

### Friday, Mar 2 (Day 19) - 4 hours
**Goal:** Feedback analysis + iteration plan

- [ ] **9:00 AM** - Compile feedback
  - Categorize: Bugs, UX issues, feature requests
  - Prioritize: Quick wins vs long-term
  
- [ ] **11:00 AM** - Analytics review
  - Calculate: DAU, retention, session time
  - Identify: Drop-off points in funnel
  
- [ ] **1:00 PM** - Update roadmap
  - Plan Week 4-6 improvements
  - Decide: What to fix vs what to defer

**End of Week 3:** ✅ 10 active beta users, clear feedback

---

## 🗓️ WEEK 4-5: Iteration & Polish

**Milestone:** High retention (70%+ DAU), 5 testimonials
**Deliverable:** Polished MVP ready for wider launch

### Focus Areas (14 days)

- [ ] **Bug fixes** - Address all critical user issues
- [ ] **UX improvements** - Smooth confusing flows
- [ ] **Feature additions** - Top 3 user requests (if quick)
- [ ] **Performance** - Faster load times, smoother animations
- [ ] **Content** - Add tips, explanations, motivation
- [ ] **Social features** - Share progress (if users want it)

### Daily Rhythm
- Morning: Check metrics, respond to users
- Midday: Build improvements
- Afternoon: Deploy updates, test with users
- Evening: Plan next day

**End of Week 5:** ✅ App is smooth, users are engaged

---

## 🗓️ WEEK 6: Testimonials & Next Phase Planning

**Milestone:** 5 video testimonials, decision on next steps
**Deliverable:** Investor deck OR revenue plan

### Tasks
- [ ] Record user testimonials
- [ ] Create demo video (polished)
- [ ] Write case studies
- [ ] Calculate unit economics
- [ ] Plan fundraising OR monetization
- [ ] Build pitch deck (if raising)

**End of Week 6:** ✅ Ready to scale (via funding or revenue)

---

## 🎯 Success Criteria & Decision Points

### Week 2 Checkpoint
**Question:** Is the avatar morphing compelling?
- ✅ YES → Continue to beta
- ❌ NO → Pivot to static transformations, re-evaluate

### Week 3 Checkpoint
**Question:** Can we get 10 beta users?
- ✅ YES → Continue iteration
- ❌ NO → Reassess product-market fit

### Week 6 Checkpoint
**Question:** Are users checking daily?
- ✅ 70%+ DAU → Raise money or monetize
- ⚠️ 40-70% DAU → Improve features, extend beta
- ❌ <40% DAU → Pivot or pause

---

## 💰 Budget Breakdown

### One-Time Costs
- [ ] Cloudflare R2 setup: $5
- [ ] Domain name (optional): $10
- Total: $15

### Monthly Costs (Months 1-2)
- [ ] Gemini API: $10
- [ ] Replicate (backup): $20
- [ ] Cloudflare R2: $5
- [ ] Posthog: Free
- [ ] Vercel: Free
- [ ] Supabase: Free
- Total: $35/mo

### Contingency
- [ ] Unexpected API costs: $50
- [ ] Tools/services: $50
- [ ] Buffer: $100

**Total Budget:** ~$350 (well under $1K)

---

## 📈 Metrics Dashboard

### Track Weekly
| Metric | Week 1 | Week 2 | Week 3 | Week 4 | Week 5 | Week 6 |
|--------|--------|--------|--------|--------|--------|--------|
| Beta Users | 0 | 0 | 10 | 15 | 20 | 25 |
| DAU % | - | - | 60% | 70% | 75% | 80% |
| Avg Session | - | - | 1.5min | 2min | 2.5min | 3min |
| Workouts Logged | 0 | 0 | 50 | 150 | 300 | 500 |
| Testimonials | 0 | 0 | 1 | 3 | 5 | 7 |

---

## 🚨 Risk Mitigation

### Technical Risks
**Risk:** Body analysis inaccurate
**Mitigation:** Manual adjustment sliders for users

**Risk:** Morphing looks fake
**Mitigation:** Conservative changes, realistic pace

**Risk:** Performance issues
**Mitigation:** Optimize images, use CDN, lazy loading

### User Risks
**Risk:** Can't get beta users
**Mitigation:** Incentivize ($10 gift cards?), personal outreach

**Risk:** Users don't return daily
**Mitigation:** Push notifications, email reminders

### Budget Risks
**Risk:** API costs higher than expected
**Mitigation:** Aggressive rate limiting, batch processing

---

## 📞 Communication Protocol

### Daily Standups (Async via Telegram)
**Time:** 9 AM PST
**Format:**
- Yesterday: What I built
- Today: What I'm building
- Blockers: Any issues

### Weekly Review (Live Call)
**Time:** Friday 4 PM PST
**Format:**
- Demo progress
- Review metrics
- Plan next week
- Adjust plan if needed

### Emergency Protocol
**If blocked >2 hours:**
- Flag in Telegram immediately
- We problem-solve together
- Don't stay stuck

---

## ✅ Pre-Flight Checklist

Before we start Day 1:
- [ ] Read entire EXECUTION_PLAN.md
- [ ] Confirm all tools/APIs BZ already has access to
- [ ] Create folder structure on Mac
- [ ] Initialize DAILY_LOG.md
- [ ] Set up Git repo
- [ ] Block calendar time for Week 1 tasks
- [ ] Mental commitment: 6 weeks, 20-25 hrs/week

**Are we ready to execute? Let's build this. 🚀**
