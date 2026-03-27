#!/usr/bin/env python3
"""Female-focused Reddit scraper for better gender balance"""
import urllib.request, json, re, ssl, time
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent.parent
IMAGES = BASE / 'data/collected/images/reddit_female'
DB = BASE / 'data/collected/database.json'
IMAGES.mkdir(parents=True, exist_ok=True)
ssl_context = ssl.create_default_context()

FEMALE_SUBS = ['xxfitness', 'StrongCurves', 'loseit', '1200isplenty', 'intermittentfasting', 'fasting', 'progresspics']

class FemaleScraper:
    def __init__(self):
        with open(DB) as f:
            self.db = json.load(f)
        self.seen = set(p['id'] for p in self.db['posts'])
        self.new = 0

    def save(self):
        self.db['lastUpdated'] = datetime.now().isoformat()
        with open(DB, 'w') as f:
            json.dump(self.db, f, indent=2)

    def extract(self, title):
        meta = {}
        if re.search(r'\b([MF])[/\s]', title, re.I):
            meta['gender'] = re.search(r'\b([MF])[/\s]', title, re.I).group(1).upper()
        if re.search(r'[/\s](\d{2})[/\s]', title):
            meta['age'] = int(re.search(r'[/\s](\d{2})[/\s]', title).group(1))
        h = re.search(r"(\d+)'(\d+)\"?", title)
        if h:
            meta['height_cm'] = round((int(h.group(1))*30.48) + (int(h.group(2))*2.54))
        w = re.search(r'(\d{2,3})\s*(?:lbs?|pounds?)?\s*[>\-→to]+\s*(\d{2,3})', title, re.I)
        if w:
            meta['weight_before'], meta['weight_after'] = int(w.group(1)), int(w.group(2))
            meta['weight_change'] = meta['weight_after'] - meta['weight_before']
        for p,u,m in [(r'(\d+)\s*months?', 'months', 30), (r'(\d+)\s*years?', 'years', 365)]:
            t = re.search(p, title, re.I)
            if t:
                meta['timeline'], meta['timeline_days'] = f"{t.group(1)} {u}", int(t.group(1))*m
                break
        meta['quality_score'] = sum([1 for k in ['gender','age','height_cm','weight_before','timeline'] if k in meta])
        return meta if meta.get('gender') == 'F' or meta.get('quality_score',0) >= 2 else None

    def get_img(self, post):
        url = post.get('url', '') or post.get('url_overridden_by_dest', '')
        if any(url.lower().endswith(e) for e in ['.jpg','.jpeg','.png']):
            return url
        if 'imgur.com' in url and '/a/' not in url:
            return f"https://i.imgur.com/{url.rstrip('/').split('/')[-1].split('.')[0]}.jpg"
        preview = post.get('preview', {})
        if preview and 'images' in preview:
            try:
                return preview['images'][0]['source']['url'].replace('&amp;','&')
            except:
                pass
        return None

    def download(self, url, pid):
        try:
            ext = url.split('.')[-1].split('?')[0][:4]
            if ext not in ['jpg','jpeg','png']: ext = 'jpg'
            filepath = IMAGES / f"female_{pid}.{ext}"
            if filepath.exists():
                return str(filepath.relative_to(BASE))
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30, context=ssl_context) as r:
                with open(filepath, 'wb') as f:
                    f.write(r.read())
            return str(filepath.relative_to(BASE))
        except:
            return None

    def fetch_json(self, url):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'PhysiqAI/2.0'})
            with urllib.request.urlopen(req, timeout=30, context=ssl_context) as r:
                return json.loads(r.read().decode('utf-8'))
        except:
            return None

    def scrape_sub(self, sub, limit=500):
        print(f"\n🔍 r/{sub}")
        url = f"https://www.reddit.com/r/{sub}/top.json?t=all&limit=100"
        count, after, pages = 0, None, 0
        max_pages = (limit // 100) + 1

        while pages < max_pages:
            data = self.fetch_json(url + (f"&after={after}" if after else ""))
            if not data or 'data' not in data:
                break
            posts = data['data'].get('children', [])
            if not posts:
                break

            for item in posts:
                post = item.get('data', {})
                pid = f"reddit_f_{post.get('id', '')}"
                if pid in self.seen or post.get('score', 0) < 30:
                    continue

                title = post.get('title', '')
                meta = self.extract(title)
                if not meta:
                    continue

                img_url = self.get_img(post)
                local_img = self.download(img_url, post.get('id', '')) if img_url else None

                record = {
                    'id': pid, 'source': 'reddit', 'subreddit': sub, 'title': title,
                    'url': post.get('url', ''), 'permalink': f"https://reddit.com{post.get('permalink', '')}",
                    'image_url': img_url, 'local_image': local_img,
                    'score': post.get('score', 0), 'metadata': meta,
                    'scraped_at': datetime.now().isoformat()
                }

                self.db['posts'].append(record)
                self.seen.add(pid)
                self.new += 1
                gender = meta.get('gender', 'unknown')
                self.db['stats']['by_gender'][gender] = self.db['stats']['by_gender'].get(gender, 0) + 1
                print(f"  ✓ {title[:50]}...")

            after = data['data'].get('after')
            if not after:
                break
            pages += 1
            time.sleep(1)

        print(f"  ✅ r/{sub}: {count} posts")
        return count

    def run(self):
        print("="*60)
        print("👩 Female-Focused Reddit Scraper")
        print("="*60)

        for sub in FEMALE_SUBS:
            self.scrape_sub(sub, 500)
            self.save()

        total = len(self.db['posts'])
        print(f"\n✅ DONE! {self.new} new female posts. Total: {total}")
        print(f"Gender: {self.db['stats']['by_gender']}")

if __name__ == "__main__":
    FemaleScraper().run()
