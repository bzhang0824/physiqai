#!/bin/bash
# Daily Reddit Fitness Scraper
# Runs every day at 3 AM UTC

APP_DIR="/home/clawd/.openclaw/workspace/projects/physiqai"
LOG_FILE="$APP_DIR/logs/reddit-daily.log"
DATE=$(date +%Y-%m-%d)

mkdir -p "$APP_DIR/logs" "$APP_DIR/data/raw_reddit/daily"

echo "[$(date)] Starting daily Reddit scrape..." >> "$LOG_FILE"

cd "$APP_DIR"

# Scrape with rate limiting (max 100 requests/minute)
python3 scripts/reddit_scraper.py \
  --subreddits progresspics Brogress gainit GettingShredded loseit \
  --limit 500 \
  --timeframe day \
  --output "data/raw_reddit/daily/transformations_$DATE.json" \
  --rate-limit 60 \
  >> "$LOG_FILE" 2>&1

# Count new records
NEW_RECORDS=$(cat "data/raw_reddit/daily/transformations_$DATE.json" 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('posts',[])))" || echo "0")

echo "[$(date)] Collected $NEW_RECORDS new records" >> "$LOG_FILE"

# Weekly consolidation (Sundays at 3:15 AM)
if [ $(date +%u) -eq 7 ]; then
    echo "[$(date)] Weekly consolidation..." >> "$LOG_FILE"
    python3 scripts/consolidate_reddit.py >> "$LOG_FILE" 2>&1
fi

echo "[$(date)] Daily scrape complete" >> "$LOG_FILE"
