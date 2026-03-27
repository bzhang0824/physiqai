#!/usr/bin/env python3
"""
Agent I2: Reddit Image Hunter - r/Brogress + r/loseit
Target: 500 posts
"""

import requests
import json
import time
import re
from datetime import datetime
from pathlib import Path

OUTPUT_FILE = Path('data/agents/agent_i2_brogress_loseit.jsonl')
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

SUBREDDITS = ['Brogress', 'loseit']

collected = []
target_per_sub = 250

for subreddit in SUBREDDITS:
    print(f"[AGENT I2] Starting r/{subreddit}...")
    sub_collected = 0

    for batch in range(5):
        try:
            url = "https://api.pullpush.io/reddit/search/submission"
            params = {
                "subreddit": subreddit,
                "size": 100,
                "sort": "desc",
                "sort_type": "score",
                "score": ">50"
            }

            response = requests.get(url, params=params, timeout=30)
            data = response.json()

            for post in data.get("data", []):
                title = post.get("title", "")

                gender = re.search(r'\b([MF])[/\\]', title.upper())
                weight_match = re.search(r'(\d+)\s*(?:lbs?|pounds?).*?(\d+)\s*(?:lbs?|pounds?)', title, re.IGNORECASE)

                if gender and weight_match:
                    post_data = {
                        "agent": "I2",
                        "source": f"reddit_{subreddit}",
                        "id": post["id"],
                        "title": title[:100],
                        "gender": gender.group(1),
                        "weight_before": int(weight_match.group(1)),
                        "weight_after": int(weight_match.group(2)),
                        "score": post.get("score", 0),
                        "image_url": post.get("url", ""),
                        "collected_at": datetime.now().isoformat(),
                        "quality": 4 if post.get("score", 0) > 300 else 3
                    }

                    collected.append(post_data)
                    sub_collected += 1

                    with open(OUTPUT_FILE, 'a') as f:
                        f.write(json.dumps(post_data) + '\n')

            print(f"[AGENT I2] r/{subreddit} Batch {batch+1}: {sub_collected} collected")
            time.sleep(1)

            if sub_collected >= target_per_sub:
                break

        except Exception as e:
            print(f"[AGENT I2] Error: {e}")
            time.sleep(2)

print(f"[AGENT I2] COMPLETE: {len(collected)} posts collected")
