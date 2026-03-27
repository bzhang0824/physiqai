#!/usr/bin/env python3
"""
SMPL Pipeline for PhysiqAI
==========================
Complete pipeline for SMPL model integration:
1. Load SMPL models (male/female)
2. Photo → SMPL parameter estimation (mock/demo)
3. Generate body mesh from parameters
4. Export to Three.js-compatible formats (JSON/GLTF)
5. API endpoint for photo → SMPL params

SMPL Parameters:
- betas (10): Shape parameters (body proportions)
- pose (72): Pose parameters (24 joints × 3 axis-angle)
- trans (3): Global translation

Author: PhysiqAI
"""

import numpy as np
import json
import base64
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
import warnings
warnings.filterwarnings('ignore')


@dataclass
class SMPLParams:
    """SMPL model parameters"""
    betas: np.ndarray  # Shape parameters (10,)
    pose: np.ndarray   # Pose parameters (72,) - axis-angle rotations
    trans: np.ndarray  # Translation (3,)
    gender: str        # 'male', 'female', or 'neutral'

    def __post_init__(self):
        # Ensure correct shapes
        self.betas = np.asarray(self.betas).reshape(-1)
        self.pose = np.asarray(self.pose).reshape(-1)
        self.trans = np.asarray(self.trans).reshape(-1)

        # Pad or truncate to correct sizes
        if len(self.betas) < 10:
            self.betas = np.pad(self.betas, (0, 10 - len(self.betas)))
        elif len(self.betas) > 10:
            self.betas = self.betas[:10]

        if len(self.pose) < 72:
            self.pose = np.pad(self.pose, (0, 72 - len(self.pose)))
        elif len(self.pose) > 72:
            self.pose = self.pose[:72]

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'betas': self.betas.tolist(),
            'pose': self.pose.tolist(),
            'trans': self.trans.tolist(),
            'gender': self.gender
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'SMPLParams':
        """Create from dictionary"""
        return cls(
            betas=np.array(data['betas']),
            pose=np.array(data['pose']),
            trans=np.array(data['trans']),
            gender=data.get('gender', 'neutral')
        )


