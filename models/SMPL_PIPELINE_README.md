# SMPL Pipeline for PhysiqAI

Complete SMPL (Skinned Multi-Person Linear) model integration for body shape estimation and 3D mesh generation.

## Overview

This pipeline provides:
1. **SMPL Model Loading** - Load male/female SMPL models
2. **Photo → SMPL Parameters** - Estimate body shape from photos
3. **Measurements → SMPL Parameters** - Convert height/weight to body shape
4. **Mesh Generation** - Generate 3D body meshes
5. **Three.js Export** - Export to web-compatible format
6. **API Endpoints** - REST API for integration

## Files

```
models/
├── smpl_pipeline.py    # Main pipeline implementation
├── smpl_api.py         # FastAPI endpoints
├── convert_smpl.py     # Convert .pkl to .npz format
└── smpl/
    ├── smpl_female.npz  # Female SMPL model (converted)
    ├── smpl_male.npz    # Male SMPL model (converted)
    ├── basicModel_f_lbs_10_207_0_v1.0.0.pkl  # Source female model
    └── basicmodel_m_lbs_10_207_0_v1.0.0.pkl  # Source male model
```

## Quick Start

### Run Demo
```bash
cd /home/clawd/.openclaw/workspace/projects/physiqai/models
python3 smpl_pipeline.py
```

### Test on Sample Photos
```bash
python3 smpl_pipeline.py --test-photos
```

### Run API Server
```bash
# Install dependencies
pip install fastapi uvicorn python-multipart

# Start server
python3 smpl_api.py
```

## API Endpoints

### 1. Photo → SMPL Parameters
```bash
curl -X POST "http://localhost:8000/api/v1/photo-to-smpl" \
  -F "photo=@/path/to/photo.jpg" \
  -F "gender=male"
```

Response:
```json
{
  "success": true,
  "params": {
    "betas": [0.1, 0.2, -0.1, ...],
    "pose": [0, 0, 0, ...],
    "trans": [0, 0, 0],
    "gender": "male"
  },
  "message": "Photo processed successfully"
}
```

### 2. Measurements → SMPL Parameters
```bash
curl -X POST "http://localhost:8000/api/v1/measurements-to-smpl" \
  -H "Content-Type: application/json" \
  -d '{"height_cm": 175, "weight_kg": 70, "gender": "male"}'
```

### 3. SMPL → Mesh
```bash
curl -X POST "http://localhost:8000/api/v1/smpl-to-mesh" \
  -H "Content-Type: application/json" \
  -d '{
    "betas": [0.1, 0.2, -0.1, 0, 0, 0, 0, 0, 0, 0],
    "pose": [0, 0, 0, ...],
    "trans": [0, 0, 0],
    "gender": "male"
  }'
```

### 4. SMPL → Three.js JSON
```bash
curl -X POST "http://localhost:8000/api/v1/smpl-to-threejs" \
  -H "Content-Type: application/json" \
  -d '{
    "betas": [0.1, 0.2, -0.1, 0, 0, 0, 0, 0, 0, 0],
    "pose": [0, 0, 0, ...],
    "trans": [0, 0, 0],
    "gender": "male"
  }'
```

## Python API

### Basic Usage
```python
from smpl_pipeline import SMPLPipeline, SMPLParams

# Initialize pipeline
pipeline = SMPLPipeline()

# From measurements
params = pipeline.measurements_to_params(
    height_cm=175,
    weight_kg=70,
    gender='male'
)

# Generate mesh
mesh = pipeline.params_to_mesh(params)

# Export to Three.js JSON
pipeline.export_threejs(mesh, 'output.json')
```

### Advanced: Custom Shape Parameters
```python
import numpy as np

# Create custom SMPL parameters
params = SMPLParams(
    betas=np.array([0.5, -0.3, 0.2, 0, 0, 0, 0, 0, 0, 0]),
    pose=np.zeros(72),  # T-pose
    trans=np.zeros(3),
    gender='female'
)

# Generate mesh
mesh = pipeline.params_to_mesh(params)

# Access vertices and faces
vertices = mesh['vertices']  # (6890, 3)
faces = mesh['faces']        # (13776, 3)
```

## SMPL Parameters

### Shape Parameters (betas)
- 10-dimensional vector
- Controls body proportions
- β₀: Overall body size
- β₁: Height-weight ratio
- β₂: Upper/lower body proportion
- β₃: Torso width
- β₄: Arm thickness
- β₅: Leg thickness
- β₆: Chest depth
- β₇: Hip width
- β₈-β₉: Fine adjustments

### Pose Parameters (pose)
- 72-dimensional vector (24 joints × 3 axis-angle rotations)
- Controls body pose/articulation
- Default: T-pose (all zeros)

## Output Formats

### Three.js BufferGeometry JSON
Compatible with Three.js `BufferGeometryLoader`:
```javascript
const loader = new THREE.BufferGeometryLoader();
const geometry = loader.load('smpl_output.json');
const material = new THREE.MeshNormalMaterial();
const mesh = new THREE.Mesh(geometry, material);
scene.add(mesh);
```

### OBJ Format
Standard Wavefront OBJ file with vertices and faces.

## Model Details

### SMPL Model
- **Vertices**: 6890
- **Faces**: 13776
- **Joints**: 24
- **Shape Parameters**: 10 (betas)
- **Pose Parameters**: 72 (24 joints × 3 rotations)

### Models Included
- Female SMPL model
- Male SMPL model
- Template meshes in T-pose
- Shape/Pose blend shapes
- Skinning weights

## Testing

The pipeline has been tested on 5 sample photos:
1. reddit_chqj4q.jpg
2. reddit_n15xuu.jpg
3. reddit_f1xv2s.jpg
4. female_asur3k.jpg
5. female_fwguom.jpg

All outputs saved to `smpl_output/` directory.

## Architecture

```
Photo/Measurements
       ↓
[PhotoToSMPL Estimator]
       ↓
SMPLParams (betas, pose, trans)
       ↓
[SMPLModel.forward()]
       ↓
Mesh (vertices, faces)
       ↓
[Export to Three.js JSON/OBJ]
       ↓
Web-ready 3D model
```

## Dependencies

- numpy
- Python 3.8+

Optional (for API):
- fastapi
- uvicorn
- python-multipart

## Notes

- The photo estimation is currently a simplified mock implementation
- In production, replace `PhotoToSMPL.estimate_from_photo()` with actual computer vision pipeline (e.g., OpenPose + SMPLify)
- SMPL models are converted from pickle format to NPZ for better compatibility
- No chumpy dependency required for converted models
