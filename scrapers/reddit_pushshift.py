#!/usr/bin/env python3
"""
PhysiqAI Reddit Scraper - Using Pushshift (NO API KEY NEEDED)
Collects transformation posts with before/after images
"""

import requests
import json
import os
import re
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import time
import urllib.request

# Configuration
SUBREDDITS = ['progresspics', 'Brogress', 'loseit', 'fitness', 'GettingShredded']
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data' / 'collected'
IMAGES_DIR = DATA_DIR / 'images' / 'reddit'
DATABASE_FILE = DATA_DIR / 'database.json'
MISSION_CONTROL = BASE_DIR / 'mission-control.json'

# Create directories
DATA_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

class RedditScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PhysiqAI Research Bot 1.0'
        })
        self.stats = {
            'posts_checked': 0,
            'posts_valid': 0,
            'images_downloaded': 0,
            'errors': []
        }
        self.database = self.load_database()

    def load_database(self) -> Dict:
        """Load existing database or create new"""
        if DATABASE_FILE.exists():
            with open(DATABASE_FILE) as f:
                return json.load(f)
        return {
            'posts': [],
            'stats': {
                'total': 0,
                'by_source': {},
                'by_gender': {'M': 0, 'F': 0, 'unknown': 0}
            },
            'lastUpdated': None
        }

    def save_database(self):
        """Save database to file"""
        self.database['lastUpdated'] = datetime.now().isoformat()
        with open(DATABASE_FILE, 'w') as f:
            json.dump(self.database, f, indent=2)

    def update_mission_control(self, agent_id: str, status: str, progress: int,
                                current: str, last_update: str, errors: List = None):
        """Update mission control JSON for live dashboard"""
        try:
            with open(MISSION_CONTROL) as f:
                mc = json.load(f)

            for agent in mc['agents']:
                if agent['id'] == agent_id:
                    agent['status'] = status
                    agent['progress'] = progress
                    agent['current'] = current
                    agent['lastUpdate'] = last_update
                    if errors:
                        agent['errors'] = errors
                    break

            mc['lastUpdated'] = datetime.now().isoformat()

            with open(MISSION_CONTROL, 'w') as f:
                json.dump(mc, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not update mission control: {e}")

    def add_message(self, message: str, msg_type: str = 'info'):
        """Add a message to mission control"""
        try:
            with open(MISSION_CONTROL) as f:
                mc = json.load(f)

            mc['messages'].insert(0, {
                'timestamp': datetime.now().isoformat(),
                'from': 'bz2.0',
                'type': msg_type,
                'message': message
            })

            # Keep only last 20 messages
            mc['messages'] = mc['messages'][:20]
            mc['lastUpdated'] = datetime.now().isoformat()

            with open(MISSION_CONTROL, 'w') as f:
                json.dump(mc, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not add message: {e}")

    def extract_metadata(self, title: str) -> Optional[Dict]:
        """Extract structured data from post title"""
        metadata = {}

        # Gender
        gender_match = re.search(r'\b([MF])\/', title, re.IGNORECASE)
        if gender_match:
            metadata['gender'] = gender_match.group(1).upper()

        # Age
        age_match = re.search(r'\/(\d{2})\/', title)
        if age_match:
            metadata['age'] = int(age_match.group(1))

        # Height
        height_match = re.search(r"(\d+)'(\d+)\"?", title)
        if height_match:
            feet = int(height_match.group(1))
            inches = int(height_match.group(2))
            metadata['height_cm'] = round((feet * 30.48) + (inches * 2.54))
            metadata['height_display'] = f"{feet}'{inches}\""

        # Weight change
        weight_match = re.search(r'(\d+)\s*(?:lbs?|pounds?)\s*[>\-→]\s*(\d+)', title, re.IGNORECASE)
        if weight_match:
            metadata['weight_before'] = int(weight_match.group(1))
            metadata['weight_after'] = int(weight_match.group(2))
            metadata['weight_change'] = metadata['weight_after'] - metadata['weight_before']

        # Timeline
        timeline_patterns = [
            (r'(\d+)\s*months?', 'months', 30),
            (r'(\d+)\s*years?', 'years', 365),
            (r'(\d+)\s*weeks?', 'weeks', 7),
        ]

        for pattern, unit, multiplier in timeline_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                value = int(match.group(1))
                metadata['timeline'] = f"{value} {unit}"
                metadata['timeline_days'] = value * multiplier
                break

        # Quality score (1-5 based on data completeness)
        score = 0
        if 'gender' in metadata: score += 1
        if 'age' in metadata: score += 1
        if 'height_cm' in metadata: score += 1
        if 'weight_before' in metadata and 'weight_after' in metadata: score += 1
        if 'timeline' in metadata: score += 1
        metadata['quality_score'] = score

        return metadata if score >= 2 else None

    def get_image_url(self, post: Dict) -> Optional[str]:
        """Extract image URL from post"""
        url = post.get('url', '')

        # Direct image
        if any(url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']):
            return url

        # Imgur
        if 'imgur.com' in url and not url.endswith('.gifv'):
            if '/a/' not in url and '/gallery/' not in url:
                # Single imgur image
                img_id = url.split('/')[-1].split('.')[0]
                return f"https://i.imgur.com/{img_id}.jpg"

        # Reddit preview
        preview = post.get('preview', {})
        if preview and 'images' in preview:
            try:
                return preview['images'][0]['source']['url'].replace('&amp;', '&')
            except:
                pass

        return None

    def download_image(self, url: str, post_id: str) -> Optional[str]:
        """Download image and return local path"""
        try:
            # Generate filename from URL hash
            ext = url.split('.')[-1].split('?')[0][:4]
            if ext not in ['jpg', 'jpeg', 'png', 'gif']:
                ext = 'jpg'
            filename = f"reddit_{post_id}.{ext}"
            filepath = IMAGES_DIR / filename

            if filepath.exists():
                return str(filepath.relative_to(BASE_DIR))

            # Download
            urllib.request.urlretrieve(url, filepath)
            self.stats['images_downloaded'] += 1
            return str(filepath.relative_to(BASE_DIR))

        except Exception as e:
            self.stats['errors'].append(f"Image download failed: {str(e)[:50]}")
            return None

    def fetch_pushshift(self, subreddit: str, limit: int = 500) -> List[Dict]:
        """Fetch posts from Pushshift API"""
        posts = []
        url = f"https://api.pullpush.io/reddit/search/submission"

        params = {
            'subreddit': subreddit,
            'size': min(limit, 100),
            'sort': 'desc',
            'sort_type': 'score'
        }

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            posts = data.get('data', [])
        except Exception as e:
            self.stats['errors'].append(f"Pushshift error for r/{subreddit}: {str(e)[:50]}")
            self.add_message(f"⚠️ Error fetching r/{subreddit}: {str(e)[:50]}", 'warning')

        return posts

    def scrape_subreddit(self, subreddit: str, limit: int = 500) -> List[Dict]:
        """Scrape a single subreddit"""
        print(f"\n🔍 Scraping r/{subreddit}...")
        self.add_message(f"Starting r/{subreddit} scrape...", 'info')

        posts = self.fetch_pushshift(subreddit, limit)
        valid_posts = []

        for i, post in enumerate(posts):
            self.stats['posts_checked'] += 1

            # Update progress
            progress = int((i / len(posts)) * 100) if posts else 0
            self.update_mission_control(
                'reddit-scraper',
                'running',
                progress,
                f"{self.stats['posts_valid']} valid posts",
                f"Checking r/{subreddit}: {i}/{len(posts)}"
            )

            # Extract metadata
            title = post.get('title', '')
            metadata = self.extract_metadata(title)

            if not metadata:
                continue

            # Get image URL
            image_url = self.get_image_url(post)
            if not image_url:
                continue

            # Download image
            local_image = self.download_image(image_url, post.get('id', str(i)))

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
                'created_utc': post.get('created_utc', 0),
                'metadata': metadata,
                'scraped_at': datetime.now().isoformat()
            }

            valid_posts.append(record)
            self.stats['posts_valid'] += 1

            # Update database
            self.database['posts'].append(record)
            self.database['stats']['total'] += 1
            self.database['stats']['by_source']['reddit'] = \
                self.database['stats']['by_source'].get('reddit', 0) + 1
            gender = metadata.get('gender', 'unknown')
            self.database['stats']['by_gender'][gender] = \
                self.database['stats']['by_gender'].get(gender, 0) + 1

            # Rate limit
            time.sleep(0.2)

        print(f"✅ r/{subreddit}: {len(valid_posts)} valid posts")
        self.add_message(f"✅ r/{subreddit} complete: {len(valid_posts)} posts with images", 'success')

        return valid_posts

    def run(self, subreddits: List[str] = None, limit_per_sub: int = 500):
        """Main scraping workflow"""
        subreddits = subreddits or SUBREDDITS

        print("🚀 PhysiqAI Reddit Scraper Started")
        print(f"📋 Target: {len(subreddits)} subreddits, {limit_per_sub} posts each")

        self.update_mission_control(
            'reddit-scraper', 'running', 0,
            '0 posts', 'Starting...'
        )
        self.add_message("🚀 Reddit scraper launched! Targeting 5 subreddits...", 'info')

        all_posts = []

        for i, subreddit in enumerate(subreddits):
            posts = self.scrape_subreddit(subreddit, limit_per_sub)
            all_posts.extend(posts)

            # Update overall progress
            overall_progress = int(((i + 1) / len(subreddits)) * 100)
            self.update_mission_control(
                'reddit-scraper', 'running', overall_progress,
                f"{len(all_posts)} posts collected",
                f"Completed {i+1}/{len(subreddits)} subreddits"
            )

            # Save incrementally
            self.save_database()

        # Final update
        self.update_mission_control(
            'reddit-scraper', 'completed', 100,
            f"{len(all_posts)} posts total",
            'Scraping complete!'
        )

        self.add_message(
            f"🎉 Reddit scraping COMPLETE! {len(all_posts)} transformation posts with images collected. "
            f"Gender split: {self.database['stats']['by_gender']}",
            'success'
        )

        # Print summary
        print("\n" + "="*50)
        print("📊 SCRAPING SUMMARY")
        print("="*50)
        print(f"Posts checked: {self.stats['posts_checked']}")
        print(f"Valid posts: {self.stats['posts_valid']}")
        print(f"Images downloaded: {self.stats['images_downloaded']}")
        print(f"Errors: {len(self.stats['errors'])}")
        print("="*50)

        return all_posts


if __name__ == "__main__":
    scraper = RedditScraper()
    scraper.run(limit_per_sub=500)
