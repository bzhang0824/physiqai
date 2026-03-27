#!/usr/bin/env python3
"""
PhysiqAI OVERNIGHT SCRAPER
Runs continuously through multiple sources to maximize data collection
"""

import urllib.request
import urllib.parse
import json
import re
import ssl
import time
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data' / 'collected'
IMAGES_DIR = DATA_DIR / 'images'
DATABASE_FILE = DATA_DIR / 'database.json'
MISSION_CONTROL = BASE_DIR / 'mission-control.json'

ssl_context = ssl.create_default_context()

# MASSIVE subreddit list for transformation content
SUBREDDITS = [
    # Main transformation subs
    'progresspics', 'Brogress', 'loseit', 'GettingShredded',
    # Fitness subs with transformations
    'fitness', 'xxfitness', 'BTFC', 'leangains',
    'bodyweightfitness', 'naturalbodybuilding', 'gainit',
    # More niche
    'FTMFitness', 'flexinlesbians', 'StrongCurves',
    'Fitness_Progression', 'weightlifting', 'powerlifting',
    # Before/after focused
    'uglyduckling', 'fasting', 'intermittentfasting',
    'keto', 'PlantBasedDiet', 'veganfitness',
]

class OvernightScraper:
    def __init__(self):
        self.stats = {'total_scraped': 0, 'images': 0, 'errors': 0}
        self.database = self.load_database()
        self.seen_ids = set(p['id'] for p in self.database.get('posts', []))

    def load_database(self) -> Dict:
        if DATABASE_FILE.exists():
            with open(DATABASE_FILE) as f:
                return json.load(f)
        return {'posts': [], 'stats': {'total': 0, 'by_source': {}, 'by_gender': {'M': 0, 'F': 0, 'unknown': 0}}, 'lastUpdated': None}

    def save_database(self):
        self.database['lastUpdated'] = datetime.now().isoformat()
        self.database['stats']['total'] = len(self.database['posts'])
        with open(DATABASE_FILE, 'w') as f:
            json.dump(self.database, f, indent=2)

    def update_mc(self, phase: str, progress: int, total: int, msg: str):
        try:
            with open(MISSION_CONTROL) as f:
                mc = json.load(f)

            mc['phase'] = phase
            mc['overallProgress'] = min(progress, 99)
            mc['lastUpdated'] = datetime.now().isoformat()

            # Update or add overnight agent
            found = False
            for a in mc['agents']:
                if a['id'] == 'overnight-scraper':
                    a['status'] = 'running'
                    a['progress'] = min(progress, 99)
                    a['current'] = f"{total} posts collected"
                    a['lastUpdate'] = msg
                    found = True
                    break

            if not found:
                mc['agents'].insert(0, {
                    'id': 'overnight-scraper',
                    'name': 'Overnight Mass Scraper',
                    'description': f'Scraping {len(SUBREDDITS)} subreddits for maximum data',
                    'status': 'running',
                    'progress': progress,
                    'target': '5000+ posts',
                    'current': f"{total} posts",
                    'eta': 'Running overnight',
                    'lastUpdate': msg,
                    'errors': []
                })

            # Add message
            mc['messages'].insert(0, {
                'timestamp': datetime.now().isoformat(),
                'from': 'bz2.0',
                'type': 'info',
                'message': msg
            })
            mc['messages'] = mc['messages'][:30]

            with open(MISSION_CONTROL, 'w') as f:
                json.dump(mc, f, indent=2)
        except Exception as e:
            print(f"MC update error: {e}")

    def fetch_json(self, url: str) -> Optional[Dict]:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'PhysiqAI Research Bot 2.0'})
            with urllib.request.urlopen(req, timeout=30, context=ssl_context) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except:
            return None

    def extract_metadata(self, title: str) -> Optional[Dict]:
        metadata = {}

        # Gender
        g = re.search(r'\b([MF])[\s/]', title, re.I)
        if g: metadata['gender'] = g.group(1).upper()

        # Age
        a = re.search(r'[MF][\s/](\d{2})[\s/\[]', title, re.I)
        if a: metadata['age'] = int(a.group(1))

        # Height
        h = re.search(r"(\d+)'(\d+)\"?", title)
        if h:
            metadata['height_cm'] = round((int(h.group(1)) * 30.48) + (int(h.group(2)) * 2.54))

        # Weight
        w = re.search(r'(\d{2,3})\s*(?:lbs?|pounds?|lb)?\s*[>\-→to]+\s*(\d{2,3})', title, re.I)
        if w:
            metadata['weight_before'] = int(w.group(1))
            metadata['weight_after'] = int(w.group(2))
            metadata['weight_change'] = metadata['weight_after'] - metadata['weight_before']

        # Timeline
        for p, u, m in [(r'(\d+)\s*months?', 'months', 30), (r'(\d+)\s*years?', 'years', 365), (r'(\d+)\s*weeks?', 'weeks', 7)]:
            t = re.search(p, title, re.I)
            if t:
                metadata['timeline'] = f"{t.group(1)} {u}"
                metadata['timeline_days'] = int(t.group(1)) * m
                break

        # Quality score
        score = sum([1 for k in ['gender', 'age', 'height_cm', 'weight_before', 'timeline'] if k in metadata])
        metadata['quality_score'] = score

        return metadata if score >= 1 else None  # Lower threshold to get more data

    def get_image_url(self, post: Dict) -> Optional[str]:
        url = post.get('url', '') or post.get('url_overridden_by_dest', '')

        if any(url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png']):
            return url

        if 'imgur.com' in url and '/a/' not in url and '/gallery/' not in url:
            img_id = url.rstrip('/').split('/')[-1].split('.')[0]
            return f"https://i.imgur.com/{img_id}.jpg"

        preview = post.get('preview', {})
        if preview and 'images' in preview:
            try:
                return preview['images'][0]['source']['url'].replace('&amp;', '&')
            except:
                pass

        return None

    def download_image(self, url: str, post_id: str, source: str) -> Optional[str]:
        try:
            img_dir = IMAGES_DIR / source
            img_dir.mkdir(parents=True, exist_ok=True)

            ext = url.split('.')[-1].split('?')[0][:4]
            if ext not in ['jpg', 'jpeg', 'png', 'gif']:
                ext = 'jpg'

            filename = f"{source}_{post_id}.{ext}"
            filepath = img_dir / filename

            if filepath.exists():
                return str(filepath.relative_to(BASE_DIR))

            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30, context=ssl_context) as resp:
                with open(filepath, 'wb') as f:
                    f.write(resp.read())

            self.stats['images'] += 1
            return str(filepath.relative_to(BASE_DIR))
        except:
            return None

    def scrape_subreddit(self, subreddit: str, limit: int = 500) -> int:
        print(f"\n🔍 Scraping r/{subreddit}...")

        url = f"https://www.reddit.com/r/{subreddit}/top.json?t=all&limit=100"
        count = 0
        after = None
        pages = 0
        max_pages = (limit // 100) + 1

        while pages < max_pages:
            fetch_url = url + (f"&after={after}" if after else "")
            data = self.fetch_json(fetch_url)

            if not data or 'data' not in data:
                break

            posts = data['data'].get('children', [])
            if not posts:
                break

            for item in posts:
                post = item.get('data', {})
                post_id = f"reddit_{post.get('id', '')}"

                if post_id in self.seen_ids:
                    continue

                if post.get('score', 0) < 20:  # Lower threshold
                    continue

                title = post.get('title', '')
                metadata = self.extract_metadata(title)

                if not metadata:
                    continue

                image_url = self.get_image_url(post)
                local_image = None
                if image_url:
                    local_image = self.download_image(image_url, post.get('id', ''), 'reddit')

                record = {
                    'id': post_id,
                    'source': 'reddit',
                    'subreddit': subreddit,
                    'title': title,
                    'url': post.get('url', ''),
                    'permalink': f"https://reddit.com{post.get('permalink', '')}",
                    'image_url': image_url,
                    'local_image': local_image,
                    'score': post.get('score', 0),
                    'metadata': metadata,
                    'scraped_at': datetime.now().isoformat()
                }

                self.database['posts'].append(record)
                self.seen_ids.add(post_id)
                self.stats['total_scraped'] += 1
                count += 1

                # Update gender stats
                gender = metadata.get('gender', 'unknown')
                self.database['stats']['by_gender'][gender] = self.database['stats']['by_gender'].get(gender, 0) + 1
                self.database['stats']['by_source']['reddit'] = self.database['stats']['by_source'].get('reddit', 0) + 1

                print(f"  ✓ {title[:50]}...")

            after = data['data'].get('after')
            if not after:
                break

            pages += 1
            time.sleep(1)

        print(f"  ✅ r/{subreddit}: {count} new posts")
        return count

    def run(self):
        print("="*60)
        print("🌙 PhysiqAI OVERNIGHT MASS SCRAPER")
        print(f"📋 Targeting {len(SUBREDDITS)} subreddits")
        print(f"🎯 Goal: 5000+ transformation posts")
        print("="*60)

        self.update_mc(
            "Overnight Data Collection",
            0,
            len(self.database['posts']),
            f"🌙 Overnight scraper started! Targeting {len(SUBREDDITS)} subreddits..."
        )

        total_new = 0

        for i, sub in enumerate(SUBREDDITS):
            progress = int((i / len(SUBREDDITS)) * 100)

            self.update_mc(
                "Overnight Data Collection",
                progress,
                len(self.database['posts']),
                f"Scraping r/{sub} ({i+1}/{len(SUBREDDITS)})"
            )

            try:
                new = self.scrape_subreddit(sub, limit=500)
                total_new += new
            except Exception as e:
                print(f"  ❌ Error on r/{sub}: {e}")
                self.stats['errors'] += 1

            # Save after each subreddit
            self.save_database()

            # Rate limit
            time.sleep(2)

        # Final update
        total = len(self.database['posts'])
        self.update_mc(
            "Data Collection Complete",
            100,
            total,
            f"🎉 Overnight scraping COMPLETE! {total} total posts ({total_new} new). Ready for model training!"
        )

        # Update agent to completed
        try:
            with open(MISSION_CONTROL) as f:
                mc = json.load(f)
            for a in mc['agents']:
                if a['id'] == 'overnight-scraper':
                    a['status'] = 'completed'
                    a['progress'] = 100
            with open(MISSION_CONTROL, 'w') as f:
                json.dump(mc, f, indent=2)
        except:
            pass

        print("\n" + "="*60)
        print("📊 OVERNIGHT SCRAPE COMPLETE!")
        print("="*60)
        print(f"Total posts: {total}")
        print(f"New posts: {total_new}")
        print(f"Images: {self.stats['images']}")
        print(f"Errors: {self.stats['errors']}")
        print(f"Gender: {self.database['stats']['by_gender']}")
        print("="*60)

if __name__ == "__main__":
    import traceback

    while True:
        try:
            scraper = OvernightScraper()
            scraper.run()

            # Rest between cycles - 5 minutes
            print("\n😴 Resting for 5 minutes before next cycle...")
            time.sleep(300)

        except KeyboardInterrupt:
            print("\n👋 Scraper stopped by user")
            break
        except Exception as e:
            print(f"\n💥 CRITICAL ERROR: {e}")
            traceback.print_exc()
            print("\n🔄 Restarting in 60 seconds...")
            time.sleep(60)
