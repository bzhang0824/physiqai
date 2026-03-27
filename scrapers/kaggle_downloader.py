#!/usr/bin/env python3
"""
PhysiqAI Kaggle Dataset Downloader
Downloads body composition and fitness datasets from Kaggle
Uses direct API calls (no kaggle CLI needed)
"""

import urllib.request
import json
import os
import zipfile
from datetime import datetime
from pathlib import Path
from base64 import b64encode

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data' / 'kaggle'
DATABASE_FILE = BASE_DIR / 'data' / 'collected' / 'database.json'
MISSION_CONTROL = BASE_DIR / 'mission-control.json'

DATA_DIR.mkdir(parents=True, exist_ok=True)

# Kaggle credentials
KAGGLE_USERNAME = "brianzhang23"
KAGGLE_KEY = "KGAT_7823fab19c245575b4cf7a7c0c20fd12"

# Datasets to download (owner/dataset-name format)
DATASETS = [
    ("fedesoriano", "body-fat-prediction-dataset"),
    ("simonezappatini", "body-fat-extended-dataset"),
    ("simeondee", "body-fitness-exercises-and-body-measurement-data"),
    ("aakashjoshi123", "exercise-and-fitness-metrics-dataset"),
    ("mustafa20635", "fitness-exercises-using-bfp-and-bmi"),
]

class KaggleDownloader:
    def __init__(self):
        self.auth = b64encode(f"{KAGGLE_USERNAME}:{KAGGLE_KEY}".encode()).decode()
        self.stats = {'downloaded': 0, 'failed': 0}

    def update_mc(self, msg: str, status: str = 'running', progress: int = 50):
        try:
            with open(MISSION_CONTROL) as f:
                mc = json.load(f)

            # Add/update kaggle agent
            found = False
            for a in mc['agents']:
                if a['id'] == 'kaggle-downloader':
                    a['status'] = status
                    a['progress'] = progress
                    a['current'] = f"{self.stats['downloaded']} datasets"
                    a['lastUpdate'] = msg
                    found = True
                    break

            if not found:
                mc['agents'].insert(0, {
                    'id': 'kaggle-downloader',
                    'name': 'Kaggle Downloader',
                    'description': 'Downloading body composition datasets from Kaggle',
                    'status': status,
                    'progress': progress,
                    'target': f'{len(DATASETS)} datasets',
                    'current': f"{self.stats['downloaded']} datasets",
                    'eta': '~5 min',
                    'lastUpdate': msg,
                    'errors': []
                })

            mc['messages'].insert(0, {
                'timestamp': datetime.now().isoformat(),
                'from': 'bz2.0',
                'type': 'info',
                'message': f"[Kaggle] {msg}"
            })
            mc['messages'] = mc['messages'][:30]
            mc['lastUpdated'] = datetime.now().isoformat()

            with open(MISSION_CONTROL, 'w') as f:
                json.dump(mc, f, indent=2)
        except Exception as e:
            print(f"MC error: {e}")

    def download_dataset(self, owner: str, dataset: str) -> bool:
        """Download a Kaggle dataset using API"""
        print(f"\n📥 Downloading {owner}/{dataset}...")

        dataset_dir = DATA_DIR / dataset
        dataset_dir.mkdir(exist_ok=True)

        # Kaggle API endpoint
        url = f"https://www.kaggle.com/api/v1/datasets/download/{owner}/{dataset}"

        try:
            req = urllib.request.Request(url)
            req.add_header('Authorization', f'Basic {self.auth}')

            zip_path = dataset_dir / f"{dataset}.zip"

            with urllib.request.urlopen(req, timeout=120) as resp:
                with open(zip_path, 'wb') as f:
                    f.write(resp.read())

            # Extract zip
            print(f"  📦 Extracting...")
            with zipfile.ZipFile(zip_path, 'r') as z:
                z.extractall(dataset_dir)

            # Remove zip
            zip_path.unlink()

            # List files
            files = list(dataset_dir.glob('*'))
            print(f"  ✅ Downloaded: {[f.name for f in files]}")

            self.stats['downloaded'] += 1
            return True

        except Exception as e:
            print(f"  ❌ Failed: {e}")
            self.stats['failed'] += 1
            return False

    def update_database(self):
        """Add Kaggle datasets to main database"""
        try:
            with open(DATABASE_FILE) as f:
                db = json.load(f)

            for dataset_name in os.listdir(DATA_DIR):
                dataset_dir = DATA_DIR / dataset_name
                if not dataset_dir.is_dir():
                    continue

                # Find CSV files
                csvs = list(dataset_dir.glob('*.csv'))

                for csv_file in csvs:
                    record_id = f"kaggle_{dataset_name}_{csv_file.stem}"

                    if any(p['id'] == record_id for p in db['posts']):
                        continue

                    # Count rows in CSV
                    try:
                        with open(csv_file) as f:
                            rows = sum(1 for _ in f) - 1  # minus header
                    except:
                        rows = 0

                    record = {
                        'id': record_id,
                        'source': 'kaggle',
                        'title': f"Kaggle: {dataset_name} - {csv_file.name}",
                        'file': str(csv_file.relative_to(BASE_DIR)),
                        'rows': rows,
                        'metadata': {
                            'type': 'body_composition_data',
                            'quality_score': 5,  # High quality structured data
                            'dataset': dataset_name
                        },
                        'scraped_at': datetime.now().isoformat()
                    }

                    db['posts'].append(record)
                    print(f"  📊 Added {csv_file.name} ({rows} rows)")

            db['stats']['by_source']['kaggle'] = len([p for p in db['posts'] if p['source'] == 'kaggle'])
            db['lastUpdated'] = datetime.now().isoformat()

            with open(DATABASE_FILE, 'w') as f:
                json.dump(db, f, indent=2)

        except Exception as e:
            print(f"Database update error: {e}")

    def run(self):
        print("="*60)
        print("📊 PhysiqAI KAGGLE DATASET DOWNLOADER")
        print(f"📋 Downloading {len(DATASETS)} body composition datasets")
        print("="*60)

        self.update_mc("Starting Kaggle downloads...", 'running', 0)

        for i, (owner, dataset) in enumerate(DATASETS):
            progress = int((i / len(DATASETS)) * 100)
            self.update_mc(f"Downloading {dataset}...", 'running', progress)

            self.download_dataset(owner, dataset)

        # Update database
        self.update_database()

        self.update_mc(
            f"Done! {self.stats['downloaded']} datasets downloaded",
            'completed',
            100
        )

        print("\n" + "="*60)
        print("📊 KAGGLE DOWNLOAD COMPLETE!")
        print(f"  Downloaded: {self.stats['downloaded']}")
        print(f"  Failed: {self.stats['failed']}")
        print("="*60)

if __name__ == "__main__":
    downloader = KaggleDownloader()
    downloader.run()
