#!/usr/bin/env python3
"""
smpl_core.py - SMPL Model Wrapper

Core SMPL model loading and mesh generation.
Wraps the official SMPL model for easy integration.
"""

import numpy as np
import pickle
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Literal


@dataclass
class SMPLConfig:
    """Configuration for SMPL model"""
    gender: Literal['male', 'female', 'neutral'] = 'neutral'
    num_betas: int = 10  # Number of shape parameters
    num_pose_params: int = 72  # Number of pose parameters (24 joints × 3)


class SMPLModel:
    """
    SMPL (Skinned Multi-Person Linear Model) wrapper.

    Provides easy interface for generating body meshes from
    shape parameters (betas) and pose parameters.
    """

    def __init__(self, model_path: Optional[Path] = None, config: Optional[SMPLConfig] = None):
        """
        Initialize SMPL model.

        Args:
            model_path: Path to SMPL .pkl file. If None, uses default based on gender.
            config: SMPLConfig instance. If None, uses defaults.
        """
        self.config = config or SMPLConfig()
        self.model_path = model_path or self._get_default_model_path()

        # Load model data
        self._load_model()

    def _get_default_model_path(self) -> Path:
        """Get default model path based on gender"""
        base = Path(__file__).parent.parent / 'models' / 'smpl'

        gender_map = {
            'male': 'basicmodel_m_lbs_10_207_0_v1.0.0.pkl',
            'female': 'basicmodel_f_lbs_10_207_0_v1.0.0.pkl',
            'neutral': 'basicmodel_neutral_lbs_10_207_0_v1.0.0.pkl'
        }

        return base / gender_map[self.config.gender]

    def _load_model(self):
        """Load SMPL model from pickle file"""
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"SMPL model not found: {self.model_path}\n"
                f"Download from https://smpl.is.tue.mpg.de/"
            )

        with open(self.model_path, 'rb') as f:
            data = pickle.load(f, encoding='latin1')

        # Extract model components
        self.faces = data['f']  # Face indices (13776, 3)

        # Template mesh (T-pose)
        self.v_template = data['v_template']  # (6890, 3)

        # Shape blend shapes
        self.shapedirs = data['shapedirs']  # (6890, 3, 10)

        # Pose blend shapes
        self.posedirs = data['posedirs']  # (6890, 3, 207)

        # Joint regressor
        self.J_regressor = data['J_regressor']  # (24, 6890)

        # Skinning weights
        self.weights = data['weights']  # (6890, 24)

        # Kinematic tree
        self.kintree_table = data['kintree_table']  # (2, 24)

        print(f"✅ Loaded SMPL model: {self.config.gender}")
        print(f"   Vertices: {len(self.v_template)}")
        print(f"   Faces: {len(self.faces)}")
        print(f"   Shape params: {self.shapedirs.shape[-1]}")

    def forward(self, betas: Optional[np.ndarray] = None,
                pose: Optional[np.ndarray] = None,
                return_joints: bool = False) -> dict:
        """
        Generate mesh from shape and pose parameters.

        Args:
            betas: Shape parameters (10,) or (batch, 10). Range typically [-3, 3]
            pose: Pose parameters (72,) - rotation vectors for 24 joints
            return_joints: If True, return joint positions

        Returns:
            Dictionary with:
                - 'vertices': (6890, 3) mesh vertices
                - 'faces': (13776, 3) face indices
                - 'joints': (24, 3) joint positions (if return_joints=True)
        """
        # Default parameters
        if betas is None:
            betas = np.zeros(self.config.num_betas)

        if pose is None:
            # T-pose (all zeros)
            pose = np.zeros(self.config.num_pose_params)

        # Ensure 1D arrays
        betas = np.asarray(betas).reshape(-1)
        pose = np.asarray(pose).reshape(-1)

        # Apply shape blend shapes
        v_shaped = self._apply_shape_blend_shapes(betas)

        # Get joint locations from shaped mesh
        J = self._get_joints(v_shaped)

        # Apply pose blend shapes and skinning
        vertices = self._apply_pose_and_skinning(v_shaped, pose, J)

        result = {
            'vertices': vertices,
            'faces': self.faces
        }

        if return_joints:
            result['joints'] = J

        return result

    def _apply_shape_blend_shapes(self, betas: np.ndarray) -> np.ndarray:
        """
        Apply shape parameters to template mesh.

        v_shaped = v_template + sum(beta_i * shape_blendshape_i)
        """
        v_shaped = self.v_template.copy()

        for i in range(min(len(betas), self.shapedirs.shape[-1])):
            v_shaped += betas[i] * self.shapedirs[:, :, i]

        return v_shaped

    def _get_joints(self, vertices: np.ndarray) -> np.ndarray:
        """
        Calculate joint positions from vertices using regressor.

        J = J_regressor @ vertices
        """
        if hasattr(self.J_regressor, 'toarray'):
            J_regressor = self.J_regressor.toarray()
        else:
            J_regressor = self.J_regressor

        return J_regressor @ vertices

    def _apply_pose_and_skinning(self, v_shaped: np.ndarray,
                                  pose: np.ndarray,
                                  J: np.ndarray) -> np.ndarray:
        """
        Apply pose-dependent deformation and linear blend skinning.

        This is a simplified version. Full implementation would:
        1. Compute rotation matrices from pose vectors
        2. Apply pose blend shapes
        3. Compute skinning transformations
        4. Apply linear blend skinning
        """
        # For now, return shaped vertices (T-pose)
        # Full pose implementation requires rotation matrix calculations
        # This is sufficient for body morphing without articulation

        # TODO: Implement full pose pipeline if needed
        return v_shaped

    def get_body_measurements(self, vertices: np.ndarray) -> dict:
        """
        Calculate body measurements from mesh vertices.

        Returns 7 key measurements:
        - chest, waist, hips, shoulders, arms, thighs, calves
        """
        # Pre-defined vertex indices for measurement locations
        # These would be determined from SMPL topology analysis
        measurement_indices = {
            'chest': self._get_chest_indices(),
            'waist': self._get_waist_indices(),
            'hips': self._get_hips_indices(),
            'shoulders': self._get_shoulder_indices(),
            'arms': self._get_arm_indices(),
            'thighs': self._get_thigh_indices(),
            'calves': self._get_calf_indices()
        }

        measurements = {}
        for name, indices in measurement_indices.items():
            if indices is not None:
                # Calculate circumference from vertices
                measurement = self._calculate_circumference(vertices, indices)
                measurements[name] = measurement * 100  # Convert to cm
            else:
                measurements[name] = None

        return measurements

    def _get_chest_indices(self):
        """Get vertex indices for chest measurement"""
        # Approximate - would need precise SMPL topology
        return list(range(1300, 1400))  # Placeholder

    def _get_waist_indices(self):
        """Get vertex indices for waist measurement"""
        return list(range(1800, 1900))  # Placeholder

    def _get_hips_indices(self):
        """Get vertex indices for hip measurement"""
        return list(range(2000, 2100))  # Placeholder

    def _get_shoulder_indices(self):
        """Get vertex indices for shoulder measurement"""
        return list(range(500, 600))  # Placeholder

    def _get_arm_indices(self):
        """Get vertex indices for arm measurement"""
        return list(range(1500, 1600))  # Placeholder

    def _get_thigh_indices(self):
        """Get vertex indices for thigh measurement"""
        return list(range(3000, 3100))  # Placeholder

    def _get_calf_indices(self):
        """Get vertex indices for calf measurement"""
        return list(range(3500, 3600))  # Placeholder

    def _calculate_circumference(self, vertices: np.ndarray, indices: list) -> float:
        """
        Calculate circumference from loop of vertices.

        Simplified: sum distances between consecutive vertices.
        """
        if len(indices) < 2:
            return 0.0

        total = 0.0
        for i in range(len(indices)):
            v1 = vertices[indices[i]]
            v2 = vertices[indices[(i + 1) % len(indices)]]
            total += np.linalg.norm(v2 - v1)

        return total

    def export_to_obj(self, vertices: np.ndarray, filepath: Path):
        """Export mesh to OBJ format"""
        with open(filepath, 'w') as f:
            # Write vertices
            for v in vertices:
                f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")

            # Write faces (1-indexed)
            for face in self.faces:
                f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")

    def export_to_gltf(self, vertices: np.ndarray, filepath: Path):
        """Export mesh to GLTF format (for web viewer)"""
        # Would use pygltflib or trimesh for this
        try:
            import trimesh
            mesh = trimesh.Trimesh(vertices=vertices, faces=self.faces)
            mesh.export(filepath)
        except ImportError:
            raise ImportError("trimesh required for GLTF export. Install: pip install trimesh")


