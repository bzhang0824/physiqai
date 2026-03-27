# PhysiqAI Tools & Services Checklist

Complete setup checklist for all required tools, APIs, and accounts.

---

## ✅ Already Have

- [x] **Google Gemini API** - Body analysis
  - Key in `.env`: `GOOGLE_AI_KEY`
  - Cost: ~$10/mo
  
- [x] **Replicate API** - Backup image processing
  - Key in `.env`: `REPLICATE_API_TOKEN`
  - Cost: ~$20/mo
  
- [x] **Mac with VSCode** - Development environment
  - Location: `~/Documents/physiqai/`
  
- [x] **Claude Code / Cursor** - AI coding assistant
  - For building with AI help

---

## 🔧 Need to Set Up (Week 1, Day 4)

### Reddit API
- [ ] Create Reddit account (if don't have)
- [ ] Go to: https://www.reddit.com/prefs/apps
- [ ] Click "Create App"
- [ ] Select "script" type
- [ ] Save credentials:
  - `REDDIT_CLIENT_ID`
  - `REDDIT_CLIENT_SECRET`
  - `REDDIT_USER_AGENT`

### Vercel (Frontend Hosting)
- [ ] Sign up: https://vercel.com
- [ ] Connect GitHub account
- [ ] Install Vercel CLI: `npm i -g vercel`
- [ ] Login: `vercel login`
- [ ] Cost: FREE

### Supabase (Database + Auth)
- [ ] Sign up: https://supabase.com
- [ ] Create new project: "physiqai-mvp"
- [ ] Save credentials:
  - `NEXT_PUBLIC_SUPABASE_URL`
  - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
  - `SUPABASE_SERVICE_ROLE_KEY`
- [ ] Cost: FREE (up to 500MB database)

### Cloudflare R2 (Image Storage)
- [ ] Sign up: https://cloudflare.com
- [ ] Go to R2 section
- [ ] Create bucket: "physiqai-images"
- [ ] Generate API token
- [ ] Save credentials:
  - `R2_ACCOUNT_ID`
  - `R2_ACCESS_KEY_ID`
  - `R2_SECRET_ACCESS_KEY`
- [ ] Cost: ~$5/mo

### GitHub (Version Control)
- [ ] Create account (if don't have)
- [ ] Create new repo: "physiqai-mvp"
- [ ] Set to private
- [ ] Clone to Mac: `git clone ...`
- [ ] Cost: FREE

### PostHog (Analytics) - Optional
- [ ] Sign up: https://posthog.com
- [ ] Create project: "PhysiqAI"
- [ ] Save: `NEXT_PUBLIC_POSTHOG_KEY`
- [ ] Cost: FREE (up to 1M events)

---

## 📦 Development Tools

### Python (Data Collection)
- [ ] Install Python 3.10+: `brew install python3`
- [ ] Install PRAW: `pip install praw`
- [ ] Install Pillow: `pip install Pillow`
- [ ] Install requests: `pip install requests`

### Node.js (Next.js App)
- [ ] Install Node 18+: `brew install node`
- [ ] Install pnpm: `npm i -g pnpm`
- [ ] Verify: `node -v && pnpm -v`

### Git
- [ ] Verify installed: `git --version`
- [ ] Configure:
  - `git config --global user.name "Brian Zhang"`
  - `git config --global user.email "your@email.com"`

---

## 🔐 Environment Variables

Create `.env.local` in project root:

```bash
# AI Services
GOOGLE_AI_KEY=AIzaSy...
REPLICATE_API_TOKEN=r8_...

# Reddit API
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
REDDIT_USER_AGENT=PhysiqAI Data Collector

# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJh...
SUPABASE_SERVICE_ROLE_KEY=eyJh...

# Cloudflare R2
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...

# PostHog (Optional)
NEXT_PUBLIC_POSTHOG_KEY=phc_...
NEXT_PUBLIC_POSTHOG_HOST=https://app.posthog.com

# App Config
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

**Important:** Never commit `.env.local` to GitHub!

---

## 📱 Communication Tools

### Daily Updates
- [ ] Telegram - Daily standups at 9 AM PST
- [ ] Format: Yesterday / Today / Blockers

### Weekly Reviews
- [ ] Telegram call - Fridays 4 PM PST
- [ ] Screen share for demos

### Emergency Help
- [ ] Telegram - If blocked >2 hours
- [ ] Don't stay stuck!

---

## 🎯 Pre-Start Verification

Before starting Day 1:

- [ ] Read entire EXECUTION_PLAN.md
- [ ] All "Already Have" items confirmed
- [ ] Mac is set up with VSCode
- [ ] Git installed and configured
- [ ] Python 3 installed
- [ ] Node.js installed
- [ ] Calendar blocked for Week 1 (4-6h/day)
- [ ] Mentally committed to 6 weeks

**Ready to execute:** YES / NO

---

## 💡 Quick References

### Folder Structure
```
~/Documents/physiqai/
├── EXECUTION_PLAN.md
├── DAILY_LOG.md
├── WEEKLY_PROGRESS.md
├── SPRINT_BOARD.md
├── TOOLS_CHECKLIST.md (this file)
├── .env.local
├── data/
│   ├── reddit_scrapes/
│   └── processed/
├── scripts/
├── src/
└── docs/
```

### Helpful Commands
```bash
# Start development server
pnpm dev

# Run scraper
python scripts/scrape_progresspics.py

# Deploy to Vercel
vercel --prod

# Check git status
git status

# Commit changes
git add . && git commit -m "Description" && git push
```

---

**Last Updated:** 2026-02-12
**Status:** Ready to start Day 1