class SMPLModel:
    """
    SMPL (Skinned Multi-Person Linear) Model Implementation.

    Simplified implementation that works without chumpy dependency.
    Loads from NPZ files converted from official SMPL pickle files.
    """

    def __init__(self, model_path: Optional[Path] = None, gender: str = 'neutral'):
        """
        Initialize SMPL model.

        Args:
            model_path: Path to SMPL .npz file. If None, uses default based on gender.
            gender: 'male', 'female', or 'neutral'
        """
        self.gender = gender
        self.model_path = model_path or self._get_default_model_path()

        # Load model data
        self._load_model()

        # Generate synthetic shapedirs if missing
        self._ensure_shapedirs()

        print(f"✅ Loaded SMPL model: {gender}")
        print(f"   Vertices: {self.v_template.shape[0]}")
        print(f"   Faces: {self.faces.shape[0]}")
        print(f"   Shape params: 10")
        print(f"   Pose params: 72")

    def _get_default_model_path(self) -> Path:
        """Get default model path based on gender"""
        base = Path(__file__).parent / 'smpl'

        gender_map = {
            'male': 'smpl_male.npz',
            'female': 'smpl_female.npz',
            'neutral': 'smpl_male.npz'  # Use male as default for neutral
        }

        return base / gender_map.get(self.gender, 'smpl_male.npz')

    def _load_model(self):
        """Load SMPL model from NPZ file"""
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"SMPL model not found: {self.model_path}\n"
                f"Run convert_smpl.py first to convert .pkl to .npz"
            )

        data = np.load(self.model_path, allow_pickle=True)

        # Extract model components
        self.faces = data['f']  # Face indices (13776, 3)
        self.v_template = data['v_template']  # Template mesh (6890, 3)

        # Shape blend shapes (if available)
        if 'shapedirs' in data:
            self.shapedirs = data['shapedirs']  # (6890, 3, 10)
        else:
            self.shapedirs = None

        # Pose blend shapes
        if 'posedirs' in data:
            self.posedirs = data['posedirs']  # (6890, 3, 207)
        else:
            self.posedirs = np.zeros((6890, 3, 207))

        # Joint regressor
        if 'J_regressor' in data:
            self.J_regressor = data['J_regressor']  # (24, 6890)
        elif 'J' in data:
            # Use pre-computed joints
            self.J_template = data['J']  # (24, 3)
            self.J_regressor = None
        else:
            self.J_regressor = None
            self.J_template = None

        # Skinning weights
        self.weights = data['weights']  # (6890, 24)

        # Kinematic tree
        self.kintree_table = data['kintree_table']  # (2, 24)

    def _ensure_shapedirs(self):
        """Generate shapedirs if missing from model file"""
        if self.shapedirs is None:
            print("   Generating synthetic shape blend shapes...")
            # Create synthetic shapedirs based on principal component analysis pattern
            # This is a simplified approximation
            n_vertices = self.v_template.shape[0]
            self.shapedirs = np.zeros((n_vertices, 3, 10))

            # Beta 0: Overall scale
            self.shapedirs[:, :, 0] = self.v_template * 0.1

            # Beta 1: Height (Y-axis)
            height_mask = self.v_template[:, 1] > 0
            self.shapedirs[height_mask, 1, 1] = 0.05

            # Beta 2: Width (X-axis)
            width_factor = np.abs(self.v_template[:, 0]) * 0.1
            self.shapedirs[:, 0, 2] = width_factor

            # Beta 3: Depth (Z-axis)
            depth_factor = np.abs(self.v_template[:, 2]) * 0.1
            self.shapedirs[:, 2, 3] = depth_factor

            # Additional shape parameters for finer control
            for i in range(4, 10):
                # Random variations for remaining parameters
                np.random.seed(i)
                variation = np.random.randn(n_vertices, 3) * 0.02
                self.shapedirs[:, :, i] = variation

    def forward(self, betas: Optional[np.ndarray] = None,
                pose: Optional[np.ndarray] = None,
                trans: Optional[np.ndarray] = None) -> Dict[str, np.ndarray]:
        """
        Generate mesh from shape and pose parameters.

        Args:
            betas: Shape parameters (10,) - body proportions
            pose: Pose parameters (72,) - axis-angle rotations for 24 joints
            trans: Global translation (3,)

        Returns:
            Dictionary with:
                - 'vertices': (6890, 3) mesh vertices
                - 'faces': (13776, 3) face indices
                - 'joints': (24, 3) joint positions
        """
        # Default parameters
        if betas is None:
            betas = np.zeros(10)
        if pose is None:
            pose = np.zeros(72)
        if trans is None:
            trans = np.zeros(3)

        betas = np.asarray(betas).reshape(-1)
        pose = np.asarray(pose).reshape(-1)
        trans = np.asarray(trans).reshape(-1)

        # Step 1: Apply shape blend shapes
        v_shaped = self._apply_shape_blend_shapes(betas)

        # Step 2: Get joint locations
        joints = self._get_joints(v_shaped)

        # Step 3: Apply pose blend shapes (simplified)
        v_posed = self._apply_pose_blend_shapes(v_shaped, pose)

        # Step 4: Apply linear blend skinning (simplified)
        vertices = self._apply_skinning(v_posed, pose, joints)

        # Step 5: Apply global translation
        vertices = vertices + trans
        joints = joints + trans

        return {
            'vertices': vertices,
            'faces': self.faces,
            'joints': joints,
            'betas': betas,
            'pose': pose
        }

    def _apply_shape_blend_shapes(self, betas: np.ndarray) -> np.ndarray:
        """Apply shape parameters to template mesh"""
        v_shaped = self.v_template.copy()

        for i in range(min(len(betas), self.shapedirs.shape[-1])):
            v_shaped += betas[i] * self.shapedirs[:, :, i]

        return v_shaped

    def _get_joints(self, vertices: np.ndarray) -> np.ndarray:
        """Calculate joint positions from vertices"""
        if self.J_regressor is not None:
            return self.J_regressor @ vertices
        elif hasattr(self, 'J_template'):
            # Use template joints with slight adjustment based on shape
            return self.J_template.copy()
        else:
            # Estimate from vertices
            return self._estimate_joints(vertices)

    def _estimate_joints(self, vertices: np.ndarray) -> np.ndarray:
        """Rough joint estimation from vertex positions"""
        # Simplified joint positions based on vertex clusters
        joints = np.zeros((24, 3))

        # Pelvis (center of hips)
        joints[0] = vertices[3000:3500].mean(axis=0)

        # Other joints (simplified)
        for i in range(1, 24):
            # Distribute joints across body
            idx = i * 287 % len(vertices)
            joints[i] = vertices[idx]

        return joints

    def _apply_pose_blend_shapes(self, vertices: np.ndarray, pose: np.ndarray) -> np.ndarray:
        """Apply pose-dependent deformations"""
        # Simplified: just return vertices for now
        # Full implementation would compute pose features and apply posedirs
        return vertices

    def _apply_skinning(self, vertices: np.ndarray, pose: np.ndarray, joints: np.ndarray) -> np.ndarray:
        """Apply linear blend skinning"""
        # Simplified: vertices already in correct position from shape/pose
        # Full implementation would compute bone transformations and blend
        return vertices

    def export_to_obj(self, result: Dict[str, np.ndarray], filepath: Path):
        """Export mesh to OBJ format"""
        vertices = result['vertices']
        faces = result['faces']

        with open(filepath, 'w') as f:
            f.write("# SMPL Model Export\n")
            f.write(f"# Vertices: {len(vertices)}\n")
            f.write(f"# Faces: {len(faces)}\n\n")

            # Write vertices
            for v in vertices:
                f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")

            # Write faces (1-indexed)
            for face in faces:
                f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")

        print(f"✅ Exported OBJ to {filepath}")

    def export_to_threejs_json(self, result: Dict[str, np.ndarray], filepath: Path):
        """
        Export to Three.js BufferGeometry JSON format.
        This is the most efficient format for web rendering.
        """
        vertices = result['vertices']
        faces = result['faces']

        # Flatten vertices for BufferGeometry
        position_array = vertices.flatten().tolist()

        # Flatten faces and convert to triangles
        index_array = faces.flatten().tolist()

        # Compute normals (simplified)
        normals = self._compute_normals(vertices, faces)
        normal_array = normals.flatten().tolist()

        # Create Three.js BufferGeometry JSON structure
        geometry = {
            "metadata": {
                "version": 4.5,
                "type": "BufferGeometry",
                "generator": "SMPLPipeline"
            },
            "type": "BufferGeometry",
            "data": {
                "attributes": {
                    "position": {
                        "itemSize": 3,
                        "type": "Float32Array",
                        "array": position_array,
                        "normalized": False
                    },
                    "normal": {
                        "itemSize": 3,
                        "type": "Float32Array",
                        "array": normal_array,
                        "normalized": False
                    }
                },
                "index": {
                    "type": "Uint32Array",
                    "array": index_array
                }
            }
        }

        with open(filepath, 'w') as f:
            json.dump(geometry, f)

        print(f"✅ Exported Three.js JSON to {filepath}")
        return geometry

    def export_to_gltf_json(self, result: Dict[str, np.ndarray], filepath: Path):
        """
        Export to simplified GLTF-compatible JSON.
        Note: This is a simplified version. Full GLTF requires more complex structure.
        """
        vertices = result['vertices']
        faces = result['faces']

        # GLTF uses right-handed coordinate system, Y-up
        # SMPL uses Y-up, so we just need to ensure correct format

        gltf = {
            "asset": {
                "version": "2.0",
                "generator": "SMPLPipeline"
            },
            "scene": 0,
            "scenes": [{"nodes": [0]}],
            "nodes": [{"mesh": 0}],
            "meshes": [{
                "primitives": [{
                    "attributes": {"POSITION": 0, "NORMAL": 1},
                    "indices": 2,
                    "mode": 4  # TRIANGLES
                }]
            }],
            "buffers": [{"uri": "data:application/octet-stream;base64,"}],  # Will be filled
            "bufferViews": [],
            "accessors": []
        }

        # For simplicity, we'll use the Three.js format which is easier
        # and can be loaded with GLTFLoader extensions
        return self.export_to_threejs_json(result, filepath)

    def _compute_normals(self, vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
        """Compute vertex normals"""
        n_vertices = len(vertices)
        normals = np.zeros_like(vertices)
        counts = np.zeros(n_vertices)

        for face in faces:
            # Get triangle vertices
            v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]

            # Compute face normal
            edge1 = v1 - v0
            edge2 = v2 - v0
            normal = np.cross(edge1, edge2)
            norm = np.linalg.norm(normal)
            if norm > 0:
                normal = normal / norm

            # Add to vertex normals
            for idx in face:
                normals[idx] += normal
                counts[idx] += 1

        # Average normals
        for i in range(n_vertices):
            if counts[i] > 0:
                normals[i] = normals[i] / counts[i]
                norm = np.linalg.norm(normals[i])
                if norm > 0:
                    normals[i] = normals[i] / norm

        return normals


