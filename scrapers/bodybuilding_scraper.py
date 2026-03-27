#!/usr/bin/env python3
"""
PhysiqAI Bodybuilding.com Scraper
Collects transformation posts from BB.com forums
NO API KEY NEEDED - public forum scraping
"""

import requests
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import time
import urllib.request

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data' / 'collected'
IMAGES_DIR = DATA_DIR / 'images' / 'bodybuilding'
DATABASE_FILE = DATA_DIR / 'database.json'
MISSION_CONTROL = BASE_DIR / 'mission-control.json'

IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Transformation gallery URLs
BB_URLS = [
    'https://www.bodybuilding.com/fun/bbmainfit.htm',  # Main transformation gallery
    'https://www.bodybuilding.com/fun/fat-loss-transformations.html',
    'https://www.bodybuilding.com/fun/muscle-building-transformations.html',
]

class BodybuildingScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        })
        self.stats = {
            'pages_scraped': 0,
            'posts_found': 0,
            'images_downloaded': 0,
            'errors': []
        }

    def update_mission_control(self, status: str, progress: int, current: str, last_update: str):
        """Update mission control JSON"""
        try:
            with open(MISSION_CONTROL) as f:
                mc = json.load(f)

            for agent in mc['agents']:
                if agent['id'] == 'bodybuilding-scraper':
                    agent['status'] = status
                    agent['progress'] = progress
                    agent['current'] = current
                    agent['lastUpdate'] = last_update
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

            mc['messages'] = mc['messages'][:20]
            mc['lastUpdated'] = datetime.now().isoformat()

            with open(MISSION_CONTROL, 'w') as f:
                json.dump(mc, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not add message: {e}")

    def extract_transformation_data(self, html: str, url: str) -> List[Dict]:
        """Extract transformation data from page"""
        soup = BeautifulSoup(html, 'html.parser')
        transformations = []

        # Look for transformation cards/articles
        # BB.com structure varies, so we look for common patterns

        # Find all transformation story links
        story_links = soup.find_all('a', href=re.compile(r'transformation|before.*after', re.I))

        for link in story_links[:50]:  # Limit per page
            try:
                href = link.get('href', '')
                if not href.startswith('http'):
                    href = f"https://www.bodybuilding.com{href}"

                # Find associated image
                img = link.find('img') or link.find_parent().find('img')
                img_url = img.get('src', '') if img else None

                # Extract text for metadata
                text = link.get_text(strip=True)
                parent_text = link.find_parent().get_text(strip=True) if link.find_parent() else ''

                # Try to extract stats from text
                metadata = self.extract_metadata_from_text(text + ' ' + parent_text)

                if metadata or img_url:
                    transformations.append({
                        'url': href,
                        'title': text[:200],
                        'image_url': img_url,
                        'metadata': metadata
                    })

            except Exception as e:
                continue

        return transformations

    def extract_metadata_from_text(self, text: str) -> Optional[Dict]:
        """Extract weight/stats from text"""
        metadata = {}

        # Weight patterns
        weight_match = re.search(r'(\d{2,3})\s*(?:lbs?|pounds?)\s*(?:to|→|>|-)\s*(\d{2,3})', text, re.I)
        if weight_match:
            metadata['weight_before'] = int(weight_match.group(1))
            metadata['weight_after'] = int(weight_match.group(2))
            metadata['weight_change'] = metadata['weight_after'] - metadata['weight_before']

        # Age pattern
        age_match = re.search(r'age[:\s]+(\d{2})|(\d{2})\s*(?:year|yr)s?\s*old', text, re.I)
        if age_match:
            metadata['age'] = int(age_match.group(1) or age_match.group(2))

        # Gender
        if re.search(r'\b(?:male|man|guy|dude|bro)\b', text, re.I):
            metadata['gender'] = 'M'
        elif re.search(r'\b(?:female|woman|girl|lady)\b', text, re.I):
            metadata['gender'] = 'F'

        # Timeline
        time_match = re.search(r'(\d+)\s*(week|month|year)s?', text, re.I)
        if time_match:
            value = int(time_match.group(1))
            unit = time_match.group(2).lower()
            metadata['timeline'] = f"{value} {unit}s"
            multipliers = {'week': 7, 'month': 30, 'year': 365}
            metadata['timeline_days'] = value * multipliers.get(unit, 30)

        # Quality score
        score = sum([
            'weight_before' in metadata,
            'age' in metadata,
            'gender' in metadata,
            'timeline' in metadata
        ])
        metadata['quality_score'] = score

        return metadata if metadata else None

    def download_image(self, url: str, post_id: str) -> Optional[str]:
        """Download image and return local path"""
        try:
            if not url or not url.startswith('http'):
                return None

            ext = url.split('.')[-1].split('?')[0][:4]
            if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                ext = 'jpg'

            filename = f"bb_{post_id}.{ext}"
            filepath = IMAGES_DIR / filename

            if filepath.exists():
                return str(filepath.relative_to(BASE_DIR))

            urllib.request.urlretrieve(url, filepath)
            self.stats['images_downloaded'] += 1
            return str(filepath.relative_to(BASE_DIR))

        except Exception as e:
            self.stats['errors'].append(f"Image download: {str(e)[:50]}")
            return None

    def scrape_page(self, url: str) -> List[Dict]:
        """Scrape a single page"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            self.stats['pages_scraped'] += 1

            transformations = self.extract_transformation_data(response.text, url)

            # Download images and build records
            records = []
            for i, t in enumerate(transformations):
                local_img = None
                if t.get('image_url'):
                    local_img = self.download_image(t['image_url'], f"{self.stats['posts_found']}_{i}")

                record = {
                    'id': f"bb_{self.stats['posts_found']}_{i}",
                    'source': 'bodybuilding.com',
                    'title': t.get('title', ''),
                    'url': t.get('url', ''),
                    'image_url': t.get('image_url'),
                    'local_image': local_img,
                    'metadata': t.get('metadata', {}),
                    'scraped_at': datetime.now().isoformat()
                }
                records.append(record)
                self.stats['posts_found'] += 1

            return records

        except Exception as e:
            self.stats['errors'].append(f"Page scrape {url}: {str(e)[:50]}")
            return []

    def run(self):
        """Main scraping workflow"""
        print("🚀 PhysiqAI Bodybuilding.com Scraper")
        print(f"📋 Target: Transformation galleries\n")

        self.update_mission_control('running', 0, '0 posts', 'Starting scrape...')
        self.add_message("🚀 Bodybuilding.com scraper launched! Targeting transformation galleries...", 'info')

        all_records = []
        total_urls = len(BB_URLS)

        for i, url in enumerate(BB_URLS):
            progress = int((i / total_urls) * 100)
            self.update_mission_control(
                'running', progress,
                f"{self.stats['posts_found']} posts found",
                f"Scraping page {i+1}/{total_urls}"
            )

            print(f"🔍 Scraping: {url}")
            records = self.scrape_page(url)
            all_records.extend(records)

            time.sleep(2)  # Be respectful

        # Update database
        try:
            with open(DATABASE_FILE) as f:
                db = json.load(f)

            for record in all_records:
                if not any(p.get('id') == record['id'] for p in db['posts']):
                    db['posts'].append(record)

            db['stats']['by_source']['bodybuilding'] = len(all_records)
            db['lastUpdated'] = datetime.now().isoformat()

            with open(DATABASE_FILE, 'w') as f:
                json.dump(db, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not update database: {e}")

        # Final update
        self.update_mission_control(
            'completed', 100,
            f"{len(all_records)} posts total",
            'Scraping complete!'
        )

        self.add_message(
            f"🎉 Bodybuilding.com scraping COMPLETE! {len(all_records)} transformation posts found. "
            f"Images downloaded: {self.stats['images_downloaded']}",
            'success'
        )

        # Summary
        print("\n" + "="*50)
        print("📊 SCRAPING SUMMARY")
        print("="*50)
        print(f"Pages scraped: {self.stats['pages_scraped']}")
        print(f"Posts found: {self.stats['posts_found']}")
        print(f"Images downloaded: {self.stats['images_downloaded']}")
        print(f"Errors: {len(self.stats['errors'])}")
        print("="*50)

        return all_records


if __name__ == "__main__":
    scraper = BodybuildingScraper()
    scraper.run()
