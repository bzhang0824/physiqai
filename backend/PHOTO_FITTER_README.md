# PhysiqAI Photo-to-SMPL Fitting Pipeline

Real photo-to-3D avatar fitting system that converts user photos into personalized SMPL body models.

## Overview

This pipeline provides a complete end-to-end system for:
1. **Photo Upload Handling** - Resize, store to Firebase/local storage
2. **Body Detection** - MediaPipe-based pose estimation, keypoints, silhouette
3. **SMPL Parameter Estimation** - Map photo features to 10 SMPL betas
4. **Mesh Generation** - Generate 3D body mesh from SMPL parameters
5. **Three.js Export** - Output mesh in web-compatible JSON format

## Features

- ✅ **Automatic Gender Detection** - Shoulder/hip ratio-based gender estimation
- ✅ **Body Type Classification** - slender, average, athletic, curvy, muscular, heavyset
- ✅ **10 SMPL Shape Parameters** - Full control over body proportions
- ✅ **Three.js Compatible Output** - Ready for web rendering
- ✅ **Firebase Integration** - Optional cloud storage support
- ✅ **Fallback Mode** - Works without MediaPipe or SMPL models

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Optional: Install MediaPipe for better body detection
pip install mediapipe opencv-python

# Optional: Install Firebase for cloud storage
pip install firebase-admin
```

## Usage

### Basic Usage

```python
from photo_fitter import PhotoFittingPipeline

# Initialize pipeline
pipeline = PhotoFittingPipeline()

# Process a photo
result = pipeline.process_photo(
    image_input='/path/to/photo.jpg',
    user_id='user_123',
    photo_type='front'
)

if result['success']:
    print(f"Detected Gender: {result['detection']['gender']}")
    print(f"Body Type: {result['detection']['body_type']}")
    print(f"SMPL Betas: {result['smpl_params']['betas']}")
    print(f"Mesh saved to: {result['mesh_path']}")
```

### With Firebase Storage

```python
firebase_config = {
    'storage_bucket': 'your-project.appspot.com',
    'credentials_path': '/path/to/serviceAccountKey.json'
}

pipeline = PhotoFittingPipeline(firebase_config=firebase_config)
result = pipeline.process_photo('/path/to/photo.jpg', user_id='user_123')
```

### Individual Components

```python
from photo_fitter import PhotoUploadHandler, BodyDetector, SMPLEstimator

# Upload handler
uploader = PhotoUploadHandler()
upload_result = uploader.upload_photo('photo.jpg', user_id='user_123')

# Body detection
detector = BodyDetector()
detection = detector.detect('photo.jpg')
print(f"Detected: {detection.gender}, Body type: {detection.measurements.body_type}")

# SMPL estimation
estimator = SMPLEstimator()
smpl_params = estimator.estimate(detection)
print(f"SMPL Betas: {smpl_params.betas}")
```

## SMPL Parameters Explained

The pipeline outputs 10 SMPL shape parameters (betas):

| Beta | Description | Range | Effect |
|------|-------------|-------|--------|
| β₀ | Overall body size | [-3, 3] | Weight/volume |
| β₁ | Height ratio | [-3, 3] | Height/weight proportion |
| β₂ | Upper/lower proportion | [-3, 3] | Torso vs legs |
| β₃ | Torso width | [-3, 3] | Shoulder/chest width |
| β₄ | Arm thickness | [-3, 3] | Arm muscle/fat |
| β₅ | Leg thickness | [-3, 3] | Leg muscle/fat |
| β₆ | Chest depth | [-3, 3] | Chest projection |
| β₇ | Hip width | [-3, 3] | Hip/buttock width |
| β₈ | Fine adjustment 1 | [-3, 3] | Subtle shape control |
| β₉ | Fine adjustment 2 | [-3, 3] | Subtle shape control |

## Body Type Templates

The pipeline uses body type templates as starting points:

- **Slender**: Lean, lightweight build (-1.5 β₀)
- **Average**: Neutral proportions (0.0 β₀)
- **Athletic**: Muscular but lean (+0.5 β₀)
- **Curvy**: Wider hips, narrower shoulders (+0.3 β₀)
- **Muscular**: Broad shoulders, thick limbs (+1.2 β₀)
- **Heavyset**: Larger overall frame (+1.8 β₀)

## Output Format

### Mesh JSON (Three.js BufferGeometry)

```json
{
  "metadata": {
    "version": 4.5,
    "type": "BufferGeometry",
    "generator": "PhysiqAI"
  },
  "type": "BufferGeometry",
  "data": {
    "attributes": {
      "position": {
        "itemSize": 3,
        "type": "Float32Array",
        "array": [...],
        "normalized": false
      },
      "normal": {
        "itemSize": 3,
        "type": "Float32Array",
        "array": [...],
        "normalized": false
      }
    },
    "index": {
      "type": "Uint32Array",
      "array": [...]
    }
  }
}
```

## Accuracy & Limitations

### Current Accuracy
- Gender detection: ~60-95% confidence (based on shoulder/hip ratio)
- Body type classification: Heuristic-based, reasonably accurate
- SMPL parameter estimation: Approximate, based on body type + measurements
- Overall: Better than generic avatars, but not perfect

### Limitations
- Single photo provides limited information
- Clothing can obscure body shape
- Pose affects perceived proportions
- No depth information from 2D photos
- Limited accuracy for extreme body types

### Future Improvements
- Multi-view photos for better accuracy
- Deep learning-based shape estimation
- Integration with SMPLify-X for optimization
- Clothing segmentation and removal
- Height/weight user input for calibration

## File Structure

```
backend/
├── photo_fitter.py      # Main pipeline
├── requirements.txt     # Python dependencies
└── README.md           # This file

storage/                # Generated (local storage mode)
├── photos/
│   └── {user_id}/
│       └── front/
│           └── *.jpg
└── meshes/
    └── *_mesh.json
```

## Testing

Run the demo:

```bash
python photo_fitter.py
```

This will:
1. Create a test image
2. Run through the full pipeline
3. Output results to console
4. Save mesh to storage/meshes/

## API Reference

### PhotoFittingPipeline

Main pipeline class combining all components.

**Methods:**
- `process_photo(image_input, user_id, photo_type='front')` - Full pipeline processing

**Parameters:**
- `image_input`: Path, bytes, or PIL Image
- `user_id`: User identifier string
- `photo_type`: 'front', 'side', or 'back'

**Returns:**
```python
{
    'success': bool,
    'photo_url': str,
    'photo_id': str,
    'user_id': str,
    'detection': {
        'success': bool,
        'gender': str,
        'gender_confidence': float,
        'body_type': str,
        'measurements': {...}
    },
    'smpl_params': {'betas': [...], 'pose': [...], ...},
    'mesh_url': str,
    'mesh_path': str,
    'processing_time_ms': float,
    'confidence': float
}
```

## Dependencies

### Required
- numpy
- Pillow

### Optional (Recommended)
- mediapipe - Better body detection
- opencv-python - Image processing
- firebase-admin - Cloud storage

## License

MIT License - PhysiqAI
