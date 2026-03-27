#!/usr/bin/env python3
"""
Test script for photo_fitter.py
Downloads a sample image and runs through the pipeline.
"""

import requests
from pathlib import Path
from photo_fitter import PhotoFittingPipeline

# Download a sample body photo (placeholder image service)
def download_sample_image():
    """Download a sample body photo for testing."""
    # Using placeholder - in production use actual body photos
    url = "https://via.placeholder.com/600x800/666/fff?text=Body+Photo"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        test_dir = Path(__file__).parent / 'test-photos'
        test_dir.mkdir(exist_ok=True)

        img_path = test_dir / 'sample_body.jpg'
        with open(img_path, 'wb') as f:
            f.write(response.content)

        print(f"Downloaded sample image to {img_path}")
        return img_path
    except Exception as e:
        print(f"Failed to download image: {e}")
        print("Creating local test image instead...")

        # Create a local test image
        from PIL import Image
        test_dir = Path(__file__).parent / 'test-photos'
        test_dir.mkdir(exist_ok=True)
        img_path = test_dir / 'sample_body.jpg'

        # Create a gradient image
        img = Image.new('RGB', (600, 800), color=(200, 200, 200))
        img.save(img_path)

        return img_path

def test_pipeline():
    """Test the full pipeline with a real image."""
    print("="*70)
    print("Photo-to-SMPL Pipeline Test")
    print("="*70)

    # Get test image
    img_path = download_sample_image()

    # Initialize pipeline
    print("\nInitializing pipeline...")
    pipeline = PhotoFittingPipeline()

    # Process the photo
    print(f"\nProcessing {img_path.name}...")
    result = pipeline.process_photo(
        image_input=str(img_path),
        user_id='test_user',
        photo_type='front'
    )

    # Print results
    print("\n" + "="*70)
    if result['success']:
        print("✅ PIPELINE SUCCESS")
        print("="*70)
        print(f"\nPhoto ID: {result['photo_id']}")
        print(f"Photo URL: {result['photo_url']}")
        print(f"\n📊 Detection Results:")
        print(f"  - Gender: {result['detection']['gender']} (confidence: {result['detection']['gender_confidence']:.1%})")
        print(f"  - Body Type: {result['detection']['body_type']}")
        if result['detection']['measurements']:
            m = result['detection']['measurements']
            print(f"  - Shoulder Width: {m['shoulder_width']:.1f} cm")
            print(f"  - Hip Width: {m['hip_width']:.1f} cm")
            print(f"  - Height Estimate: {m['height_estimate']:.1f} cm")
        print(f"\n🧬 SMPL Parameters:")
        betas = result['smpl_params']['betas']
        for i, beta in enumerate(betas):
            print(f"  β{i}: {beta:+.3f}")
        print(f"\n💾 Output Files:")
        print(f"  - Mesh: {result['mesh_path']}")
        print(f"  - Confidence: {result['confidence']:.1%}")
        print(f"  - Processing Time: {result['processing_time_ms']:.0f}ms")
    else:
        print("❌ PIPELINE FAILED")
        print("="*70)
        print(f"Error: {result['error']}")

    print("\n" + "="*70)
    return result['success']

if __name__ == "__main__":
    success = test_pipeline()
    exit(0 if success else 1)