class PhotoToSMPL:
    """
    Photo → SMPL parameter estimation.

    This is a simplified/mock implementation.
    In production, this would use:
    - Body keypoint detection (OpenPose, MediaPipe)
    - SMPLify optimization
    - Deep learning models (HMR, SPIN, etc.)
    """

    def __init__(self, smpl_model: SMPLModel):
        self.smpl_model = smpl_model

    def estimate_from_photo(self, photo_path: Path, gender: str = 'neutral') -> SMPLParams:
        """
        Estimate SMPL parameters from photo.

        In a real implementation, this would:
        1. Detect body keypoints
        2. Run SMPLify optimization
        3. Return fitted parameters

        For now, returns mock parameters based on photo analysis simulation.
        """
        # Mock implementation - generate varied parameters
        # In production, replace with actual computer vision pipeline

        np.random.seed(hash(str(photo_path)) % 2**32)

        # Random body shape variation
        betas = np.random.randn(10) * 0.5

        # T-pose (all zeros) or slight variation
        pose = np.zeros(72)
        # Add slight arm variation
        pose[16:19] = [0.2, 0, 0]  # Left arm
        pose[19:22] = [-0.2, 0, 0]  # Right arm

        # Zero translation
        trans = np.zeros(3)

        return SMPLParams(betas=betas, pose=pose, trans=trans, gender=gender)

    def estimate_from_measurements(self, height_cm: float, weight_kg: float,
                                   gender: str = 'neutral') -> SMPLParams:
        """
        Estimate SMPL parameters from basic body measurements.

        This is a more realistic starting point for production use.
        """
        # Normalize to SMPL parameter space
        # SMPL template is roughly 172cm, 70kg for male

        height_m = height_cm / 100
        bmi = weight_kg / (height_m ** 2)

        # Beta 0: Overall scale based on BMI
        beta0 = (bmi - 22) / 5  # Normalize around average BMI

        # Beta 1: Height variation
        beta1 = (height_cm - 172) / 10

        # Other betas: random variation for now
        betas = np.zeros(10)
        betas[0] = beta0
        betas[1] = beta1
        betas[2:] = np.random.randn(8) * 0.3

        # T-pose
        pose = np.zeros(72)
        trans = np.zeros(3)

        return SMPLParams(betas=betas, pose=pose, trans=trans, gender=gender)


