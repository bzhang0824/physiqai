#!/usr/bin/env python3
"""
PhysiqAI ML Training Pipeline - Initial Setup
Prepares data for body transformation model training
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'
PROCESSED_DIR = DATA_DIR / 'processed'
MODELS_DIR = BASE_DIR / 'models'
PROCESSED_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)

def analyze_dataset():
    """Analyze current data quality"""
    with open(DATA_DIR / 'collected/database.json') as f:
        db = json.load(f)

    posts = db['posts']

    # Quality metrics
    with_images = sum(1 for p in posts if p.get('local_image'))
    with_gender = sum(1 for p in posts if p.get('metadata', {}).get('gender'))
    with_weight = sum(1 for p in posts if p.get('metadata', {}).get('weight_change'))
    with_timeline = sum(1 for p in posts if p.get('metadata', {}).get('timeline'))

    high_quality = sum(1 for p in posts if p.get('metadata', {}).get('quality_score', 0) >= 4)

    print("="*60)
    print("📊 DATASET QUALITY ANALYSIS")
    print("="*60)
    print(f"Total posts: {len(posts)}")
    print(f"With images: {with_images} ({with_images/len(posts)*100:.1f}%)")
    print(f"With gender: {with_gender} ({with_gender/len(posts)*100:.1f}%)")
    print(f"With weight data: {with_weight} ({with_weight/len(posts)*100:.1f}%)")
    print(f"With timeline: {with_timeline} ({with_timeline/len(posts)*100:.1f}%)")
    print(f"High quality (4+): {high_quality} ({high_quality/len(posts)*100:.1f}%)")
    print("="*60)

    return {
        'total': len(posts),
        'with_images': with_images,
        'with_gender': with_gender,
        'with_weight': with_weight,
        'high_quality': high_quality
    }

def create_train_val_split():
    """Create train/val/test splits"""
    with open(DATA_DIR / 'collected/database.json') as f:
        db = json.load(f)

    # Filter for posts with images
    posts = [p for p in db['posts'] if p.get('local_image')]

    # Split: 70% train, 15% val, 15% test
    import random
    random.seed(42)
    random.shuffle(posts)

    n = len(posts)
    train_end = int(n * 0.7)
    val_end = int(n * 0.85)

    splits = {
        'train': posts[:train_end],
        'val': posts[train_end:val_end],
        'test': posts[val_end:]
    }

    # Save splits
    for split_name, split_posts in splits.items():
        with open(PROCESSED_DIR / f'{split_name}.json', 'w') as f:
            json.dump(split_posts, f, indent=2)
        print(f"  {split_name}: {len(split_posts)} posts")

    return splits

def write_training_config():
    """Write initial training config"""
    config = {
        'model': {
            'name': 'BodyTransformerNet',
            'architecture': 'CNN + LSTM',
            'input_size': [224, 224, 3],
            'output': 'body_composition_vector'
        },
        'training': {
            'batch_size': 32,
            'epochs': 100,
            'learning_rate': 0.001,
            'optimizer': 'Adam',
            'loss': 'MSE'
        },
        'data': {
            'augmentation': ['flip', 'rotate', 'brightness'],
            'normalize': True,
            'cache_images': True
        },
        'hardware': {
            'gpu_required': '8GB+ VRAM',
            'estimated_training_time': '12-24 hours',
            'checkpoint_interval': 'every 10 epochs'
        }
    }

    with open(MODELS_DIR / 'config.json', 'w') as f:
        json.dump(config, f, indent=2)

    print("\n" + "="*60)
    print("🧠 TRAINING CONFIG")
    print("="*60)
    print(f"Architecture: {config['model']['architecture']}")
    print(f"Input: {config['model']['input_size']}")
    print(f"Batch size: {config['training']['batch_size']}")
    print(f"GPU Required: {config['hardware']['gpu_required']}")
    print(f"Est. training time: {config['hardware']['estimated_training_time']}")
    print("="*60)

def main():
    print("🚀 PhysiqAI ML Pipeline Setup\n")

    # Analyze dataset
    stats = analyze_dataset()

    # Create splits
    print("\n📁 Creating train/val/test splits...")
    splits = create_train_val_split()

    # Write config
    write_training_config()

    # Summary
    print("\n" + "="*60)
    print("✅ PIPELINE READY")
    print("="*60)
    print(f"✓ Processed {stats['with_images']} images")
    print(f"✓ Created {len(splits['train'])} train / {len(splits['val'])} val / {len(splits['test'])} test")
    print(f"✓ Config saved to models/config.json")
    print("\nNext steps:")
    print("1. Install PyTorch/TensorFlow")
    print("2. Implement BodyTransformerNet architecture")
    print("3. Start training")
    print("="*60)

if __name__ == "__main__":
    main()
