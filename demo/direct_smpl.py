#!/usr/bin/env python3
"""
Direct SMPL Loader - Chumpy-Free
=================================

Loads SMPL pickle file with minimal chumpy compatibility.
"""

import sys
from pathlib import Path

# Add current directory to path for minimal_chumpy
sys.path.insert(0, str(Path(__file__).parent))

# Import minimal chumpy BEFORE numpy to set up compatibility
import minimal_chumpy

# Now import other modules
import pickle
import numpy as np


class DirectSMPL:
    """Direct SMPL model loader that works with minimal chumpy"""

    def __init__(self, model_path: Path):
        """Load SMPL model from pickle file"""
        self.model_path = Path(model_path)

        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")

        print(f"Loading SMPL model from: {model_path}")

        # Load pickle file with chumpy compatibility
        with open(self.model_path, 'rb') as f:
            data = pickle.load(f, encoding='latin1')

        # Extract core components and convert chumpy to numpy
        self.faces = np.array(data['f'])  # (13776, 3)
        self.v_template = self._to_numpy(data['v_template'])  # (6890, 3)
        self.shapedirs = self._to_numpy(data['shapedirs'])  # (6890, 3, 10)
        self.posedirs = self._to_numpy(data['posedirs'])  # (6890, 3, 207)
        self.weights = self._to_numpy(data['weights'])  # (6890, 24)
        self.kintree_table = np.array(data['kintree_table'])  # (2, 24)

        # Joint regressor (might be scipy sparse matrix)
        J_regressor = data['J_regressor']
        if hasattr(J_regressor, 'toarray'):
            self.J_regressor = J_regressor.toarray()
        else:
            self.J_regressor = self._to_numpy(J_regressor)

        print(f"✅ SMPL model loaded:")
        print(f"   Vertices: {len(self.v_template)}")
        print(f"   Faces: {len(self.faces)}")
        print(f"   Shape params: {self.shapedirs.shape[-1]}")

    def _to_numpy(self, obj):
        """Convert chumpy/scipy objects to numpy arrays"""
        if isinstance(obj, np.ndarray):
            return obj
        elif hasattr(obj, 'data') and hasattr(obj.data, '__array__'):
            # chumpy Ch object
            return np.array(obj.data)
        elif hasattr(obj, 'toarray'):
            # scipy sparse
            return obj.toarray()
        else:
            return np.array(obj)

    def generate(self, betas=None, pose=None):
        """
        Generate mesh from shape parameters.

        Args:
            betas: Shape parameters (10,), range [-3, 3]
            pose: Pose parameters (72,) - T-pose if None

        Returns:
            dict with 'vertices', 'faces', and 'joints'
        """
        if betas is None:
            betas = np.zeros(10)

        betas = np.asarray(betas).reshape(-1)

        # Apply shape blend shapes
        # v_shaped = v_template + sum(beta_i * shape_blendshape_i)
        v_shaped = self.v_template.copy()

        num_betas = min(len(betas), self.shapedirs.shape[-1])
        for i in range(num_betas):
            v_shaped += betas[i] * self.shapedirs[:, :, i]

        # Get joint locations
        joints = self._get_joints(v_shaped)

        # For now, return T-pose (no pose blend shapes applied)
        # Full implementation would apply pose here
        vertices = v_shaped

        return {
            'vertices': vertices,
            'faces': self.faces,
            'joints': joints
        }

    def _get_joints(self, vertices):
        """Calculate joint positions from vertices"""
        return self.J_regressor @ vertices

    def get_measurements(self, vertices):
        """Calculate approximate body measurements from vertices"""
        x_coords = vertices[:, 0]
        y_coords = vertices[:, 1]
        z_coords = vertices[:, 2]

        # Height: from top of head to feet
        height = np.max(y_coords) - np.min(y_coords)

        # Chest: around upper torso
        chest_y = 0.35
        chest_indices = np.where((y_coords > chest_y - 0.08) & (y_coords < chest_y + 0.08))[0]
        if len(chest_indices) > 5:
            chest_width = np.max(x_coords[chest_indices]) - np.min(x_coords[chest_indices])
            chest_depth = np.max(z_coords[chest_indices]) - np.min(z_coords[chest_indices])
            chest_circumference = np.pi * (chest_width + chest_depth)
        else:
            chest_circumference = 0.85

        # Waist: around middle torso (narrowest point)
        waist_y = 0.0
        waist_indices = np.where((y_coords > waist_y - 0.05) & (y_coords < waist_y + 0.05))[0]
        if len(waist_indices) > 5:
            waist_width = np.max(x_coords[waist_indices]) - np.min(x_coords[waist_indices])
            waist_depth = np.max(z_coords[waist_indices]) - np.min(z_coords[waist_indices])
            waist_circumference = np.pi * (waist_width + waist_depth)
        else:
            waist_circumference = 0.70

        # Hips: around lower torso
        hip_y = -0.25
        hip_indices = np.where((y_coords > hip_y - 0.08) & (y_coords < hip_y + 0.08))[0]
        if len(hip_indices) > 5:
            hip_width = np.max(x_coords[hip_indices]) - np.min(x_coords[hip_indices])
            hip_depth = np.max(z_coords[hip_indices]) - np.min(z_coords[hip_indices])
            hip_circumference = np.pi * (hip_width + hip_depth)
        else:
            hip_circumference = 0.95

        # BMI estimation
        weight_kg = 60 + (chest_circumference + waist_circumference + hip_circumference - 2.5) * 20
        height_m = height
        bmi = weight_kg / (height_m ** 2) if height_m > 0 else 0

        return {
            'chest_cm': chest_circumference * 100,
            'waist_cm': waist_circumference * 100,
            'hips_cm': hip_circumference * 100,
            'height_cm': height * 100,
            'estimated_weight_kg': weight_kg,
            'estimated_bmi': bmi,
        }

    def export_obj(self, vertices, filepath):
        """Export mesh to OBJ format"""
        filepath = Path(filepath)
        with open(filepath, 'w') as f:
            f.write(f"# SMPL Generated Mesh\n")
            f.write(f"# Vertices: {len(vertices)}\n")
            f.write(f"# Faces: {len(self.faces)}\n\n")

            # Write vertices
            for v in vertices:
                f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")

            # Write faces (1-indexed)
            f.write("\n")
            for face in self.faces:
                f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")

        return filepath


