#!/bin/bash
# Wrapper to keep the scraper running

cd /home/clawd/.openclaw/workspace/projects/physiqai

while true; do
    echo "[$(date)] Starting scraper..." >> logs/wrapper.log
    python3 -u scrapers/overnight_scrape.py >> logs/overnight_scrape.log 2>&1
    echo "[$(date)] Scraper exited with code $?. Restarting in 10 seconds..." >> logs/wrapper.log
    sleep 10
done
