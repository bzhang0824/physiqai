#!/usr/bin/env python3
"""
PhysiqAI NHANES Downloader - NO EXTERNAL DEPENDENCIES
Downloads FREE body composition data from CDC
"""

import urllib.request
import json
import ssl
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data' / 'collected' / 'nhanes'
DATABASE_FILE = BASE_DIR / 'data' / 'collected' / 'database.json'
MISSION_CONTROL = BASE_DIR / 'mission-control.json'

DATA_DIR.mkdir(parents=True, exist_ok=True)
ssl_context = ssl.create_default_context()

# CDC NHANES datasets (all FREE)
DATASETS = {
    'BMX_L': ('https://wwwn.cdc.gov/Nchs/Nhanes/2021-2022/BMX_L.XPT', 'Body Measures 2021-2022', '~10K records'),
    'BMX_J': ('https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/BMX_J.XPT', 'Body Measures 2017-2018', '~9K records'),
    'BMX_I': ('https://wwwn.cdc.gov/Nchs/Nhanes/2015-2016/BMX_I.XPT', 'Body Measures 2015-2016', '~10K records'),
    'DEMO_L': ('https://wwwn.cdc.gov/Nchs/Nhanes/2021-2022/DEMO_L.XPT', 'Demographics 2021-2022', '~15K records'),
    'PAQ_L': ('https://wwwn.cdc.gov/Nchs/Nhanes/2021-2022/PAQ_L.XPT', 'Physical Activity 2021-2022', '~10K records'),
}

def update_mc(status, progress, current, update):
    try:
        with open(MISSION_CONTROL) as f:
            mc = json.load(f)
        for a in mc['agents']:
            if a['id'] == 'nhanes-download':
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

def run():
    print("🚀 PhysiqAI NHANES Downloader")
    print("💰 FREE government data from CDC\n")

    update_mc('running', 0, '0 files', 'Starting...')
    add_msg("🚀 NHANES downloader launched! Fetching CDC body composition data...", 'info')

    downloaded = []
    total_mb = 0

    for i, (key, (url, name, records)) in enumerate(DATASETS.items()):
        progress = int((i / len(DATASETS)) * 100)
        update_mc('running', progress, f"{len(downloaded)} files", f"Downloading {name}...")

        filepath = DATA_DIR / f"{key}.XPT"

        if filepath.exists():
            print(f"  ✓ {key} already exists")
            downloaded.append(key)
            continue

        try:
            print(f"  ⬇️ Downloading {name}...")
            req = urllib.request.Request(url, headers={'User-Agent': 'PhysiqAI/1.0'})
            with urllib.request.urlopen(req, timeout=120, context=ssl_context) as resp:
                with open(filepath, 'wb') as f:
                    f.write(resp.read())

            size_mb = filepath.stat().st_size / (1024 * 1024)
            total_mb += size_mb
            downloaded.append(key)
            print(f"  ✓ {key} downloaded ({size_mb:.1f} MB)")

        except Exception as e:
            print(f"  ❌ Failed: {e}")

    # Update database
    try:
        with open(DATABASE_FILE) as f:
            db = json.load(f)

        for key in downloaded:
            url, name, records = DATASETS[key]
            filepath = DATA_DIR / f"{key}.XPT"
            record = {
                'id': f"nhanes_{key}",
                'source': 'nhanes',
                'title': name,
                'file': str(filepath.relative_to(BASE_DIR)),
                'estimated_records': records,
                'size_mb': round(filepath.stat().st_size / (1024*1024), 2) if filepath.exists() else 0,
                'metadata': {'type': 'body_composition', 'quality_score': 5},
                'scraped_at': datetime.now().isoformat()
            }
            if not any(p['id'] == record['id'] for p in db['posts']):
                db['posts'].append(record)

        db['stats']['by_source']['nhanes'] = len(downloaded)
        db['lastUpdated'] = datetime.now().isoformat()

        with open(DATABASE_FILE, 'w') as f:
            json.dump(db, f, indent=2)
    except Exception as e:
        print(f"DB update failed: {e}")

    update_mc('completed', 100, f"{len(downloaded)} datasets ({total_mb:.1f} MB)", 'Complete!')
    add_msg(f"🎉 NHANES DONE! {len(downloaded)} datasets downloaded ({total_mb:.1f} MB). Includes body measures, demographics, physical activity.", 'success')

    print(f"\n{'='*50}")
    print(f"📊 SUMMARY: {len(downloaded)} files, {total_mb:.1f} MB total")
    print(f"{'='*50}")

if __name__ == "__main__":
    run()
