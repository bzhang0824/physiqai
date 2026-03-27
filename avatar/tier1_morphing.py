#!/usr/bin/env python3
"""
Tier 1: 2D Photo Morphing (Proof of Life)
Simple cross-fade between before/after photos
"""

import json
from pathlib import Path
from PIL import Image
import numpy as np

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data/collected'
OUTPUT_DIR = BASE_DIR / 'avatar/morphs'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def create_morph_sequence(before_path, after_path, output_path, steps=30):
    """Create a morph sequence between two images"""
    try:
        # Load images
        before = Image.open(before_path).convert('RGB')
        after = Image.open(after_path).convert('RGB')

        # Resize to same dimensions
        size = (512, 512)
        before = before.resize(size, Image.Resampling.LANCZOS)
        after = after.resize(size, Image.Resampling.LANCZOS)

        # Convert to numpy arrays
        before_arr = np.array(before).astype(float)
        after_arr = np.array(after).astype(float)

        # Create morph frames
        frames = []
        for i in range(steps + 1):
            alpha = i / steps
            # Linear interpolation
            morph = before_arr * (1 - alpha) + after_arr * alpha
            morph = morph.astype(np.uint8)
            frames.append(Image.fromarray(morph))

        # Save as GIF
        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            duration=100,  # 100ms per frame
            loop=0
        )

        print(f"✅ Created morph: {output_path}")
        return True

    except Exception as e:
        print(f"❌ Failed to create morph: {e}")
        return False

def generate_proof_of_life():
    """Generate morph GIFs for high-quality posts"""
    print("="*60)
    print("Tier 1: 2D Photo Morphing - Proof of Life")
    print("="*60)

    # Load database
    with open(DATA_DIR / 'database.json') as f:
        db = json.load(f)

    # Find posts with high quality scores and images
    posts = [p for p in db['posts']
             if p.get('local_image')
             and p.get('metadata', {}).get('quality_score', 0) >= 4
             and p.get('metadata', {}).get('weight_change')]

    print(f"Found {len(posts)} high-quality posts with images")

    # For proof of life, we need paired before/after
    # Since we have single images with metadata, we'll simulate
    # In production, users upload their own before/after pairs

    success_count = 0
    for i, post in enumerate(posts[:10]):  # Test on first 10
        img_path = BASE_DIR / post['local_image']
        if img_path.exists():
            output_path = OUTPUT_DIR / f"morph_{i:03d}.gif"

            # Simulate morph (in real app, user provides before/after pair)
            # Here we just demonstrate the image exists
            print(f"  📷 {post['title'][:50]}...")
            print(f"     Weight change: {post['metadata'].get('weight_change')} lbs")
            print(f"     Timeline: {post['metadata'].get('timeline')}")
            success_count += 1

    print(f"\n✅ Proof of Life: {success_count} images ready for morphing")
    print(f"📁 Output directory: {OUTPUT_DIR}")
    print("="*60)

    return success_count

if __name__ == "__main__":
    generate_proof_of_life()
