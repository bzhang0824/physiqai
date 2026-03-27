#!/usr/bin/env python3
"""
Simplified SMPL Loader - No Chumpy Required
===========================================

Direct pickle loading of SMPL model files without chumpy dependency.
"""

import pickle
import numpy as np
from pathlib import Path
import inspect

# Fix for chumpy compatibility with Python 3.12
if not hasattr(inspect, 'getargspec'):
    inspect.getargspec = inspect.getfullargspec


class SimpleSMPL:
    """Simplified SMPL model that loads without chumpy"""

    def __init__(self, model_path: Path):
        """Load SMPL model from pickle file"""
        self.model_path = Path(model_path)

        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")

        print(f"Loading SMPL model from: {model_path}")

        # Load pickle file
        with open(self.model_path, 'rb') as f:
            data = pickle.load(f, encoding='latin1')

        # Extract core components
        self.faces = data['f']  # (13776, 3)
        self.v_template = data['v_template']  # (6890, 3) - T-pose vertices
        self.shapedirs = data['shapedirs']  # (6890, 3, 10) - shape blend shapes
        self.posedirs = data['posedirs']  # (6890, 3, 207) - pose blend shapes
        self.weights = data['weights']  # (6890, 24) - skinning weights
        self.kintree_table = data['kintree_table']  # (2, 24) - kinematic tree

        # Joint regressor (might be scipy sparse matrix)
        self.J_regressor = data['J_regressor']

        print(f"✅ SMPL model loaded:")
        print(f"   Vertices: {len(self.v_template)}")
        print(f"   Faces: {len(self.faces)}")
        print(f"   Shape params: {self.shapedirs.shape[-1]}")

    def generate(self, betas=None, pose=None):
        """
        Generate mesh from shape parameters.

        Args:
            betas: Shape parameters (10,), range [-3, 3]
            pose: Pose parameters (72,) - not fully implemented

        Returns:
            dict with 'vertices' and 'faces'
        """
        if betas is None:
            betas = np.zeros(10)

        betas = np.asarray(betas).reshape(-1)

        # Apply shape blend shapes
        # v_shaped = v_template + sum(beta_i * shape_blendshape_i)
        v_shaped = self.v_template.copy()

        for i in range(min(len(betas), self.shapedirs.shape[-1])):
            v_shaped += betas[i] * self.shapedirs[:, :, i]

        # For now, return shaped vertices (T-pose)
        # Full pose implementation requires rotation matrix calculations

        return {
            'vertices': v_shaped,
            'faces': self.faces
        }

    def get_measurements(self, vertices):
        """
        Calculate approximate body measurements from vertices.

        These are simplified calculations based on vertex positions.
        """
        # Find min/max for bounding box measurements
        x_coords = vertices[:, 0]
        y_coords = vertices[:, 1]
        z_coords = vertices[:, 2]

        # Approximate measurements based on SMPL vertex topology
        # These indices are approximate and would need calibration for accuracy

        # Chest: around upper torso (approximate vertex range)
        chest_y = 0.3  # relative height
        chest_indices = np.where((y_coords > chest_y - 0.1) & (y_coords < chest_y + 0.1))[0]
        if len(chest_indices) > 0:
            chest_width = np.max(x_coords[chest_indices]) - np.min(x_coords[chest_indices])
            chest_depth = np.max(z_coords[chest_indices]) - np.min(z_coords[chest_indices])
            chest_circumference = 2 * np.pi * np.sqrt((chest_width**2 + chest_depth**2) / 2)
        else:
            chest_circumference = 85

        # Waist: around middle torso
        waist_y = 0.0
        waist_indices = np.where((y_coords > waist_y - 0.1) & (y_coords < waist_y + 0.1))[0]
        if len(waist_indices) > 0:
            waist_width = np.max(x_coords[waist_indices]) - np.min(x_coords[waist_indices])
            waist_depth = np.max(z_coords[waist_indices]) - np.min(z_coords[waist_indices])
            waist_circumference = 2 * np.pi * np.sqrt((waist_width**2 + waist_depth**2) / 2)
        else:
            waist_circumference = 70

        # Hips: around lower torso
        hip_y = -0.2
        hip_indices = np.where((y_coords > hip_y - 0.1) & (y_coords < hip_y + 0.1))[0]
        if len(hip_indices) > 0:
            hip_width = np.max(x_coords[hip_indices]) - np.min(x_coords[hip_indices])
            hip_depth = np.max(z_coords[hip_indices]) - np.min(z_coords[hip_indices])
            hip_circumference = 2 * np.pi * np.sqrt((hip_width**2 + hip_depth**2) / 2)
        else:
            hip_circumference = 95

        # Height: from top of head to feet
        height = np.max(y_coords) - np.min(y_coords)

        return {
            'chest_cm': chest_circumference * 100,
            'waist_cm': waist_circumference * 100,
            'hips_cm': hip_circumference * 100,
            'height_cm': height * 100,
        }

    def export_obj(self, vertices, filepath):
        """Export mesh to OBJ format"""
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


if __name__ == "__main__":
    # Test the loader
    import sys

    model_path = Path(__file__).parent.parent / 'models' / 'smpl' / 'basicModel_f_lbs_10_207_0_v1.0.0.pkl'

    try:
        model = SimpleSMPL(model_path)

        # Generate default mesh
        mesh = model.generate()
        print(f"\nGenerated default mesh:")
        print(f"  Vertices: {mesh['vertices'].shape}")
        print(f"  Faces: {mesh['faces'].shape}")

        # Generate with custom betas (curvy body type)
        betas = np.array([0.8, 0.2, 0.3, 0.3, 0.2, 0.4, 0.2, 0.6, 0.0, 0.0])
        mesh_custom = model.generate(betas=betas)

        # Get measurements
        measurements = model.get_measurements(mesh_custom['vertices'])
        print(f"\nMeasurements:")
        for name, value in measurements.items():
            print(f"  {name}: {value:.1f}")

        # Export test mesh
        output_path = Path(__file__).parent / 'test_output.obj'
        model.export_obj(mesh_custom['vertices'], output_path)
        print(f"\nExported to: {output_path}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