class SMPLPipeline:
    """
    Main SMPL Pipeline API.

    Usage:
        pipeline = SMPLPipeline()

        # From photo
        result = pipeline.photo_to_mesh('/path/to/photo.jpg', gender='female')

        # From measurements
        result = pipeline.measurements_to_mesh(height_cm=170, weight_kg=65, gender='female')

        # Export
        pipeline.export_threejs(result, 'output.json')
    """

    def __init__(self, models_dir: Optional[Path] = None):
        """Initialize pipeline with SMPL models"""
        self.models_dir = models_dir or Path(__file__).parent / 'smpl'

        # Load models
        self.models = {}
        for gender in ['male', 'female']:
            try:
                model_path = self.models_dir / f'smpl_{gender}.npz'
                if model_path.exists():
                    self.models[gender] = SMPLModel(model_path, gender)
                else:
                    print(f"Warning: {model_path} not found")
            except Exception as e:
                print(f"Warning: Could not load {gender} model: {e}")

        # Default to available model
        self.default_gender = 'male' if 'male' in self.models else 'female'

        # Initialize photo estimator
        if self.models:
            self.photo_estimator = PhotoToSMPL(self.models[self.default_gender])

        print(f"✅ SMPL Pipeline initialized with {len(self.models)} models")

    def get_model(self, gender: str) -> SMPLModel:
        """Get SMPL model for gender"""
        gender = gender.lower()
        if gender in self.models:
            return self.models[gender]
        elif gender == 'neutral':
            return self.models[self.default_gender]
        else:
            raise ValueError(f"Unknown gender: {gender}. Available: {list(self.models.keys())}")

    def photo_to_params(self, photo_path: Union[str, Path],
                        gender: str = 'neutral') -> SMPLParams:
        """
        Convert photo to SMPL parameters.

        API Endpoint: POST /api/v1/photo-to-smpl
        Input: image file
        Output: SMPLParams JSON
        """
        photo_path = Path(photo_path)

        if not photo_path.exists():
            raise FileNotFoundError(f"Photo not found: {photo_path}")

        model = self.get_model(gender)
        estimator = PhotoToSMPL(model)

        return estimator.estimate_from_photo(photo_path, gender)

    def measurements_to_params(self, height_cm: float, weight_kg: float,
                               gender: str = 'neutral') -> SMPLParams:
        """
        Convert body measurements to SMPL parameters.

        API Endpoint: POST /api/v1/measurements-to-smpl
        Input: {height_cm, weight_kg, gender}
        Output: SMPLParams JSON
        """
        model = self.get_model(gender)
        estimator = PhotoToSMPL(model)

        return estimator.estimate_from_measurements(height_cm, weight_kg, gender)

    def params_to_mesh(self, params: SMPLParams) -> Dict[str, np.ndarray]:
        """
        Generate mesh from SMPL parameters.

        API Endpoint: POST /api/v1/smpl-to-mesh
        Input: SMPLParams JSON
        Output: mesh data
        """
        model = self.get_model(params.gender)
        return model.forward(
            betas=params.betas,
            pose=params.pose,
            trans=params.trans
        )

    def photo_to_mesh(self, photo_path: Union[str, Path],
                      gender: str = 'neutral') -> Dict[str, np.ndarray]:
        """Full pipeline: photo → params → mesh"""
        params = self.photo_to_params(photo_path, gender)
        return self.params_to_mesh(params)

    def export_threejs(self, mesh_data: Dict[str, np.ndarray],
                       filepath: Union[str, Path]) -> dict:
        """Export mesh to Three.js JSON format"""
        filepath = Path(filepath)

        # Use the model that generated this mesh
        model = list(self.models.values())[0]
        return model.export_to_threejs_json(mesh_data, filepath)

    def export_obj(self, mesh_data: Dict[str, np.ndarray],
                   filepath: Union[str, Path]):
        """Export mesh to OBJ format"""
        filepath = Path(filepath)

        model = list(self.models.values())[0]
        model.export_to_obj(mesh_data, filepath)


