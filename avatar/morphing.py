#!/usr/bin/env python3
"""
Tier 1: 2D Photo Morphing MVP
Simple cross-fade GIF generator using PIL only (no numpy)
"""

import json
import argparse
from pathlib import Path
from PIL import Image
import sys

# Directories
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data/collected'
OUTPUT_DIR = BASE_DIR / 'avatar/morphs'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def split_before_after(image_path):
    """Split a side-by-side before/after image into two separate images."""
    img = Image.open(image_path).convert('RGB')
    width, height = img.size

    # Most progress pics are side-by-side (left=before, right=after)
    mid = width // 2

    before = img.crop((0, 0, mid, height))
    after = img.crop((mid, 0, width, height))

    return before, after


def create_morph_gif(before_path, after_path, output_path, steps=30, duration=80,
                     bounce=False, target_size=(512, 512)):
    """
    Create a morph GIF from two image paths.

    Args:
        before_path: Path to before image
        after_path: Path to after image (or None to split side-by-side)
        output_path: Where to save the GIF
        steps: Number of frames in the morph (default 30)
        duration: Milliseconds per frame (default 80ms)
        bounce: If True, animate before->after->before
        target_size: Resize images to this size
    """
    try:
        # Load images
        if after_path is None:
            # Split side-by-side image
            before, after = split_before_after(before_path)
        else:
            before = Image.open(before_path).convert('RGB')
            after = Image.open(after_path).convert('RGB')

        # Resize to target size
        before = before.resize(target_size, Image.Resampling.LANCZOS)
        after = after.resize(target_size, Image.Resampling.LANCZOS)

        # Generate cross-fade frames
        frames = []
        for i in range(steps + 1):
            alpha = i / steps
            blended = Image.blend(before, after, alpha)
            frames.append(blended)

        # Add bounce effect if requested
        if bounce:
            reverse_frames = frames[-2:0:-1]  # Exclude first and last
            frames.extend(reverse_frames)

        # Save as GIF
        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            duration=duration,
            loop=0,
            optimize=False  # Disable optimization for speed
        )

        print(f"✅ Created: {output_path.name} ({len(frames)} frames, {output_path.stat().st_size/1024:.1f} KB)")
        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def find_best_pairs(limit=10):
    """Find the best before/after pairs from the database."""
    db_path = DATA_DIR / 'database.json'

    with open(db_path) as f:
        db = json.load(f)

    candidates = []

    for post in db['posts']:
        if not post.get('local_image'):
            continue

        img_path = BASE_DIR / post['local_image']
        if not img_path.exists():
            continue

        metadata = post.get('metadata', {})
        quality = metadata.get('quality_score', 0)
        weight_change = metadata.get('weight_change')

        # Score based on quality and weight change
        score = quality * 10
        if weight_change:
            score += min(abs(weight_change) / 10, 50)

        candidates.append({
            'post': post,
            'path': img_path,
            'score': score,
            'quality': quality
        })

    candidates.sort(key=lambda x: x['score'], reverse=True)
    return candidates[:limit]


def generate_examples(limit=10):
    """Generate morph GIFs for the best pairs."""
    print("="*60)
    print("Tier 1: 2D Photo Morphing MVP")
    print("="*60)

    print("\n🔍 Finding best pairs...")
    best_pairs = find_best_pairs(limit)
    print(f"Found {len(best_pairs)} pairs\n")

    success = 0

    for i, pair in enumerate(best_pairs, 1):
        post = pair['post']
        img_path = pair['path']

        print(f"[{i}/{len(best_pairs)}] {post['title'][:45]}...")

        output_path = OUTPUT_DIR / f"morph_{i:02d}.gif"

        if create_morph_gif(
            before_path=img_path,
            after_path=None,
            output_path=output_path,
            steps=30,
            duration=80,
            target_size=(512, 512),
            bounce=True
        ):
            success += 1

    print("\n" + "="*60)
    print(f"✅ Generated {success}/{limit} morph GIFs")
    print(f"📁 Output: {OUTPUT_DIR}")
    print("="*60)

    return success


def main():
    parser = argparse.ArgumentParser(description='2D Photo Morphing MVP')
    parser.add_argument('--before', '-b', help='Before image path')
    parser.add_argument('--after', '-a', help='After image path (optional)')
    parser.add_argument('--output', '-o', default=str(OUTPUT_DIR / 'output.gif'), help='Output path')
    parser.add_argument('--steps', '-s', type=int, default=30, help='Frame count')
    parser.add_argument('--duration', '-d', type=int, default=80, help='Frame duration (ms)')
    parser.add_argument('--size', type=int, nargs=2, default=[512, 512], help='Size: w h')
    parser.add_argument('--bounce', action='store_true', help='Ping-pong animation')
    parser.add_argument('--examples', action='store_true', help='Generate 10 examples')

    args = parser.parse_args()

    if args.examples:
        generate_examples(10)
    elif args.before:
        create_morph_gif(
            before_path=args.before,
            after_path=args.after,
            output_path=args.output,
            steps=args.steps,
            duration=args.duration,
            target_size=tuple(args.size),
            bounce=args.bounce
        )
    else:
        parser.print_help()
        print("\nUsage examples:")
        print("  python morphing.py --examples")
        print("  python morphing.py -b before.jpg -a after.jpg -o out.gif")
        print("  python morphing.py -b sidebyside.jpg -o out.gif --bounce")


if __name__ == "__main__":
    main()