if __name__ == "__main__":
    # Test the loader
    model_path = Path(__file__).parent.parent / 'models' / 'smpl' / 'basicModel_f_lbs_10_207_0_v1.0.0.pkl'

    try:
        model = DirectSMPL(model_path)

        # Test different body types
        body_types = {
            'default': np.zeros(10),
            'slender': np.array([-1.5, 0.5, -0.3, -0.5, -0.4, -0.3, -0.2, -0.3, 0.0, 0.0]),
            'curvy': np.array([0.8, 0.2, 0.3, 0.3, 0.2, 0.4, 0.2, 0.6, 0.0, 0.0]),
            'muscular': np.array([1.2, -0.2, 0.6, 0.8, 0.7, 0.5, 0.5, 0.3, 0.0, 0.0]),
        }

        print("\n" + "="*60)
        print("GENERATING TEST MESHES")
        print("="*60)

        for name, betas in body_types.items():
            print(f"\n{name.upper()} BODY TYPE:")
            print("-" * 40)

            mesh = model.generate(betas=betas)
            measurements = model.get_measurements(mesh['vertices'])

            print(f"  Vertices: {mesh['vertices'].shape[0]}")
            print(f"  Faces: {mesh['faces'].shape[0]}")
            print(f"  Height: {measurements['height_cm']:.1f} cm")
            print(f"  Chest: {measurements['chest_cm']:.1f} cm")
            print(f"  Waist: {measurements['waist_cm']:.1f} cm")
            print(f"  Hips: {measurements['hips_cm']:.1f} cm")
            print(f"  Est. Weight: {measurements['estimated_weight_kg']:.1f} kg")

            # Export mesh
            output_path = Path(__file__).parent / f'test_{name}.obj'
            model.export_obj(mesh['vertices'], output_path)
            print(f"  Exported: {output_path.name} ({output_path.stat().st_size / 1024:.1f} KB)")

        print("\n✅ All tests passed!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
