#!/usr/bin/env python3
"""
Kaggle Dataset Downloader using API
"""

import requests
import json
import os
from pathlib import Path

# Load credentials
kaggle_dir = Path.home() / '.kaggle'
kaggle_json = kaggle_dir / 'kaggle.json'

with open(kaggle_json) as f:
    creds = json.load(f)

USERNAME = creds['username']
API_KEY = creds['key']

# Target datasets for body composition/fitness
TARGET_DATASETS = [
    # Obesity/weight classification
    "spittman1248/obesity-levels",
    # Body fat prediction
    "fedesoriano/body-fat-prediction-dataset",
    # Weight loss
    "shanegerous/weight-loss",
    # Fitness tracking
    "divyansh22/fitness-tracker-dataset",
    # Health metrics
    "uciml/breast-cancer-wisconsin-data",  # health classification
    # More general health
    "kumarajarshi/life-expectancy-who",
]

def download_dataset(dataset_slug):
    """Download a Kaggle dataset"""
    print(f"\n📥 Downloading: {dataset_slug}")

    try:
        # Kaggle API endpoint for dataset download
        url = f"https://www.kaggle.com/api/v1/datasets/download/{dataset_slug}"

        response = requests.get(
            url,
            auth=(USERNAME, API_KEY),
            timeout=60
        )

        if response.status_code == 200:
            # Save zip file
            dataset_name = dataset_slug.split('/')[-1]
            output_dir = Path('data/kaggle_datasets')
            output_dir.mkdir(parents=True, exist_ok=True)

            zip_path = output_dir / f"{dataset_name}.zip"
            with open(zip_path, 'wb') as f:
                f.write(response.content)

            print(f"  ✅ Saved: {zip_path} ({len(response.content)//1024} KB)")
            return True
        else:
            print(f"  ❌ Failed: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def list_fitness_datasets():
    """Search for fitness/body datasets on Kaggle"""
    print("🔍 Searching Kaggle for fitness/body composition datasets...")

    search_terms = [
        "body composition",
        "body fat",
        "weight loss",
        "fitness",
        "obesity",
        "anthropometric"
    ]

    datasets_found = []

    for term in search_terms:
        try:
            url = "https://www.kaggle.com/api/v1/datasets/list"
            params = {
                "search": term,
                "sortBy": "hottest",
                "pageSize": 10
            }

            response = requests.get(
                url,
                auth=(USERNAME, API_KEY),
                params=params,
                timeout=30
            )

            if response.status_code == 200:
                datasets = response.json()
                for ds in datasets:
                    datasets_found.append({
                        'ref': ds.get('ref'),
                        'title': ds.get('title'),
                        'size': ds.get('size'),
                        'downloadCount': ds.get('downloadCount')
                    })

        except Exception as e:
            print(f"Search error for '{term}': {e}")

    # Remove duplicates
    seen = set()
    unique = []
    for ds in datasets_found:
        if ds['ref'] not in seen:
            seen.add(ds['ref'])
            unique.append(ds)

    return unique

if __name__ == "__main__":
    print("="*60)
    print("KAGGLE DATASET DOWNLOADER")
    print(f"User: {USERNAME}")
    print("="*60)

    # Download target datasets
    successful = 0
    for dataset in TARGET_DATASETS:
        if download_dataset(dataset):
            successful += 1

    print(f"\n✅ Downloaded {successful}/{len(TARGET_DATASETS)} datasets")

    # List additional datasets found
    print("\n🔍 Searching for more fitness datasets...")
    found = list_fitness_datasets()

    print(f"\n📊 Found {len(found)} additional datasets:")
    for ds in found[:10]:  # Show top 10
        print(f"  - {ds['ref']} ({ds.get('downloadCount', 0)} downloads)")

    # Save list
    with open('data/kaggle_datasets/dataset_inventory.json', 'w') as f:
        json.dump(found, f, indent=2)

    print(f"\n💾 Inventory saved to: data/kaggle_datasets/dataset_inventory.json")