# FastAPI endpoint definition (for reference)
"""
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse

app = FastAPI()
pipeline = SMPLPipeline()

@app.post("/api/v1/photo-to-smpl")
async def photo_to_smpl(photo: UploadFile = File(...), gender: str = Form("neutral")):
    # Save uploaded file temporarily
    temp_path = f"/tmp/{photo.filename}"
    with open(temp_path, "wb") as f:
        f.write(await photo.read())

    # Run pipeline
    params = pipeline.photo_to_params(temp_path, gender)

    return JSONResponse(content=params.to_dict())

@app.post("/api/v1/measurements-to-smpl")
async def measurements_to_smpl(height_cm: float, weight_kg: float, gender: str = "neutral"):
    params = pipeline.measurements_to_params(height_cm, weight_kg, gender)
    return JSONResponse(content=params.to_dict())

@app.post("/api/v1/smpl-to-mesh")
async def smpl_to_mesh(params: dict):
    smpl_params = SMPLParams.from_dict(params)
    mesh = pipeline.params_to_mesh(smpl_params)

    # Return simplified mesh data
    return JSONResponse(content={
        'vertices': mesh['vertices'].tolist(),
        'faces': mesh['faces'].tolist(),
        'n_vertices': len(mesh['vertices']),
        'n_faces': len(mesh['faces'])
    })
"""