# Convenience functions
def load_smpl_model(gender: str = 'neutral') -> SMPLModel:
    """Quick loader for SMPL model"""
    config = SMPLConfig(gender=gender)
    return SMPLModel(config=config)


def generate_body(betas: np.ndarray, gender: str = 'neutral', pose: Optional[np.ndarray] = None) -> dict:
    """
    One-shot body generation from betas.

    Args:
        betas: Shape parameters (10,)
        gender: 'male', 'female', or 'neutral'
        pose: Optional pose parameters (72,)

    Returns:
        Dictionary with vertices and faces
    """
    model = load_smpl_model(gender)
    return model.forward(betas=betas, pose=pose)


if __name__ == "__main__":
    # Demo: Generate default body
    print("SMPL Core Demo")
    print("=" * 50)

    try:
        model = load_smpl_model('neutral')

        # Generate default body
        mesh = model.forward()
        print(f"\nGenerated mesh:")
        print(f"  Vertices: {mesh['vertices'].shape}")
        print(f"  Faces: {mesh['faces'].shape}")

        # Generate with custom betas
        betas = np.array([0.5, -0.3, 0.2, 0, 0, 0, 0, 0, 0, 0])
        mesh_custom = model.forward(betas=betas)
        print(f"\nCustom body generated")

        # Try measurements
        measurements = model.get_body_measurements(mesh_custom['vertices'])
        print(f"\nApproximate measurements:")
        for name, value in measurements.items():
            if value:
                print(f"  {name}: {value:.1f} cm")

    except FileNotFoundError as e:
        print(f"\n⚠️  {e}")
        print("\nTo use SMPL models:")
        print("1. Download from https://smpl.is.tue.mpg.de/")
        print("2. Place .pkl files in models/smpl/")
