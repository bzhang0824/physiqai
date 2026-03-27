#!/usr/bin/env python3
"""
Agent I1: Reddit Image Hunter - r/progresspics
Target: 1000 posts with images
"""

import requests
import json
import time
import re
from datetime import datetime
from pathlib import Path

OUTPUT_FILE = Path('data/agents/agent_i1_progresspics.jsonl')
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

print("[AGENT I1] Starting Reddit r/progresspics deep scrape...")

collected = []
target = 1000

for batch in range(10):  # 100 posts per batch
    try:
        url = "https://api.pullpush.io/reddit/search/submission"
        params = {
            "subreddit": "progresspics",
            "size": 100,
            "sort": "desc",
            "sort_type": "score",
            "score": ">100"
        }

        if batch > 0:
            params["before"] = collected[-1]["timestamp"] if collected else None

        response = requests.get(url, params=params, timeout=30)
        data = response.json()

        for post in data.get("data", []):
            title = post.get("title", "")

            # Parse transformation data
            gender = re.search(r'\b([MF])[/\\]', title.upper())
            weight_match = re.search(r'(\d+)\s*(?:lbs?|pounds?).*?(\d+)\s*(?:lbs?|pounds?)', title, re.IGNORECASE)
            timeline = re.search(r'(\d+)\s*(months?|years?)', title, re.IGNORECASE)

            if gender and weight_match and timeline:
                post_data = {
                    "agent": "I1",
                    "source": "reddit_progresspics",
                    "id": post["id"],
                    "title": title,
                    "gender": gender.group(1),
                    "weight_before": int(weight_match.group(1)),
                    "weight_after": int(weight_match.group(2)),
                    "timeline": timeline.group(0),
                    "score": post.get("score", 0),
                    "image_url": post.get("url", ""),
                    "timestamp": post.get("created_utc"),
                    "collected_at": datetime.now().isoformat()
                }

                # Quality score
                quality = 3
                if post_data["score"] > 500: quality += 1
                if "http" in post_data["image_url"]: quality += 1
                post_data["quality"] = min(quality, 5)

                collected.append(post_data)

                # Save incrementally
                with open(OUTPUT_FILE, 'a') as f:
                    f.write(json.dumps(post_data) + '\n')

        print(f"[AGENT I1] Batch {batch+1}/10: {len(collected)} collected")
        time.sleep(1)

        if len(collected) >= target:
            break

    except Exception as e:
        print(f"[AGENT I1] Error: {e}")
        time.sleep(2)

print(f"[AGENT I1] COMPLETE: {len(collected)} posts collected")