def demo_pipeline():
    """Demonstrate the full SMPL pipeline"""
    print("="*70)
    print("SMPL Pipeline Demo")
    print("="*70)

    # Initialize pipeline
    pipeline = SMPLPipeline()

    # Test 1: Generate from measurements
    print("\n📏 Test 1: Measurements → SMPL → Mesh")
    print("-"*50)

    params = pipeline.measurements_to_params(
        height_cm=175,
        weight_kg=70,
        gender='male'
    )
    print(f"Generated params:")
    print(f"  Betas: {params.betas[:5].round(3)}...")
    print(f"  Gender: {params.gender}")

    mesh = pipeline.params_to_mesh(params)
    print(f"Generated mesh:")
    print(f"  Vertices: {mesh['vertices'].shape}")
    print(f"  Faces: {mesh['faces'].shape}")

    # Export to Three.js JSON
    output_dir = Path(__file__).parent / 'smpl_output'
    output_dir.mkdir(exist_ok=True)

    json_path = output_dir / 'body_threejs.json'
    pipeline.export_threejs(mesh, json_path)

    obj_path = output_dir / 'body.obj'
    pipeline.export_obj(mesh, obj_path)

    # Test 2: Different body shapes
    print("\n🧍 Test 2: Different Body Shapes")
    print("-"*50)

    shapes = [
        ("Tall & Thin", [0.2, 1.5, -0.3, 0, 0, 0, 0, 0, 0, 0]),
        ("Short & Stocky", [0.5, -1.0, 0.5, 0, 0, 0, 0, 0, 0, 0]),
        ("Athletic", [0.3, 0.5, 0.2, 0.1, 0.2, 0.1, 0, 0, 0, 0]),
    ]

    for name, betas in shapes:
        params = SMPLParams(
            betas=np.array(betas),
            pose=np.zeros(72),
            trans=np.zeros(3),
            gender='male'
        )
        mesh = pipeline.params_to_mesh(params)

        # Calculate bounding box for size reference
        verts = mesh['vertices']
        height = verts[:, 1].max() - verts[:, 1].min()
        width = verts[:, 0].max() - verts[:, 0].min()

        print(f"  {name}: Height={height:.2f}m, Width={width:.2f}m")

    print("\n" + "="*70)
    print("✅ Demo complete! Check outputs in:", output_dir)
    print("="*70)


def test_on_sample_photos():
    """Test pipeline on sample photos from data directory"""
    print("="*70)
    print("Testing on Sample Photos")
    print("="*70)

    pipeline = SMPLPipeline()

    # Find sample photos
    data_dir = Path('/home/clawd/.openclaw/workspace/projects/physiqai/data/collected/images')

    sample_photos = []
    for subdir in ['reddit', 'reddit_female']:
        photo_dir = data_dir / subdir
        if photo_dir.exists():
            photos = list(photo_dir.glob('*.jpg'))[:3]
            sample_photos.extend(photos)

    if not sample_photos:
        print("No sample photos found!")
        return

    print(f"\nFound {len(sample_photos)} sample photos")

    output_dir = Path(__file__).parent / 'smpl_output'
    output_dir.mkdir(exist_ok=True)

    for i, photo_path in enumerate(sample_photos[:5], 1):
        print(f"\n📷 Photo {i}: {photo_path.name}")
        print("-"*50)

        try:
            # Determine gender from path
            gender = 'female' if 'female' in str(photo_path) else 'male'

            # Photo → SMPL params
            params = pipeline.photo_to_params(photo_path, gender)
            print(f"  Estimated betas: {params.betas[:3].round(3)}...")

            # SMPL params → Mesh
            mesh = pipeline.params_to_mesh(params)
            print(f"  Generated mesh: {mesh['vertices'].shape[0]} vertices")

            # Export
            json_path = output_dir / f'sample_{i}_{photo_path.stem}.json'
            pipeline.export_threejs(mesh, json_path)

        except Exception as e:
            print(f"  Error: {e}")

    print(f"\n✅ Sample processing complete! Outputs in: {output_dir}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--test-photos':
        test_on_sample_photos()
    else:
        demo_pipeline()
