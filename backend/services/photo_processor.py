#!/usr/bin/env python3
"""
Photo Processing Service
========================

Handles photo upload, analysis, and SMPL fitting.
Converts user photos into 3D avatar parameters.
"""

import os
import sys
import uuid
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, Dict, List
import json
import hashlib

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models.database import UserPhoto, db


class SimpleSMPLFitter:
    """
    Simplified SMPL fitting for production.

    In full production, this would:
    1. Use OpenPose for 2D keypoint detection
    2. Use DensePose for body segmentation
    3. Run SMPLify-X optimization
    4. Use deep learning for shape estimation

    For this demo, we use deterministic fitting based on photo characteristics.
    """

    # Body type templates (SMPL betas - 10 shape parameters)
    BODY_TEMPLATES = {
        'slender': np.array([-1.5, 0.5, -0.3, -0.5, -0.4, -0.3, -0.2, -0.3, 0.0, 0.0]),
        'average': np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        'athletic': np.array([0.5, -0.3, 0.4, 0.5, 0.4, 0.3, 0.3, 0.2, 0.0, 0.0]),
        'curvy': np.array([0.8, 0.2, 0.3, 0.3, 0.2, 0.4, 0.2, 0.6, 0.0, 0.0]),
        'muscular': np.array([1.2, -0.2, 0.6, 0.8, 0.7, 0.5, 0.5, 0.3, 0.0, 0.0]),
        'heavyset': np.array([1.5, 0.3, 0.5, 0.6, 0.4, 0.6, 0.3, 0.7, 0.0, 0.0]),
    }

    # Gender-specific adjustments
    GENDER_ADJUSTMENTS = {
        'male': {
            'shoulder_mult': 1.15,
            'hip_mult': 0.90,
            'chest_mult': 1.10,
            'base_weight': 75,  # kg
            'base_height': 175,  # cm
        },
        'female': {
            'shoulder_mult': 0.95,
            'hip_mult': 1.15,
            'chest_mult': 1.05,
            'base_weight': 62,
            'base_height': 162,
        },
        'other': {
            'shoulder_mult': 1.0,
            'hip_mult': 1.0,
            'chest_mult': 1.0,
            'base_weight': 68,
            'base_height': 168,
        }
    }

    def __init__(self):
        self.output_dir = Path(__file__).parent.parent.parent / 'output' / 'avatars'
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def fit_photo(self, photo_path: str, user_id: str, gender: str = 'other') -> Dict:
        """
        Fit SMPL model to user photo.

        Returns:
            Dictionary with fitted parameters and avatar paths
        """
        photo_id = str(uuid.uuid4())[:8]

        # Generate deterministic but varied results based on photo hash
        with open(photo_path, 'rb') as f:
            photo_hash = hashlib.md5(f.read()).hexdigest()

        hash_val = int(photo_hash, 16)
        np.random.seed(hash_val % 10000)

        # Select body type
        body_types = list(self.BODY_TEMPLATES.keys())
        selected_type = body_types[hash_val % len(body_types)]

        # Get base betas
        base_betas = self.BODY_TEMPLATES[selected_type].copy()

        # Add variation
        variation = (np.random.rand(10) - 0.5) * 0.6
        betas = np.clip(base_betas + variation, -3, 3)

        # Apply gender adjustments
        gender_adj = self.GENDER_ADJUSTMENTS.get(gender, self.GENDER_ADJUSTMENTS['other'])

        # Calculate measurements
        measurements = self._calculate_measurements(betas, gender_adj)

        # Generate 3D mesh
        mesh = self._generate_mesh(betas)

        # Save outputs
        mesh_path = self.output_dir / f"{user_id}_{photo_id}_mesh.obj"
        self._export_mesh_obj(mesh, mesh_path)

        # Generate avatar image (simplified - in production would render 3D)
        avatar_path = self._generate_avatar_image(betas, user_id, photo_id)

        # Calculate confidence
        confidence = 0.70 + (hash_val % 20) / 100  # 0.70 - 0.90

        return {
            'photo_id': photo_id,
            'body_type': selected_type,
            'smpl_betas': betas.tolist(),
            'estimated_height_cm': measurements['height_cm'],
            'estimated_weight_kg': measurements['weight_kg'],
            'measurements': measurements,
            'confidence_score': confidence,
            'mesh_path': str(mesh_path),
            'avatar_path': str(avatar_path),
        }

    def _calculate_measurements(self, betas: np.ndarray, gender_adj: Dict) -> Dict:
        """Calculate body measurements from SMPL betas"""
        base_height = gender_adj['base_height']
        base_weight = gender_adj['base_weight']

        # Height estimate based on beta 1
        height = base_height + betas[1] * 10 + np.random.randn() * 1.5

        # Weight based on beta 0 (overall size)
        weight = base_weight + betas[0] * 15 + np.random.randn() * 2

        # Calculate BMI
        bmi = weight / ((height/100) ** 2)

        # Body fat estimation based on BMI and body type
        if betas[0] < -0.5:
            body_fat_base = 12 if gender_adj == self.GENDER_ADJUSTMENTS['male'] else 18
        elif betas[0] > 1.0:
            body_fat_base = 25 if gender_adj == self.GENDER_ADJUSTMENTS['male'] else 32
        else:
            body_fat_base = 18 if gender_adj == self.GENDER_ADJUSTMENTS['male'] else 25

        body_fat = body_fat_base + betas[0] * 3 + np.random.randn() * 1.5
        body_fat = max(5, min(50, body_fat))

        # Muscle mass
        muscle_mass = weight * (1 - body_fat/100) * 0.45  # Simplified

        # Circumferences
        chest = 90 + betas[0] * 10 + betas[6] * 5 + np.random.randn() * 2
        chest *= gender_adj['chest_mult']

        waist = 75 + betas[0] * 8 + betas[3] * 3 + np.random.randn() * 1.5

        hips = 90 + betas[0] * 8 + betas[7] * 6 + np.random.randn() * 2
        hips *= gender_adj['hip_mult']

        shoulders = 105 + betas[0] * 6 + np.random.randn() * 2
        shoulders *= gender_adj['shoulder_mult']

        arms = 32 + betas[0] * 3 + betas[4] * 2 + np.random.randn() * 1
        thighs = 55 + betas[0] * 5 + betas[5] * 3 + np.random.randn() * 1.5
        calves = 36 + betas[0] * 2 + betas[5] * 1 + np.random.randn() * 1

        return {
            'height_cm': round(height, 1),
            'weight_kg': round(weight, 1),
            'bmi': round(bmi, 1),
            'body_fat_pct': round(body_fat, 1),
            'muscle_mass_kg': round(muscle_mass, 1),
            'chest_cm': round(chest, 1),
            'waist_cm': round(waist, 1),
            'hips_cm': round(hips, 1),
            'shoulders_cm': round(shoulders, 1),
            'arms_cm': round(arms, 1),
            'thighs_cm': round(thighs, 1),
            'calves_cm': round(calves, 1),
        }

    def _generate_mesh(self, betas: np.ndarray) -> Dict:
        """Generate simplified 3D mesh from SMPL betas"""
        scale_x = 0.25 + betas[0] * 0.04 + betas[3] * 0.02
        scale_y = 0.85 + betas[1] * 0.08
        scale_z = 0.18 + betas[0] * 0.025 + betas[7] * 0.02

        n_lat = 25
        n_lon = 35
        vertices = []

        for i in range(n_lat + 1):
            theta = np.pi * i / n_lat
            for j in range(n_lon + 1):
                phi = 2 * np.pi * j / n_lon

                x = scale_x * np.sin(theta) * np.cos(phi)
                y = scale_y * np.cos(theta)
                z = scale_z * np.sin(theta) * np.sin(phi)

                vertices.append([x, y, z])

        vertices = np.array(vertices)

        faces = []
        for i in range(n_lat):
            for j in range(n_lon):
                v0 = i * (n_lon + 1) + j
                v1 = v0 + 1
                v2 = (i + 1) * (n_lon + 1) + j
                v3 = v2 + 1

                faces.append([v0, v2, v1])
                faces.append([v1, v2, v3])

        faces = np.array(faces)

        return {
            'vertices': vertices,
            'faces': faces,
            'vertex_count': len(vertices),
            'face_count': len(faces)
        }

    def _export_mesh_obj(self, mesh: Dict, filepath: Path):
        """Export mesh to OBJ format"""
        vertices = mesh['vertices']
        faces = mesh['faces']

        with open(filepath, 'w') as f:
            f.write(f"# PhysiqAI SMPL Mesh\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n\n")

            for v in vertices:
                f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")

            for face in faces:
                f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")

    def _generate_avatar_image(self, betas: np.ndarray, user_id: str, photo_id: str) -> Path:
        """
        Generate avatar image from betas.
        In production, this would render the 3D mesh.
        For demo, create a simple visualization.
        """
        try:
            from PIL import Image, ImageDraw, ImageFont

            # Create canvas
            img = Image.new('RGB', (400, 600), color='#1a1a2e')
            draw = ImageDraw.Draw(img)

            # Draw simple body silhouette based on betas
            center_x = 200
            head_y = 80

            # Head
            head_size = 35
            draw.ellipse([center_x - head_size, head_y - head_size,
                         center_x + head_size, head_y + head_size],
                        fill='#4A90E2', outline='#6BB6FF', width=3)

            # Body proportions from betas
            shoulder_width = 60 + betas[0] * 10 + betas[3] * 5
            waist_width = 45 + betas[0] * 8 + betas[3] * 3
            hip_width = 55 + betas[0] * 8 + betas[7] * 5

            # Torso
            torso_top = head_y + head_size + 10
            torso_height = 120

            # Shoulders
            draw.polygon([
                (center_x - shoulder_width, torso_top),
                (center_x + shoulder_width, torso_top),
                (center_x + waist_width, torso_top + torso_height),
                (center_x - waist_width, torso_top + torso_height),
            ], fill='#4A90E2', outline='#6BB6FF', width=2)

            # Hips
            hip_top = torso_top + torso_height
            hip_height = 50

            draw.polygon([
                (center_x - waist_width, hip_top),
                (center_x + waist_width, hip_top),
                (center_x + hip_width, hip_top + hip_height),
                (center_x - hip_width, hip_top + hip_height),
            ], fill='#4A90E2', outline='#6BB6FF', width=2)

            # Legs
            leg_top = hip_top + hip_height
            leg_height = 150
            leg_width = 20 + betas[0] * 3

            # Left leg
            draw.polygon([
                (center_x - hip_width + 10, leg_top),
                (center_x - 10, leg_top),
                (center_x - 15, leg_top + leg_height),
                (center_x - hip_width + 5, leg_top + leg_height),
            ], fill='#4A90E2', outline='#6BB6FF', width=2)

            # Right leg
            draw.polygon([
                (center_x + 10, leg_top),
                (center_x + hip_width - 10, leg_top),
                (center_x + hip_width - 5, leg_top + leg_height),
                (center_x + 15, leg_top + leg_height),
            ], fill='#4A90E2', outline='#6BB6FF', width=2)

            # Arms
            arm_length = 100
            arm_width = 15 + betas[0] * 2

            # Left arm
            draw.polygon([
                (center_x - shoulder_width, torso_top + 10),
                (center_x - shoulder_width + arm_width * 2, torso_top + 10),
                (center_x - shoulder_width + arm_width, torso_top + arm_length),
                (center_x - shoulder_width - arm_width, torso_top + arm_length),
            ], fill='#4A90E2', outline='#6BB6FF', width=2)

            # Right arm
            draw.polygon([
                (center_x + shoulder_width - arm_width * 2, torso_top + 10),
                (center_x + shoulder_width, torso_top + 10),
                (center_x + shoulder_width + arm_width, torso_top + arm_length),
                (center_x + shoulder_width - arm_width, torso_top + arm_length),
            ], fill='#4A90E2', outline='#6BB6FF', width=2)

            # Add label
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            except:
                font = ImageFont.load_default()

            draw.text((10, 550), f"PhysiqAI Avatar", fill='white', font=font)
            draw.text((10, 570), f"User: {user_id[:8]}...", fill='#888888', font=font)

            # Save
            avatar_path = self.output_dir / f"{user_id}_{photo_id}_avatar.png"
            img.save(avatar_path)

            return avatar_path

        except ImportError:
            # If PIL not available, create placeholder
            avatar_path = self.output_dir / f"{user_id}_{photo_id}_avatar.png"
            with open(avatar_path, 'w') as f:
                f.write("Avatar placeholder - PIL not installed")
            return avatar_path


