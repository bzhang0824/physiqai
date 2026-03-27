#!/bin/bash
# Wrapper to properly daemonize the overnight scraper

cd /home/clawd/.openclaw/workspace/projects/physiqai
exec python3 scrapers/overnight_scrape.py >> logs/overnight_scrape.log 2>&1
