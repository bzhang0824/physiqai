#!/usr/bin/env python3
"""
PhysiqAI Bodybuilding.com Scraper - NO EXTERNAL DEPENDENCIES
Uses HTML parsing with regex (no BeautifulSoup needed)
"""

import urllib.request
import urllib.error
import json
import re
import ssl
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data' / 'collected'
IMAGES_DIR = DATA_DIR / 'images' / 'bodybuilding'
DATABASE_FILE = DATA_DIR / 'database.json'
MISSION_CONTROL = BASE_DIR / 'mission-control.json'

IMAGES_DIR.mkdir(parents=True, exist_ok=True)
ssl_context = ssl.create_default_context()

# Transformation pages to scrape
PAGES = [
    'https://www.bodybuilding.com/fun/bbmainfit.htm',
    'https://www.bodybuilding.com/fun/fat-loss-transformations.html',
    'https://www.bodybuilding.com/fun/moretrans.htm',
    'https://www.bodybuilding.com/fun/bbfemtrans.htm',
]

def update_mc(status, progress, current, update):
    try:
        with open(MISSION_CONTROL) as f:
            mc = json.load(f)
        for a in mc['agents']:
            if a['id'] == 'bodybuilding-scraper':
                a['status'], a['progress'], a['current'], a['lastUpdate'] = status, progress, current, update
        mc['lastUpdated'] = datetime.now().isoformat()
        with open(MISSION_CONTROL, 'w') as f:
            json.dump(mc, f, indent=2)
    except: pass

def add_msg(msg, t='info'):
    try:
        with open(MISSION_CONTROL) as f:
            mc = json.load(f)
        mc['messages'].insert(0, {'timestamp': datetime.now().isoformat(), 'from': 'bz2.0', 'type': t, 'message': msg})
        mc['messages'] = mc['messages'][:20]
        mc['lastUpdated'] = datetime.now().isoformat()
        with open(MISSION_CONTROL, 'w') as f:
            json.dump(mc, f, indent=2)
    except: pass

def fetch_page(url: str) -> str:
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })
        with urllib.request.urlopen(req, timeout=30, context=ssl_context) as resp:
            return resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"  ❌ Fetch failed: {e}")
        return ""

def extract_links_and_images(html: str, base_url: str) -> List[Dict]:
    """Extract transformation links and images using regex"""
    results = []

    # Find all links with "transformation" or "before" in them
    link_pattern = r'<a[^>]+href=["\']([^"\']+(?:transform|before|after|story)[^"\']*)["\'][^>]*>(.*?)</a>'

    for match in re.finditer(link_pattern, html, re.IGNORECASE | re.DOTALL):
        href = match.group(1)
        text = re.sub(r'<[^>]+>', '', match.group(2)).strip()

        # Make absolute URL
        if href.startswith('/'):
            href = 'https://www.bodybuilding.com' + href
        elif not href.startswith('http'):
            href = base_url.rsplit('/', 1)[0] + '/' + href

        results.append({'url': href, 'title': text[:200]})

    # Also find images near transformation content
    img_pattern = r'<img[^>]+src=["\']([^"\']+\.(?:jpg|jpeg|png|gif))["\']'
    images = re.findall(img_pattern, html, re.IGNORECASE)

    # Associate images with results
    for i, r in enumerate(results[:20]):  # Limit
        if i < len(images):
            img_url = images[i]
            if img_url.startswith('/'):
                img_url = 'https://www.bodybuilding.com' + img_url
            r['image_url'] = img_url

    return results[:50]  # Limit per page

