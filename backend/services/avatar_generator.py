#!/usr/bin/env python3
"""
Avatar Generator Service
========================

Generates and morphs user avatars based on:
- SMPL body parameters
- Workout effects (pump, adaptations)
- Progress over time
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
import json
import uuid

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models.database import User, UserPhoto, ProgressEntry, db


@dataclass
class AvatarState:
    """Complete avatar state for rendering"""
    smpl_betas: List[float]
    muscle_pump: Dict[str, float]
    vascularity: float
    skin_tone: str
    pose: str

    def to_dict(self) -> dict:
        return {
            'smpl_betas': self.smpl_betas,
            'muscle_pump': self.muscle_pump,
            'vascularity': round(self.vascularity, 3),
            'skin_tone': self.skin_tone,
            'pose': self.pose,
        }


class AvatarGenerator:
    """
    Generates and morphs 3D avatars.

    Creates visual representations of:
    - Current body state
    - Post-workout pump
    - Future predictions
    - Progress comparisons
    """

    def __init__(self):
        self.output_dir = Path(__file__).parent.parent.parent / 'output' / 'avatars'
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Skin tones
        self.skin_tones = {
            'light': '#F5D5C5',
            'medium': '#D4A574',
            'tan': '#C68642',
            'dark': '#8D5524',
            'deep': '#3D2314',
        }

    def generate_current_avatar(self, user: User,
                                 with_pump: bool = False,
                                 pump_muscles: Optional[Dict[str, float]] = None) -> Dict:
        """
        Generate current avatar for user.

        Args:
            user: The user
            with_pump: Whether to apply post-workout pump
            pump_muscles: Muscle pump values if with_pump=True

        Returns:
            Avatar data with paths and state
        """
        # Get latest photo/fitting
        photos = db.get_user_photos(user.id)
        if not photos or not photos[-1].smpl_betas:
            # Generate default avatar
            base_betas = [0.0] * 10
        else:
            base_betas = photos[-1].smpl_betas

        base_betas = np.array(base_betas)

        # Apply current body composition adjustments
        if user.current_weight_kg and photos and photos[-1].estimated_weight_kg:
            weight_diff = user.current_weight_kg - photos[-1].estimated_weight_kg
            base_betas[0] += weight_diff * 0.02  # Adjust beta 0 for weight change

        # Apply pump if requested
        if with_pump and pump_muscles:
            base_betas = self._apply_pump_to_betas(base_betas, pump_muscles)

        # Generate mesh
        mesh = self._generate_mesh(base_betas)

        # Save files
        avatar_id = str(uuid.uuid4())[:8]
        mesh_path = self.output_dir / f"{user.id}_{avatar_id}_current.obj"
        self._export_mesh_obj(mesh, mesh_path)

        image_path = self._generate_avatar_image(base_betas, user, avatar_id,
                                                   with_pump=with_pump)

        return {
            'avatar_id': avatar_id,
            'mesh_path': str(mesh_path),
            'image_path': str(image_path),
            'smpl_betas': base_betas.tolist(),
            'state': AvatarState(
                smpl_betas=base_betas.tolist(),
                muscle_pump=pump_muscles or {},
                vascularity=0.3 if not with_pump else 0.7,
                skin_tone='medium',
                pose='standing_front',
            ).to_dict(),
        }

    def generate_future_avatar(self, user: User, weeks: int,
                                target_betas: Optional[List[float]] = None) -> Dict:
        """
        Generate predicted future avatar.

        Args:
            user: The user
            weeks: Weeks in the future
            target_betas: Optional target SMPL parameters

        Returns:
            Future avatar data
        """
        # Get current betas
        photos = db.get_user_photos(user.id)
        if not photos or not photos[-1].smpl_betas:
            current_betas = np.array([0.0] * 10)
        else:
            current_betas = np.array(photos[-1].smpl_betas)

        # Calculate future betas
        if target_betas:
            # Interpolate toward target
            target = np.array(target_betas)
            progress = min(weeks / 12, 1.0)  # Max 12 weeks for full effect
            future_betas = current_betas + (target - current_betas) * progress
        else:
            # Default projection (muscle gain)
            future_betas = current_betas.copy()
            future_betas[0] += weeks * 0.01  # Slight size increase
            future_betas[4] += weeks * 0.005  # Arms
            future_betas[5] += weeks * 0.008  # Legs
            future_betas[6] += weeks * 0.004  # Chest

        future_betas = np.clip(future_betas, -3, 3)

        # Generate mesh
        mesh = self._generate_mesh(future_betas)

        # Save files
        avatar_id = str(uuid.uuid4())[:8]
        mesh_path = self.output_dir / f"{user.id}_{avatar_id}_future_{weeks}w.obj"
        self._export_mesh_obj(mesh, mesh_path)

        image_path = self._generate_avatar_image(future_betas, user, avatar_id,
                                                   label=f"{weeks} Weeks Future")

        return {
            'avatar_id': avatar_id,
            'weeks': weeks,
            'mesh_path': str(mesh_path),
            'image_path': str(image_path),
            'smpl_betas': future_betas.tolist(),
            'projection': {
                'from_current': current_betas.tolist(),
                'to_future': future_betas.tolist(),
                'confidence': max(0.5, 0.9 - (weeks / 20)),
            },
        }

    def generate_comparison(self, user: User,
                            before_date: Optional[datetime] = None,
                            after_date: Optional[datetime] = None) -> Dict:
        """
        Generate before/after comparison.

        Args:
            user: The user
            before_date: Date for "before" state
            after_date: Date for "after" state (default: now)

        Returns:
            Comparison data with both avatars
        """
        # Get measurements for dates
        measurements = db.get_user_measurements(user.id)

        if not measurements:
            return self._generate_default_comparison(user)

        # Find closest measurements to dates
        before_m = None
        after_m = None

        if before_date:
            for m in measurements:
                if not before_m or abs((m.measured_at - before_date).days) < abs((before_m.measured_at - before_date).days):
                    before_m = m
        else:
            # Use oldest
            before_m = measurements[0] if measurements else None

        after_date = after_date or datetime.now()
        for m in measurements:
            if not after_m or abs((m.measured_at - after_date).days) < abs((after_m.measured_at - after_date).days):
                after_m = m

        if not before_m or not after_m:
            return self._generate_default_comparison(user)

        # Generate avatars for both states
        before_betas = self._measurements_to_betas(before_m)
        after_betas = self._measurements_to_betas(after_m)

        before_avatar = self._generate_comparison_avatar(before_betas, user, "before")
        after_avatar = self._generate_comparison_avatar(after_betas, user, "after")

        # Calculate changes
        weight_change = (after_m.weight_kg or 0) - (before_m.weight_kg or 0)
        bf_change = (after_m.body_fat_pct or 0) - (before_m.body_fat_pct or 0)

        return {
            'before': {
                'date': before_m.measured_at.isoformat(),
                'avatar': before_avatar,
                'measurements': before_m.to_dict(),
            },
            'after': {
                'date': after_m.measured_at.isoformat(),
                'avatar': after_avatar,
                'measurements': after_m.to_dict(),
            },
            'changes': {
                'weight_kg': round(weight_change, 1),
                'body_fat_pct': round(bf_change, 1),
                'days_between': (after_m.measured_at - before_m.measured_at).days,
            },
        }

    def generate_timeline(self, user: User, weeks: int = 12) -> List[Dict]:
        """
        Generate avatar timeline showing progression.

        Args:
            user: The user
            weeks: Number of weeks to show

        Returns:
            List of weekly avatar states
        """
        timeline = []

        # Get base betas
        photos = db.get_user_photos(user.id)
        if not photos or not photos[-1].smpl_betas:
            base_betas = np.array([0.0] * 10)
        else:
            base_betas = np.array(photos[-1].smpl_betas)

        # Generate weekly states
        for week in range(weeks + 1):
            progress = week / weeks

            # Interpolate with projected growth
            adjusted_betas = base_betas.copy()
            adjusted_betas[0] += week * 0.008  # Overall growth
            adjusted_betas[4] += week * 0.004  # Arms
            adjusted_betas[5] += week * 0.006  # Legs
            adjusted_betas[6] += week * 0.003  # Chest

            adjusted_betas = np.clip(adjusted_betas, -3, 3)

            # Generate image
            avatar_id = str(uuid.uuid4())[:8]
            image_path = self._generate_avatar_image(
                adjusted_betas, user, avatar_id,
                label=f"Week {week}",
                size=(200, 300)
            )

            timeline.append({
                'week': week,
                'avatar_id': avatar_id,
                'image_path': str(image_path),
                'smpl_betas': adjusted_betas.tolist(),
                'progress_pct': round(progress * 100, 1),
            })

        return timeline

    def morph_avatars(self, from_betas: List[float], to_betas: List[float],
                      steps: int = 30) -> Dict:
        """
        Generate morph animation between two avatar states.

        Args:
            from_betas: Starting SMPL parameters
            to_betas: Ending SMPL parameters
            steps: Number of animation steps

        Returns:
            Morph data with frame paths
        """
        from_arr = np.array(from_betas)
        to_arr = np.array(to_betas)

        frames = []
        for i in range(steps + 1):
            t = i / steps
            # Smooth interpolation
            t_smooth = 0.5 - 0.5 * np.cos(t * np.pi)

            interp_betas = from_arr + (to_arr - from_arr) * t_smooth

            frames.append({
                'step': i,
                'smpl_betas': interp_betas.tolist(),
                'progress': round(t * 100, 1),
            })

        return {
            'steps': steps,
            'frames': frames,
            'from_betas': from_betas,
            'to_betas': to_betas,
        }

    def _generate_mesh(self, betas: np.ndarray) -> Dict:
        """Generate simplified mesh from betas"""
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

        return {'vertices': vertices, 'faces': faces}

    def _export_mesh_obj(self, mesh: Dict, filepath: Path):
        """Export mesh to OBJ format"""
        with open(filepath, 'w') as f:
            f.write(f"# PhysiqAI Avatar Mesh\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n\n")

            for v in mesh['vertices']:
                f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")

            for face in mesh['faces']:
                f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")

    def _generate_avatar_image(self, betas: np.ndarray, user: User,
                                avatar_id: str, label: str = "",
                                with_pump: bool = False,
                                size: Tuple[int, int] = (400, 600)) -> Path:
        """Generate avatar image visualization"""
        try:
            from PIL import Image, ImageDraw, ImageFont

            width, height = size
            img = Image.new('RGB', (width, height), color='#1a1a2e')
            draw = ImageDraw.Draw(img)

            center_x = width // 2
            head_y = height // 8

            # Scale factors from betas
            size_factor = 1.0 + betas[0] * 0.1
            height_factor = 1.0 + betas[1] * 0.05
            shoulder_factor = 1.0 + betas[3] * 0.1
            arm_factor = 1.0 + betas[4] * 0.1
            leg_factor = 1.0 + betas[5] * 0.1
            chest_factor = 1.0 + betas[6] * 0.1
            hip_factor = 1.0 + betas[7] * 0.1

            # Pump effect
            pump_mult = 1.05 if with_pump else 1.0

            # Colors
            body_color = '#4A90E2'
            outline_color = '#6BB6FF'

            # Head
            head_size = int(35 * size_factor)
            draw.ellipse([center_x - head_size, head_y - head_size,
                         center_x + head_size, head_y + head_size],
                        fill=body_color, outline=outline_color, width=3)

            # Torso
            torso_top = head_y + head_size + 10
            torso_height = int(120 * height_factor)

            shoulder_width = int(60 * size_factor * shoulder_factor * pump_mult)
            waist_width = int(45 * size_factor * pump_mult)
            chest_width = int(shoulder_width * 0.9 * chest_factor * pump_mult)

            # Upper torso (chest/shoulders)
            draw.polygon([
                (center_x - shoulder_width, torso_top),
                (center_x + shoulder_width, torso_top),
                (center_x + chest_width, torso_top + torso_height // 2),
                (center_x - chest_width, torso_top + torso_height // 2),
            ], fill=body_color, outline=outline_color, width=2)

            # Lower torso (waist)
            draw.polygon([
                (center_x - chest_width, torso_top + torso_height // 2),
                (center_x + chest_width, torso_top + torso_height // 2),
                (center_x + waist_width, torso_top + torso_height),
                (center_x - waist_width, torso_top + torso_height),
            ], fill=body_color, outline=outline_color, width=2)

            # Hips
            hip_top = torso_top + torso_height
            hip_height = int(50 * height_factor * hip_factor)
            hip_width = int(55 * size_factor * hip_factor)

            draw.polygon([
                (center_x - waist_width, hip_top),
                (center_x + waist_width, hip_top),
                (center_x + hip_width, hip_top + hip_height),
                (center_x - hip_width, hip_top + hip_height),
            ], fill=body_color, outline=outline_color, width=2)

            # Legs
            leg_top = hip_top + hip_height
            leg_height = int(150 * height_factor)
            leg_width = int(20 * size_factor * leg_factor)

            # Left leg
            draw.polygon([
                (center_x - hip_width + 10, leg_top),
                (center_x - 10, leg_top),
                (center_x - 15, leg_top + leg_height),
                (center_x - hip_width + 5, leg_top + leg_height),
            ], fill=body_color, outline=outline_color, width=2)

            # Right leg
            draw.polygon([
                (center_x + 10, leg_top),
                (center_x + hip_width - 10, leg_top),
                (center_x + hip_width - 5, leg_top + leg_height),
                (center_x + 15, leg_top + leg_height),
            ], fill=body_color, outline=outline_color, width=2)

            # Arms
            arm_length = int(100 * height_factor)
            arm_width = int(15 * size_factor * arm_factor * pump_mult)

            # Left arm
            draw.polygon([
                (center_x - shoulder_width, torso_top + 10),
                (center_x - shoulder_width + arm_width * 2, torso_top + 10),
                (center_x - shoulder_width + arm_width, torso_top + arm_length),
                (center_x - shoulder_width - arm_width, torso_top + arm_length),
            ], fill=body_color, outline=outline_color, width=2)

            # Right arm
            draw.polygon([
                (center_x + shoulder_width - arm_width * 2, torso_top + 10),
                (center_x + shoulder_width, torso_top + 10),
                (center_x + shoulder_width + arm_width, torso_top + arm_length),
                (center_x + shoulder_width - arm_width, torso_top + arm_length),
            ], fill=body_color, outline=outline_color, width=2)

            # Add label
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
                small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
            except:
                font = ImageFont.load_default()
                small_font = font

            if label:
                draw.text((10, height - 60), label, fill='white', font=font)

            draw.text((10, height - 40), f"{user.name}", fill='white', font=font)

            # Add measurements if available
            if user.current_weight_kg:
                draw.text((10, height - 20), f"{user.current_weight_kg:.1f} kg", fill='#888888', font=small_font)

            # Save
            image_path = self.output_dir / f"{user.id}_{avatar_id}_avatar.png"
            img.save(image_path)

            return image_path

        except ImportError:
            # PIL not available, create placeholder
            image_path = self.output_dir / f"{user.id}_{avatar_id}_avatar.png"
            with open(image_path, 'w') as f:
                f.write("Avatar image placeholder - PIL not installed")
            return image_path

    def _apply_pump_to_betas(self, betas: np.ndarray, pump_muscles: Dict[str, float]) -> np.ndarray:
        """Apply muscle pump to SMPL betas"""
        adjusted = betas.copy()

        # Map muscle groups to beta indices
        muscle_to_beta = {
            'biceps': 4, 'triceps': 4, 'forearms': 4,  # Arms
            'quads': 5, 'hamstrings': 5, 'calves': 5,  # Legs
            'chest': 6,
            'glutes': 7, 'hips': 7,
        }

        for muscle, pump in pump_muscles.items():
            if muscle in muscle_to_beta and pump > 0:
                beta_idx = muscle_to_beta[muscle]
                adjusted[beta_idx] += pump * 0.1  # Small temporary adjustment

        return np.clip(adjusted, -3, 3)

    def _measurements_to_betas(self, measurement) -> np.ndarray:
        """Convert body measurements to SMPL betas"""
        betas = np.zeros(10)

        if measurement.weight_kg:
            # Beta 0 correlates with overall size/weight
            betas[0] = (measurement.weight_kg - 70) / 15

        if measurement.bmi:
            # Beta 1 correlates with height/weight ratio
            betas[1] = (measurement.bmi - 22) / 5

        return np.clip(betas, -3, 3)

    def _generate_comparison_avatar(self, betas: np.ndarray, user: User,
                                     suffix: str) -> Dict:
        """Generate avatar for comparison"""
        avatar_id = str(uuid.uuid4())[:8]

        mesh = self._generate_mesh(betas)
        mesh_path = self.output_dir / f"{user.id}_{avatar_id}_{suffix}.obj"
        self._export_mesh_obj(mesh, mesh_path)

        image_path = self._generate_avatar_image(betas, user, avatar_id, label=suffix)

        return {
            'avatar_id': avatar_id,
            'mesh_path': str(mesh_path),
            'image_path': str(image_path),
            'smpl_betas': betas.tolist(),
        }

    def _generate_default_comparison(self, user: User) -> Dict:
        """Generate default comparison when no data available"""
        default_betas = [0.0] * 10

        return {
            'before': {
                'date': datetime.now().isoformat(),
                'avatar': self._generate_comparison_avatar(np.array(default_betas), user, "before"),
                'measurements': {},
            },
            'after': {
                'date': datetime.now().isoformat(),
                'avatar': self._generate_comparison_avatar(np.array(default_betas), user, "after"),
                'measurements': {},
            },
            'changes': {
                'weight_kg': 0,
                'body_fat_pct': 0,
                'days_between': 0,
                'note': 'No measurement data available',
            },
        }


# Singleton instance
avatar_generator = AvatarGenerator()


if __name__ == "__main__":
    print("Avatar Generator Service")
    print("=" * 60)
    print("\nThis service generates and morphs 3D avatars.")
    print("Import and use AvatarGenerator class in your application.")
    print("\nExample:")
    print("  from backend.services.avatar_generator import avatar_generator")
    print("  avatar = avatar_generator.generate_current_avatar(user)")
