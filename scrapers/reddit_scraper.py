#!/usr/bin/env python3
"""
PhysiqAI Reddit Scraper - NO EXTERNAL DEPENDENCIES
Uses only built-in Python modules (urllib, json, re)
"""

import urllib.request
import urllib.error
import json
import os
import re
import ssl
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Configuration
SUBREDDITS = ['progresspics', 'Brogress', 'loseit', 'GettingShredded', 'fitness', 'xxfitness', 'BTFC', 'leangains', 'bodyweightfitness', 'naturalbodybuilding']
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data' / 'collected'
IMAGES_DIR = DATA_DIR / 'images' / 'reddit'
DATABASE_FILE = DATA_DIR / 'database.json'
MISSION_CONTROL = BASE_DIR / 'mission-control.json'

# Create directories
DATA_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# SSL context for HTTPS
ssl_context = ssl.create_default_context()

class RedditScraper:
    def __init__(self):
        self.stats = {
            'posts_checked': 0,
            'posts_valid': 0,
            'images_downloaded': 0,
            'errors': []
        }
        self.database = self.load_database()

    def load_database(self) -> Dict:
        if DATABASE_FILE.exists():
            with open(DATABASE_FILE) as f:
                return json.load(f)
        return {'posts': [], 'stats': {'total': 0, 'by_source': {}, 'by_gender': {'M': 0, 'F': 0, 'unknown': 0}}, 'lastUpdated': None}

    def save_database(self):
        self.database['lastUpdated'] = datetime.now().isoformat()
        with open(DATABASE_FILE, 'w') as f:
            json.dump(self.database, f, indent=2)

    def update_mission_control(self, agent_id: str, status: str, progress: int, current: str, last_update: str):
        try:
            with open(MISSION_CONTROL) as f:
                mc = json.load(f)
            for agent in mc['agents']:
                if agent['id'] == agent_id:
                    agent['status'] = status
                    agent['progress'] = progress
                    agent['current'] = current
                    agent['lastUpdate'] = last_update
                    break
            mc['lastUpdated'] = datetime.now().isoformat()
            with open(MISSION_CONTROL, 'w') as f:
                json.dump(mc, f, indent=2)
        except Exception as e:
            print(f"Warning: Mission control update failed: {e}")

    def add_message(self, message: str, msg_type: str = 'info'):
        try:
            with open(MISSION_CONTROL) as f:
                mc = json.load(f)
            mc['messages'].insert(0, {
                'timestamp': datetime.now().isoformat(),
                'from': 'bz2.0',
                'type': msg_type,
                'message': message
            })
            mc['messages'] = mc['messages'][:20]
            mc['lastUpdated'] = datetime.now().isoformat()
            with open(MISSION_CONTROL, 'w') as f:
                json.dump(mc, f, indent=2)
        except Exception as e:
            print(f"Warning: Message add failed: {e}")

    def extract_metadata(self, title: str) -> Optional[Dict]:
        metadata = {}

        # Gender (M/25 or F/30 pattern)
        gender_match = re.search(r'\b([MF])[\s/]', title, re.IGNORECASE)
        if gender_match:
            metadata['gender'] = gender_match.group(1).upper()

        # Age
        age_match = re.search(r'[MF][\s/](\d{2})[\s/\[]', title, re.IGNORECASE)
        if age_match:
            metadata['age'] = int(age_match.group(1))

        # Height (5'10" format)
        height_match = re.search(r"(\d+)'(\d+)\"?", title)
        if height_match:
            feet, inches = int(height_match.group(1)), int(height_match.group(2))
            metadata['height_cm'] = round((feet * 30.48) + (inches * 2.54))
            metadata['height_display'] = f"{feet}'{inches}\""

        # Weight change (210lbs > 180lbs or 210 > 180)
        weight_match = re.search(r'(\d{2,3})\s*(?:lbs?|pounds?|lb)?\s*[>\-→to]+\s*(\d{2,3})', title, re.IGNORECASE)
        if weight_match:
            metadata['weight_before'] = int(weight_match.group(1))
            metadata['weight_after'] = int(weight_match.group(2))
            metadata['weight_change'] = metadata['weight_after'] - metadata['weight_before']

        # Timeline
        for pattern, unit, mult in [(r'(\d+)\s*months?', 'months', 30), (r'(\d+)\s*years?', 'years', 365), (r'(\d+)\s*weeks?', 'weeks', 7)]:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                val = int(match.group(1))
                metadata['timeline'] = f"{val} {unit}"
                metadata['timeline_days'] = val * mult
                break

        # Quality score
        score = sum([1 for k in ['gender', 'age', 'height_cm', 'weight_before', 'timeline'] if k in metadata])
        metadata['quality_score'] = score

        return metadata if score >= 2 else None

    def fetch_json(self, url: str) -> Optional[Dict]:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'PhysiqAI Research Bot 1.0'})
            with urllib.request.urlopen(req, timeout=30, context=ssl_context) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            self.stats['errors'].append(f"Fetch error: {str(e)[:50]}")
            return None

    def download_image(self, url: str, post_id: str) -> Optional[str]:
        try:
            ext = url.split('.')[-1].split('?')[0][:4]
            if ext not in ['jpg', 'jpeg', 'png', 'gif']:
                ext = 'jpg'

            filename = f"reddit_{post_id}.{ext}"
            filepath = IMAGES_DIR / filename

            if filepath.exists():
                return str(filepath.relative_to(BASE_DIR))

            req = urllib.request.Request(url, headers={'User-Agent': 'PhysiqAI/1.0'})
            with urllib.request.urlopen(req, timeout=30, context=ssl_context) as resp:
                with open(filepath, 'wb') as f:
                    f.write(resp.read())

            self.stats['images_downloaded'] += 1
            return str(filepath.relative_to(BASE_DIR))
        except Exception as e:
            return None

    def get_image_url(self, post: Dict) -> Optional[str]:
        url = post.get('url', '') or post.get('url_overridden_by_dest', '')

        # Direct image
        if any(url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png']):
            return url

        # Imgur single image
        if 'imgur.com' in url and '/a/' not in url and '/gallery/' not in url:
            img_id = url.rstrip('/').split('/')[-1].split('.')[0]
            return f"https://i.imgur.com/{img_id}.jpg"

        # Reddit preview
        preview = post.get('preview', {})
        if preview and 'images' in preview:
            try:
                return preview['images'][0]['source']['url'].replace('&amp;', '&')
            except:
                pass

        return None

    def scrape_subreddit(self, subreddit: str, limit: int = 500) -> List[Dict]:
        print(f"\n🔍 Scraping r/{subreddit}...")
        self.add_message(f"Starting r/{subreddit}...", 'info')

        # Use Reddit JSON endpoint (no API key needed)
        url = f"https://www.reddit.com/r/{subreddit}/top.json?t=year&limit=100"

        all_posts = []
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
                self.stats['posts_checked'] += 1

                # Update progress
                progress = min(95, int((len(all_posts) / limit) * 100))
                self.update_mission_control(
                    'reddit-scraper', 'running', progress,
                    f"{self.stats['posts_valid']} valid posts",
                    f"r/{subreddit}: checking post {self.stats['posts_checked']}"
                )

                # Filter
                if post.get('score', 0) < 50:
                    continue

                # Extract metadata
                title = post.get('title', '')
                metadata = self.extract_metadata(title)
                if not metadata:
                    continue

                # Get image
                image_url = self.get_image_url(post)
                if not image_url:
                    continue

                # Download image
                local_image = self.download_image(image_url, post.get('id', ''))

                # Build record
                record = {
                    'id': f"reddit_{post.get('id', '')}",
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

                all_posts.append(record)
                self.stats['posts_valid'] += 1

                # Update database
                if not any(p['id'] == record['id'] for p in self.database['posts']):
                    self.database['posts'].append(record)
                    self.database['stats']['total'] += 1
                    self.database['stats']['by_source']['reddit'] = self.database['stats']['by_source'].get('reddit', 0) + 1
                    gender = metadata.get('gender', 'unknown')
                    self.database['stats']['by_gender'][gender] = self.database['stats']['by_gender'].get(gender, 0) + 1

                print(f"  ✓ {title[:60]}... (Score: {post.get('score', 0)})")

            after = data['data'].get('after')
            if not after:
                break

            pages += 1
            time.sleep(1)  # Rate limit

        print(f"✅ r/{subreddit}: {len(all_posts)} valid posts")
        self.add_message(f"✅ r/{subreddit}: {len(all_posts)} posts collected", 'success')

        return all_posts

    def run(self, subreddits: List[str] = None, limit_per_sub: int = 500):
        subreddits = subreddits or SUBREDDITS

        print("🚀 PhysiqAI Reddit Scraper")
        print(f"📋 Targeting {len(subreddits)} subreddits\n")

        self.update_mission_control('reddit-scraper', 'running', 0, '0 posts', 'Starting...')
        self.add_message("🚀 Reddit scraper launched!", 'info')

        all_posts = []

        for i, sub in enumerate(subreddits):
            posts = self.scrape_subreddit(sub, limit_per_sub)
            all_posts.extend(posts)

            progress = int(((i + 1) / len(subreddits)) * 100)
            self.update_mission_control(
                'reddit-scraper', 'running', progress,
                f"{len(all_posts)} posts total",
                f"Completed {i+1}/{len(subreddits)} subreddits"
            )
            self.save_database()

        # Final
        self.update_mission_control('reddit-scraper', 'completed', 100, f"{len(all_posts)} posts", 'Complete!')
        self.add_message(f"🎉 Reddit DONE! {len(all_posts)} transformation posts. Gender: {self.database['stats']['by_gender']}", 'success')

        print(f"\n{'='*50}")
        print(f"📊 SUMMARY: {self.stats['posts_valid']} valid, {self.stats['images_downloaded']} images")
        print(f"{'='*50}")

        return all_posts

if __name__ == "__main__":
    scraper = RedditScraper()
    scraper.run(limit_per_sub=500)
