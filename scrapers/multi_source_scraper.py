#!/usr/bin/env python3
"""
PhysiqAI MULTI-SOURCE SCRAPER
Scrapes transformation data from multiple platforms beyond Reddit
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
from html.parser import HTMLParser

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data' / 'collected'
IMAGES_DIR = DATA_DIR / 'images'
DATABASE_FILE = DATA_DIR / 'database.json'
MISSION_CONTROL = BASE_DIR / 'mission-control.json'

ssl_context = ssl.create_default_context()

class MultiSourceScraper:
    def __init__(self):
        self.database = self.load_database()
        self.seen_ids = set(p['id'] for p in self.database.get('posts', []))
        self.stats = {'total': 0, 'images': 0}

    def load_database(self) -> Dict:
        if DATABASE_FILE.exists():
            with open(DATABASE_FILE) as f:
                return json.load(f)
        return {'posts': [], 'stats': {'total': 0, 'by_source': {}, 'by_gender': {}}, 'lastUpdated': None}

    def save_database(self):
        self.database['lastUpdated'] = datetime.now().isoformat()
        self.database['stats']['total'] = len(self.database['posts'])
        with open(DATABASE_FILE, 'w') as f:
            json.dump(self.database, f, indent=2)

    def update_mc(self, source: str, status: str, progress: int, current: str, msg: str):
        try:
            with open(MISSION_CONTROL) as f:
                mc = json.load(f)

            # Add/update agent
            agent_id = f"{source.lower()}-scraper"
            found = False
            for a in mc['agents']:
                if a['id'] == agent_id:
                    a['status'] = status
                    a['progress'] = progress
                    a['current'] = current
                    a['lastUpdate'] = msg
                    found = True
                    break

            if not found:
                mc['agents'].append({
                    'id': agent_id,
                    'name': f'{source} Scraper',
                    'description': f'Collecting from {source}',
                    'status': status,
                    'progress': progress,
                    'target': '500+ posts',
                    'current': current,
                    'eta': '~15 min',
                    'lastUpdate': msg,
                    'errors': []
                })

            mc['messages'].insert(0, {
                'timestamp': datetime.now().isoformat(),
                'from': 'bz2.0',
                'type': 'info',
                'message': f"[{source}] {msg}"
            })
            mc['messages'] = mc['messages'][:30]
            mc['lastUpdated'] = datetime.now().isoformat()

            with open(MISSION_CONTROL, 'w') as f:
                json.dump(mc, f, indent=2)
        except Exception as e:
            print(f"MC error: {e}")

    def fetch(self, url: str, headers: Dict = None) -> str:
        try:
            h = headers or {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
            req = urllib.request.Request(url, headers=h)
            with urllib.request.urlopen(req, timeout=30, context=ssl_context) as resp:
                return resp.read().decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"  Fetch error: {e}")
            return ""

    def download_image(self, url: str, post_id: str, source: str) -> Optional[str]:
        try:
            img_dir = IMAGES_DIR / source
            img_dir.mkdir(parents=True, exist_ok=True)

            ext = url.split('.')[-1].split('?')[0][:4]
            if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
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

    def add_record(self, record: Dict):
        if record['id'] not in self.seen_ids:
            self.database['posts'].append(record)
            self.seen_ids.add(record['id'])
            self.stats['total'] += 1

            source = record.get('source', 'unknown')
            self.database['stats']['by_source'][source] = self.database['stats']['by_source'].get(source, 0) + 1

    # ==================== TUMBLR ====================
    def scrape_tumblr(self):
        """Scrape Tumblr fitness transformation tags"""
        print("\n📱 Scraping Tumblr...")
        self.update_mc('Tumblr', 'running', 0, '0 posts', 'Starting Tumblr scrape...')

        tags = ['fitness transformation', 'weight loss transformation', 'body transformation', 'before and after fitness']
        count = 0

        for tag in tags:
            url = f"https://www.tumblr.com/search/{urllib.parse.quote(tag)}"
            html = self.fetch(url)

            # Extract image URLs from Tumblr's format
            img_pattern = r'(https://\d+\.media\.tumblr\.com/[a-f0-9]+/[a-f0-9\-]+/s\d+x\d+/[a-f0-9]+\.(?:jpg|png|gif))'
            images = list(set(re.findall(img_pattern, html, re.I)))

            for i, img_url in enumerate(images[:30]):
                post_id = f"tumblr_{tag.replace(' ', '_')}_{i}"

                if post_id in self.seen_ids:
                    continue

                local_img = self.download_image(img_url, post_id, 'tumblr')

                record = {
                    'id': post_id,
                    'source': 'tumblr',
                    'title': f'Tumblr: {tag}',
                    'url': url,
                    'image_url': img_url,
                    'local_image': local_img,
                    'metadata': {'quality_score': 2, 'tag': tag},
                    'scraped_at': datetime.now().isoformat()
                }

                self.add_record(record)
                count += 1
                print(f"  ✓ Tumblr image {count}")

            time.sleep(2)

        self.update_mc('Tumblr', 'completed', 100, f'{count} posts', f'Done! {count} images')
        print(f"  ✅ Tumblr: {count} images")
        return count

    # ==================== FLICKR ====================
    def scrape_flickr(self):
        """Scrape Flickr fitness/transformation photos (public API)"""
        print("\n📷 Scraping Flickr...")
        self.update_mc('Flickr', 'running', 0, '0 posts', 'Starting Flickr scrape...')

        # Flickr public feed (no API key needed)
        tags = ['fitness transformation', 'before after fitness', 'weight loss progress', 'body transformation']
        count = 0

        for tag in tags:
            url = f"https://www.flickr.com/search/?text={urllib.parse.quote(tag)}&media=photos"
            html = self.fetch(url)

            # Extract image URLs
            img_pattern = r'(https://live\.staticflickr\.com/\d+/\d+_[a-f0-9]+(?:_[a-z])?\.(?:jpg|png))'
            images = list(set(re.findall(img_pattern, html, re.I)))

            for i, img_url in enumerate(images[:20]):
                post_id = f"flickr_{tag.replace(' ', '_')}_{i}"

                if post_id in self.seen_ids:
                    continue

                # Get larger version
                large_url = re.sub(r'_[a-z]\.', '_b.', img_url)
                local_img = self.download_image(large_url, post_id, 'flickr')

                record = {
                    'id': post_id,
                    'source': 'flickr',
                    'title': f'Flickr: {tag}',
                    'url': url,
                    'image_url': large_url,
                    'local_image': local_img,
                    'metadata': {'quality_score': 2, 'tag': tag},
                    'scraped_at': datetime.now().isoformat()
                }

                self.add_record(record)
                count += 1
                print(f"  ✓ Flickr image {count}")

            time.sleep(2)

        self.update_mc('Flickr', 'completed', 100, f'{count} posts', f'Done! {count} images')
        print(f"  ✅ Flickr: {count} images")
        return count

    # ==================== PINTEREST (Public) ====================
    def scrape_pinterest(self):
        """Scrape Pinterest transformation pins (public search)"""
        print("\n📌 Scraping Pinterest...")
        self.update_mc('Pinterest', 'running', 0, '0 posts', 'Starting Pinterest scrape...')

        queries = ['fitness transformation', 'weight loss before after', 'body transformation results']
        count = 0

        for query in queries:
            url = f"https://www.pinterest.com/search/pins/?q={urllib.parse.quote(query)}"
            html = self.fetch(url)

            # Pinterest image patterns
            img_patterns = [
                r'(https://i\.pinimg\.com/\d+x/[a-f0-9]+/[a-f0-9]+/[a-f0-9]+\.(?:jpg|png))',
                r'(https://i\.pinimg\.com/originals/[a-f0-9]+/[a-f0-9]+/[a-f0-9]+\.(?:jpg|png))'
            ]

            images = []
            for pattern in img_patterns:
                images.extend(re.findall(pattern, html, re.I))
            images = list(set(images))

            for i, img_url in enumerate(images[:25]):
                post_id = f"pinterest_{query.replace(' ', '_')}_{i}"

                if post_id in self.seen_ids:
                    continue

                local_img = self.download_image(img_url, post_id, 'pinterest')

                record = {
                    'id': post_id,
                    'source': 'pinterest',
                    'title': f'Pinterest: {query}',
                    'url': url,
                    'image_url': img_url,
                    'local_image': local_img,
                    'metadata': {'quality_score': 2, 'query': query},
                    'scraped_at': datetime.now().isoformat()
                }

                self.add_record(record)
                count += 1
                print(f"  ✓ Pinterest image {count}")

            time.sleep(3)

        self.update_mc('Pinterest', 'completed', 100, f'{count} posts', f'Done! {count} images')
        print(f"  ✅ Pinterest: {count} images")
        return count

    # ==================== UNSPLASH (Free API) ====================
    def scrape_unsplash(self):
        """Scrape Unsplash fitness photos (free, no API key for search page)"""
        print("\n🖼️ Scraping Unsplash...")
        self.update_mc('Unsplash', 'running', 0, '0 posts', 'Starting Unsplash scrape...')

        queries = ['fitness', 'gym workout', 'bodybuilding', 'weight training', 'athletic body']
        count = 0

        for query in queries:
            url = f"https://unsplash.com/s/photos/{urllib.parse.quote(query)}"
            html = self.fetch(url)

            # Unsplash image pattern
            img_pattern = r'(https://images\.unsplash\.com/photo-[a-f0-9\-]+\?[^"]+)'
            images = list(set(re.findall(img_pattern, html, re.I)))

            for i, img_url in enumerate(images[:20]):
                post_id = f"unsplash_{query.replace(' ', '_')}_{i}"

                if post_id in self.seen_ids:
                    continue

                # Get smaller version for storage
                clean_url = img_url.split('?')[0] + '?w=800&q=80'
                local_img = self.download_image(clean_url, post_id, 'unsplash')

                record = {
                    'id': post_id,
                    'source': 'unsplash',
                    'title': f'Unsplash: {query}',
                    'url': url,
                    'image_url': clean_url,
                    'local_image': local_img,
                    'metadata': {'quality_score': 3, 'query': query},  # Higher quality stock photos
                    'scraped_at': datetime.now().isoformat()
                }

                self.add_record(record)
                count += 1
                print(f"  ✓ Unsplash image {count}")

            time.sleep(2)

        self.update_mc('Unsplash', 'completed', 100, f'{count} posts', f'Done! {count} images')
        print(f"  ✅ Unsplash: {count} images")
        return count

    # ==================== PEXELS (Free stock) ====================
    def scrape_pexels(self):
        """Scrape Pexels fitness photos"""
        print("\n📸 Scraping Pexels...")
        self.update_mc('Pexels', 'running', 0, '0 posts', 'Starting Pexels scrape...')

        queries = ['fitness', 'gym', 'bodybuilder', 'workout', 'athletic']
        count = 0

        for query in queries:
            url = f"https://www.pexels.com/search/{urllib.parse.quote(query)}/"
            html = self.fetch(url)

            # Pexels image pattern
            img_pattern = r'(https://images\.pexels\.com/photos/\d+/[^"?]+\.(?:jpeg|jpg|png))'
            images = list(set(re.findall(img_pattern, html, re.I)))

            for i, img_url in enumerate(images[:20]):
                post_id = f"pexels_{query}_{i}"

                if post_id in self.seen_ids:
                    continue

                local_img = self.download_image(img_url, post_id, 'pexels')

                record = {
                    'id': post_id,
                    'source': 'pexels',
                    'title': f'Pexels: {query}',
                    'url': url,
                    'image_url': img_url,
                    'local_image': local_img,
                    'metadata': {'quality_score': 3, 'query': query},
                    'scraped_at': datetime.now().isoformat()
                }

                self.add_record(record)
                count += 1
                print(f"  ✓ Pexels image {count}")

            time.sleep(2)

        self.update_mc('Pexels', 'completed', 100, f'{count} posts', f'Done! {count} images')
        print(f"  ✅ Pexels: {count} images")
        return count

    def run(self):
        print("="*60)
        print("🌐 PhysiqAI MULTI-SOURCE SCRAPER")
        print("📋 Sources: Tumblr, Flickr, Pinterest, Unsplash, Pexels")
        print("="*60)

        results = {}

        # Run all scrapers
        results['tumblr'] = self.scrape_tumblr()
        self.save_database()

        results['flickr'] = self.scrape_flickr()
        self.save_database()

        results['pinterest'] = self.scrape_pinterest()
        self.save_database()

        results['unsplash'] = self.scrape_unsplash()
        self.save_database()

        results['pexels'] = self.scrape_pexels()
        self.save_database()

        # Summary
        total = sum(results.values())
        print("\n" + "="*60)
        print("📊 MULTI-SOURCE SCRAPE COMPLETE!")
        print("="*60)
        for source, count in results.items():
            print(f"  {source}: {count} images")
        print(f"\n  TOTAL: {total} new images")
        print(f"  Database now has: {len(self.database['posts'])} posts")
        print("="*60)

        return results

if __name__ == "__main__":
    scraper = MultiSourceScraper()
    scraper.run()
