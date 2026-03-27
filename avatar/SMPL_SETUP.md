# SMPL 3D Model Setup Guide

## Overview
SMPL (Skinned Multi-Person Linear Model) is a realistic 3D human body model that can represent a wide range of body shapes and poses. This document explains how to obtain and integrate SMPL models into the PhysiqAI avatar system.

## Current Status
✅ **Basic 3D Avatar**: `viewer-v2.html` uses procedurally generated humanoid mesh with morph targets  
⏳ **SMPL Integration**: Pending model download and integration

## What is SMPL?

SMPL provides:
- **Shape parameters** (10-300 shape coefficients) controlling body proportions
- **Pose parameters** (72 parameters) controlling skeletal pose
- **Gender-specific models** (male, female, neutral)
- **FBX/OBJ export** for use in web applications

## Required Files

### SMPL Models (Free Academic License)
1. **basicmodel_m_lbs_10_207_0_v1.0.0.pkl** - Male model
2. **basicmodel_f_lbs_10_207_0_v1.0.0.pkl** - Female model
3. **basicmodel_neutral_lbs_10_207_0_v1.0.0.pkl** - Neutral model

### SMPL-X Models (Optional - Expressive Faces/Hands)
- Full body + facial expressions + hand poses
- Available at https://smpl-x.is.tue.mpg.de/

## Download Instructions

### Step 1: Register
1. Visit https://smpl.is.tue.mpg.de/
2. Click "Download Model" 
3. Create an account (requires academic email preferred)
4. Accept the license agreement

### Step 2: Download
1. Login to your account
2. Navigate to "Downloads"
3. Download:
   - SMPL for Python (version 1.0.0 or 1.1.0)
   - SMPL for Maya/Unity (if needed)
4. Extract the .pkl files

### Step 3: Install in Project
```bash
# Copy models to the project
cp basicmodel_*.pkl /home/clawd/.openclaw/workspace/projects/physiqai/models/smpl/

# Verify installation
ls -la projects/physiqai/models/smpl/
```

## File Structure After Setup
```
projects/physiqai/
├── models/
│   └── smpl/
│       ├── basicmodel_m_lbs_10_207_0_v1.0.0.pkl
│       ├── basicmodel_f_lbs_10_207_0_v1.0.0.pkl
│       ├── basicmodel_neutral_lbs_10_207_0_v1.0.0.pkl
│       └── README.md
├── avatar/
│   ├── viewer-v2.html        # Current (procedural mesh)
│   ├── viewer-v3.html        # Future (SMPL-based)
│   └── SMPL_SETUP.md         # This file
└── data/
    └── smpl_fits/            # User-specific SMPL fits
```

## Integration Roadmap

### Phase 1: Current ✅
- **viewer-v2.html**: Procedurally generated humanoid
- Morph targets: Weight, Muscle, Body Fat
- Real-time slider controls
- Three.js primitives (spheres, cylinders)

### Phase 2: SMPL Loading (Next)
- Convert SMPL .pkl to JSON/GLTF for web
- Load SMPL mesh into Three.js
- Apply shape parameters (betas)
- Implement gender switching

### Phase 3: SMPLify-X Integration (Future)
- Fit SMPL model to user photos
- Extract body measurements from images
- Generate personalized avatars

## Technical Details

### SMPL Shape Parameters
- **Beta 0-9**: Primary body shape (height, weight, proportions)
- **Beta 0**: Overall body size
- **Beta 1**: Height vs width ratio
- **Beta 2**: Muscle mass distribution
- ... and more

### For Web Usage
Since SMPL models are Python-based, for web integration we need:
1. **Pre-computed meshes** for different body types
2. **Morph targets** in Three.js format
3. **Custom shader** for shape blending

### Alternative: SMPL-Web Viewer
Open-source web viewers available:
- https://github.com/smplbody/smpl-web (community)
- https://github.com/Meshcapade/smpl-web (commercial)

## Using Current viewer-v2.html

The current viewer provides:

| Feature | Status | Description |
|---------|--------|-------------|
| Weight Slider | ✅ | Controls overall body mass |
| Muscle Slider | ✅ | Controls shoulder/arm width |
| Fat Slider | ✅ | Controls torso/hip roundness |
| Torso Width | ✅ | Independent torso scaling |
| Arm Thickness | ✅ | Arm scaling |
| Leg Thickness | ✅ | Leg scaling |
| Presets | ✅ | Skinny/Fit/Muscular/Overweight |
| Real-time | ✅ | 60fps morph updates |

### Opening the Viewer
```bash
# Serve the file locally
cd projects/physiqai/avatar
python3 -m http.server 8000

# Open in browser
# http://localhost:8000/viewer-v2.html
```

## Next Steps for SMPL Integration

1. **Download SMPL models** from https://smpl.is.tue.mpg.de/
2. **Convert models** to web-compatible format (GLTF/GLB)
3. **Create viewer-v3.html** with full SMPL support
4. **Implement pose controls** for articulation
5. **Add photo-to-avatar** pipeline with SMPLify-X

## Resources

- **SMPL Website**: https://smpl.is.tue.mpg.de/
- **SMPL-X Website**: https://smpl-x.is.tue.mpg.de/
- **SMPL Paper**: https://files.is.tue.mpg.de/black/papers/SMPL2015.pdf
- **SMPLify-X Paper**: https://smpl-x.is.tue.mpg.de/media/upload/smplex.pdf

## License Notice

SMPL models are provided under the **SMPL Model License**:
- Free for academic/research use
- Commercial use requires separate license
- Redistribution prohibited

---

*Document created for PhysiqAI Avatar System*  
*Last updated: 2026-02-22*