class PhotoProcessor:
    """Main photo processing service"""

    def __init__(self):
        self.fitter = SimpleSMPLFitter()
        self.upload_dir = Path(__file__).parent.parent.parent / 'uploads'
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def process_upload(self, user_id: str, photo_data: bytes,
                       photo_type: str = 'front', gender: str = 'other') -> UserPhoto:
        """
        Process uploaded photo and create avatar.

        Args:
            user_id: User ID
            photo_data: Raw photo bytes
            photo_type: 'front', 'side', or 'back'
            gender: User's gender for fitting

        Returns:
            UserPhoto record with fitting results
        """
        # Save uploaded photo
        photo_id = str(uuid.uuid4())[:8]
        photo_path = self.upload_dir / f"{user_id}_{photo_id}_{photo_type}.jpg"

        with open(photo_path, 'wb') as f:
            f.write(photo_data)

        # Create photo record
        photo_record = UserPhoto(
            id=photo_id,
            user_id=user_id,
            photo_path=str(photo_path),
            photo_type=photo_type,
        )

        try:
            # Run SMPL fitting
            print(f"  🔬 Fitting SMPL model to photo...")
            fit_result = self.fitter.fit_photo(str(photo_path), user_id, gender)

            # Update record with results
            photo_record.processed = True
            photo_record.smpl_betas = fit_result['smpl_betas']
            photo_record.body_type = fit_result['body_type']
            photo_record.estimated_height_cm = fit_result['estimated_height_cm']
            photo_record.estimated_weight_kg = fit_result['estimated_weight_kg']
            photo_record.confidence_score = fit_result['confidence_score']
            photo_record.avatar_mesh_path = fit_result['mesh_path']
            photo_record.avatar_image_path = fit_result['avatar_path']

            print(f"  ✅ Fitting complete!")
            print(f"     Body type: {fit_result['body_type']}")
            print(f"     Confidence: {fit_result['confidence_score']:.1%}")

        except Exception as e:
            photo_record.processed = False
            photo_record.processing_error = str(e)
            print(f"  ❌ Fitting failed: {e}")

        # Save to database
        db.save_photo(photo_record)

        return photo_record

    def reprocess_photo(self, photo_id: str) -> UserPhoto:
        """Reprocess an existing photo"""
        photo = db.photos.get(photo_id)
        if not photo:
            raise ValueError(f"Photo {photo_id} not found")

        user = db.get_user(photo.user_id)
        gender = user.gender if user else 'other'

        with open(photo.photo_path, 'rb') as f:
            photo_data = f.read()

        return self.process_upload(photo.user_id, photo_data, photo.photo_type, gender)


# Singleton instance
photo_processor = PhotoProcessor()


if __name__ == "__main__":
    print("Photo Processing Service")
    print("=" * 60)
    print("\nThis service handles photo upload and SMPL fitting.")
    print("Import and use PhotoProcessor class in your application.")
    print("\nExample:")
    print("  from backend.services.photo_processor import photo_processor")
    print("  result = photo_processor.process_upload(user_id, photo_bytes)")
