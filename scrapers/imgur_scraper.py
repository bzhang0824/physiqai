#!/usr/bin/env python3
"""
PhysiqAI Imgur Transformation Scraper
Scrapes public Imgur galleries for transformation photos
NO API KEY NEEDED - uses public gallery endpoints
"""

import urllib.request
import json
import re
import ssl
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data' / 'collected'
IMAGES_DIR = DATA_DIR / 'images' / 'imgur'
DATABASE_FILE = DATA_DIR / 'database.json'
MISSION_CONTROL = BASE_DIR / 'mission-control.json'

IMAGES_DIR.mkdir(parents=True, exist_ok=True)
ssl_context = ssl.create_default_context()

# Imgur search terms for transformations
SEARCH_TERMS = [
    'transformation',
    'weight loss progress',
    'before after fitness',
    'body transformation',
    'fitness journey',
    'weight loss journey'
]

class ImgurScraper:
    def __init__(self):
        self.stats = {'posts_found': 0, 'images_downloaded': 0, 'errors': []}
        self.database = self.load_database()

    def load_database(self) -> Dict:
        if DATABASE_FILE.exists():
            with open(DATABASE_FILE) as f:
                return json.load(f)
        return {'posts': [], 'stats': {'total': 0, 'by_source': {}, 'by_gender': {}}, 'lastUpdated': None}

    def save_database(self):
        self.database['lastUpdated'] = datetime.now().isoformat()
        with open(DATABASE_FILE, 'w') as f:
            json.dump(self.database, f, indent=2)

    def update_mc(self, status, progress, current, update):
        try:
            with open(MISSION_CONTROL) as f:
                mc = json.load(f)
            # Add or update imgur agent
            imgur_agent = None
            for a in mc['agents']:
                if a['id'] == 'imgur-scraper':
                    imgur_agent = a
                    break
            if not imgur_agent:
                imgur_agent = {
                    'id': 'imgur-scraper',
                    'name': 'Imgur Scraper',
                    'description': 'Scraping public Imgur transformation galleries',
                    'status': status,
                    'progress': progress,
                    'target': '500+ posts',
                    'current': current,
                    'eta': '~20 min',
                    'lastUpdate': update,
                    'errors': []
                }
                mc['agents'].append(imgur_agent)
            else:
                imgur_agent['status'] = status
                imgur_agent['progress'] = progress
                imgur_agent['current'] = current
                imgur_agent['lastUpdate'] = update
            mc['lastUpdated'] = datetime.now().isoformat()
            with open(MISSION_CONTROL, 'w') as f:
                json.dump(mc, f, indent=2)
        except Exception as e:
            print(f"MC update failed: {e}")

    def add_msg(self, msg, t='info'):
        try:
            with open(MISSION_CONTROL) as f:
                mc = json.load(f)
            mc['messages'].insert(0, {'timestamp': datetime.now().isoformat(), 'from': 'bz2.0', 'type': t, 'message': msg})
            mc['messages'] = mc['messages'][:20]
            with open(MISSION_CONTROL, 'w') as f:
                json.dump(mc, f, indent=2)
        except: pass

    def fetch_page(self, url: str) -> str:
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
                'Accept': 'text/html,application/xhtml+xml,*/*'
            })
            with urllib.request.urlopen(req, timeout=30, context=ssl_context) as resp:
                return resp.read().decode('utf-8', errors='ignore')
        except Exception as e:
            self.stats['errors'].append(f"Fetch: {str(e)[:50]}")
            return ""

    def extract_imgur_posts(self, html: str, search_term: str) -> List[Dict]:
        """Extract imgur post data from search results"""
        posts = []

        # Find image hashes and titles
        # Imgur uses data attributes and JSON in the page
        hash_pattern = r'data-id="([a-zA-Z0-9]{5,10})"'
        hashes = re.findall(hash_pattern, html)

        # Also find titles
        title_pattern = r'alt="([^"]*(?:transform|before|after|progress|weight|loss|gain)[^"]*)"'
        titles = re.findall(title_pattern, html, re.IGNORECASE)

        # Extract direct image links
        img_pattern = r'(https://i\.imgur\.com/[a-zA-Z0-9]+\.(?:jpg|jpeg|png|gif))'
        images = list(set(re.findall(img_pattern, html, re.IGNORECASE)))

        for i, img_url in enumerate(images[:50]):  # Limit per search
            img_hash = img_url.split('/')[-1].split('.')[0]

            post = {
                'id': f"imgur_{img_hash}",
                'source': 'imgur',
                'title': titles[i] if i < len(titles) else f"Imgur transformation - {search_term}",
                'url': f"https://imgur.com/{img_hash}",
                'image_url': img_url,
                'search_term': search_term,
                'metadata': {'quality_score': 2},  # Basic score, no detailed metadata
                'scraped_at': datetime.now().isoformat()
            }
            posts.append(post)

        return posts

    def download_image(self, url: str, post_id: str) -> Optional[str]:
        try:
            ext = url.split('.')[-1].split('?')[0][:4]
            if ext not in ['jpg', 'jpeg', 'png', 'gif']:
                ext = 'jpg'

            filename = f"{post_id}.{ext}"
            filepath = IMAGES_DIR / filename

            if filepath.exists():
                return str(filepath.relative_to(BASE_DIR))

            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30, context=ssl_context) as resp:
                with open(filepath, 'wb') as f:
                    f.write(resp.read())

            self.stats['images_downloaded'] += 1
            return str(filepath.relative_to(BASE_DIR))
        except:
            return None

    def search_imgur(self, term: str) -> List[Dict]:
        """Search Imgur for a term"""
        print(f"  🔍 Searching: {term}")

        # Imgur search URL
        url = f"https://imgur.com/search?q={urllib.parse.quote(term)}"
        html = self.fetch_page(url)

        if not html:
            return []

        posts = self.extract_imgur_posts(html, term)

        # Download images
        for post in posts:
            local_img = self.download_image(post['image_url'], post['id'])
            post['local_image'] = local_img

            # Add to database if not exists
            if not any(p['id'] == post['id'] for p in self.database['posts']):
                self.database['posts'].append(post)
                self.database['stats']['total'] += 1
                self.database['stats']['by_source']['imgur'] = self.database['stats']['by_source'].get('imgur', 0) + 1
                self.stats['posts_found'] += 1

        print(f"    ✓ Found {len(posts)} images")
        return posts

    def run(self):
        print("🚀 PhysiqAI Imgur Scraper")
        print(f"📋 Searching {len(SEARCH_TERMS)} terms\n")

        self.update_mc('running', 0, '0 posts', 'Starting...')
        self.add_msg("🚀 Imgur scraper launched! Searching public galleries...", 'info')

        all_posts = []

        for i, term in enumerate(SEARCH_TERMS):
            progress = int((i / len(SEARCH_TERMS)) * 100)
            self.update_mc('running', progress, f"{self.stats['posts_found']} posts", f"Searching: {term}")

            posts = self.search_imgur(term)
            all_posts.extend(posts)

            self.save_database()
            time.sleep(2)  # Be nice

        self.update_mc('completed', 100, f"{self.stats['posts_found']} posts", 'Complete!')
        self.add_msg(f"🎉 Imgur scraping done! {self.stats['posts_found']} transformation images found", 'success')

        print(f"\n{'='*50}")
        print(f"📊 SUMMARY: {self.stats['posts_found']} posts, {self.stats['images_downloaded']} images")
        print(f"{'='*50}")

        return all_posts

# Need to import urllib.parse
import urllib.parse

if __name__ == "__main__":
    scraper = ImgurScraper()
    scraper.run()
