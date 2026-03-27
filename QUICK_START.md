# PhysiqAI - Day 1 Quick Start

**Goal:** Get Reddit scraper running in 15 minutes

---

## 🚀 Steps

### 1. Get Reddit API Keys (5 min)
- Go to: https://www.reddit.com/prefs/apps
- Click "Create App"
- Choose "script" type
- Save `client_id` and `client_secret`

### 2. Setup (5 min)
```bash
cd ~/Documents/physiqai/
chmod +x scripts/setup_day1.sh
./scripts/setup_day1.sh

# Edit .env with your credentials
nano .env
```

### 3. Run Scraper (5 min)
```bash
python3 scripts/scrape_progresspics.py
```

### 4. Check Results
```bash
ls data/reddit_scrapes/images/
# Should see 10 images

cat data/reddit_scrapes/metadata/*.json
# Should see JSON with metadata
```

---

## ✅ Success = 10 images downloaded

---

## 🆘 Help

**Error: "Module not found"**
→ `pip3 install praw pillow requests`

**Error: "Invalid credentials"**
→ Check .env file, make sure app type is "script"

**No images?**
→ Normal - script filters for quality. Try increasing to 50 posts.

---

**Need help?** Message me in Telegram with error details.

**Working?** Let me know and I'll build Day 2 tomorrow!
