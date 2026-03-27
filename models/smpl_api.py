#!/usr/bin/env python3
"""
FastAPI endpoints for SMPL pipeline
===================================

API endpoints:
- POST /api/v1/photo-to-smpl: Photo → SMPL parameters
- POST /api/v1/measurements-to-smpl: Measurements → SMPL parameters
- POST /api/v1/smpl-to-mesh: SMPL params → mesh data
- POST /api/v1/smpl-to-threejs: SMPL params → Three.js JSON

Usage:
    uvicorn smpl_api:app --host 0.0.0.0 --port 8000

Or run directly:
    python smpl_api.py
"""

import sys
import json
from pathlib import Path
from typing import Optional
from dataclasses import asdict

try:
    from fastapi import FastAPI, File, UploadFile, Form, HTTPException
    from fastapi.responses import JSONResponse, FileResponse
    from pydantic import BaseModel
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    print("FastAPI not installed. Install with: pip install fastapi uvicorn python-multipart")

# Import SMPL pipeline
sys.path.insert(0, str(Path(__file__).parent))
from smpl_pipeline import SMPLPipeline, SMPLParams

# Initialize FastAPI app and pipeline
app = None
pipeline = None

if HAS_FASTAPI:
    app = FastAPI(
        title="PhysiqAI SMPL API",
        description="Convert photos and measurements to 3D body meshes using SMPL",
        version="1.0.0"
    )

# Pydantic models for request/response
class MeasurementsInput(BaseModel):
    height_cm: float
    weight_kg: float
    gender: str = "neutral"

class SMPLParamsInput(BaseModel):
    betas: list
    pose: list
    trans: list
    gender: str = "neutral"

class SMPLResponse(BaseModel):
    success: bool
    params: dict
    message: str = ""

# Initialize pipeline on startup
@app.on_event("startup") if HAS_FASTAPI else lambda: None
async def startup_event():
    global pipeline
    pipeline = SMPLPipeline()
    print("✅ SMPL Pipeline initialized")

@app.post("/api/v1/photo-to-smpl", response_model=SMPLResponse) if HAS_FASTAPI else None
async def photo_to_smpl(
    photo: UploadFile = File(...),
    gender: str = Form("neutral")
):
    """
    Convert photo to SMPL parameters.

    - **photo**: Image file (JPG/PNG)
    - **gender**: male, female, or neutral

    Returns SMPL shape and pose parameters.
    """
    try:
        # Save uploaded file temporarily
        temp_path = f"/tmp/{photo.filename}"
        with open(temp_path, "wb") as f:
            content = await photo.read()
            f.write(content)

        # Run pipeline
        params = pipeline.photo_to_params(temp_path, gender)

        return {
            "success": True,
            "params": params.to_dict(),
            "message": "Photo processed successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/measurements-to-smpl", response_model=SMPLResponse) if HAS_FASTAPI else None
async def measurements_to_smpl(input_data: MeasurementsInput):
    """
    Convert body measurements to SMPL parameters.

    - **height_cm**: Height in centimeters
    - **weight_kg**: Weight in kilograms
    - **gender**: male, female, or neutral

    Returns SMPL shape and pose parameters.
    """
    try:
        params = pipeline.measurements_to_params(
            input_data.height_cm,
            input_data.weight_kg,
            input_data.gender
        )

        return {
            "success": True,
            "params": params.to_dict(),
            "message": "Measurements converted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/smpl-to-mesh") if HAS_FASTAPI else None
async def smpl_to_mesh(params_input: SMPLParamsInput):
    """
    Generate mesh from SMPL parameters.

    Returns mesh vertices and faces.
    """
    try:
        params = SMPLParams.from_dict({
            'betas': params_input.betas,
            'pose': params_input.pose,
            'trans': params_input.trans,
            'gender': params_input.gender
        })

        mesh = pipeline.params_to_mesh(params)

        return {
            "success": True,
            "mesh": {
                'vertices': mesh['vertices'].tolist(),
                'faces': mesh['faces'].tolist(),
                'n_vertices': len(mesh['vertices']),
                'n_faces': len(mesh['faces'])
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/smpl-to-threejs") if HAS_FASTAPI else None
async def smpl_to_threejs(params_input: SMPLParamsInput):
    """
    Generate Three.js BufferGeometry JSON from SMPL parameters.

    Returns JSON compatible with Three.js BufferGeometryLoader.
    """
    try:
        params = SMPLParams.from_dict({
            'betas': params_input.betas,
            'pose': params_input.pose,
            'trans': params_input.trans,
            'gender': params_input.gender
        })

        mesh = pipeline.params_to_mesh(params)

        # Export to Three.js JSON
        output_path = f"/tmp/smpl_output_{hash(str(params.betas))}.json"
        json_data = pipeline.export_threejs(mesh, output_path)

        return {
            "success": True,
            "geometry": json_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health") if HAS_FASTAPI else None
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "pipeline_ready": pipeline is not None}

# Command-line interface
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        # Run demo without FastAPI
        from smpl_pipeline import demo_pipeline
        demo_pipeline()
    elif HAS_FASTAPI:
        # Run FastAPI server
        import uvicorn
        print("Starting SMPL API server...")
        print("Endpoints:")
        print("  POST /api/v1/photo-to-smpl")
        print("  POST /api/v1/measurements-to-smpl")
        print("  POST /api/v1/smpl-to-mesh")
        print("  POST /api/v1/smpl-to-threejs")
        print("  GET  /health")
        print("\nServer running at http://localhost:8000")
        print("API docs at http://localhost:8000/docs")
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        print("FastAPI not installed. Install with:")
        print("  pip install fastapi uvicorn python-multipart")
        print("\nOr run demo without server:")
        print("  python smpl_api.py --demo")