def extract_metadata(text: str) -> Dict:
    """Extract weight/stats from text"""
    metadata = {}

    # Weight
    weight_match = re.search(r'(\d{2,3})\s*(?:lbs?|pounds?)?\s*(?:to|→|>|-)\s*(\d{2,3})', text, re.I)
    if weight_match:
        metadata['weight_before'] = int(weight_match.group(1))
        metadata['weight_after'] = int(weight_match.group(2))
        metadata['weight_change'] = metadata['weight_after'] - metadata['weight_before']

    # Gender hints
    if re.search(r'\b(?:male|man|guy|his)\b', text, re.I):
        metadata['gender'] = 'M'
    elif re.search(r'\b(?:female|woman|girl|her|she)\b', text, re.I):
        metadata['gender'] = 'F'

    # Timeline
    time_match = re.search(r'(\d+)\s*(week|month|year)s?', text, re.I)
    if time_match:
        val = int(time_match.group(1))
        unit = time_match.group(2).lower()
        metadata['timeline'] = f"{val} {unit}s"
        metadata['timeline_days'] = val * {'week': 7, 'month': 30, 'year': 365}.get(unit, 30)

    metadata['quality_score'] = sum([1 for k in ['weight_before', 'gender', 'timeline'] if k in metadata]) + 1

    return metadata

def download_image(url: str, idx: int) -> Optional[str]:
    try:
        if not url.startswith('http'):
            return None

        ext = url.split('.')[-1].split('?')[0][:4]
        if ext not in ['jpg', 'jpeg', 'png', 'gif']:
            ext = 'jpg'

        filename = f"bb_{idx}.{ext}"
        filepath = IMAGES_DIR / filename

        if filepath.exists():
            return str(filepath.relative_to(BASE_DIR))

        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30, context=ssl_context) as resp:
            with open(filepath, 'wb') as f:
                f.write(resp.read())

        return str(filepath.relative_to(BASE_DIR))
    except:
        return None

def run():
    print("🚀 PhysiqAI Bodybuilding.com Scraper")
    print(f"📋 Targeting {len(PAGES)} transformation pages\n")

    update_mc('running', 0, '0 posts', 'Starting...')
    add_msg("🚀 Bodybuilding.com scraper launched!", 'info')

    all_records = []
    img_count = 0

    for i, page_url in enumerate(PAGES):
        progress = int((i / len(PAGES)) * 100)
        update_mc('running', progress, f"{len(all_records)} posts", f"Scraping page {i+1}/{len(PAGES)}")

        print(f"🔍 Scraping: {page_url}")
        html = fetch_page(page_url)

        if not html:
            continue

        links = extract_links_and_images(html, page_url)

        for item in links:
            # Download image if available
            local_img = None
            if item.get('image_url'):
                local_img = download_image(item['image_url'], img_count)
                if local_img:
                    img_count += 1

            record = {
                'id': f"bb_{len(all_records)}",
                'source': 'bodybuilding',
                'title': item.get('title', 'Transformation'),
                'url': item.get('url', ''),
                'image_url': item.get('image_url'),
                'local_image': local_img,
                'metadata': extract_metadata(item.get('title', '')),
                'scraped_at': datetime.now().isoformat()
            }
            all_records.append(record)

        print(f"  ✓ Found {len(links)} transformation links")
        time.sleep(2)  # Be nice

    # Update database
    try:
        with open(DATABASE_FILE) as f:
            db = json.load(f)

        for record in all_records:
            if not any(p['id'] == record['id'] for p in db['posts']):
                db['posts'].append(record)

        db['stats']['by_source']['bodybuilding'] = len(all_records)
        db['lastUpdated'] = datetime.now().isoformat()

        with open(DATABASE_FILE, 'w') as f:
            json.dump(db, f, indent=2)
    except Exception as e:
        print(f"DB update failed: {e}")

    update_mc('completed', 100, f"{len(all_records)} posts", 'Complete!')
    add_msg(f"🎉 Bodybuilding.com DONE! {len(all_records)} transformation posts found, {img_count} images downloaded.", 'success')

    print(f"\n{'='*50}")
    print(f"📊 SUMMARY: {len(all_records)} posts, {img_count} images")
    print(f"{'='*50}")

if __name__ == "__main__":
    run()
