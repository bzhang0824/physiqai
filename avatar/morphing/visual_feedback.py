#!/usr/bin/env python3
"""
visual_feedback.py - Visual Feedback System

Generates visual cues to differentiate muscle gain vs fat loss,
creates comparison renders, and produces heatmaps of body changes.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum
from pathlib import Path

from .body_mapper import BodyState
from .vertex_displacement import MuscleGroup


class ChangeVisualizationType(Enum):
    """Types of body changes with distinct visual treatments"""
    MUSCLE_GAIN = "muscle_gain"      # Blue-white glow, fullness
    FAT_LOSS = "fat_loss"            # Edge lighting, definition
    PUMP = "pump"                    # Red tint, vascularity
    WEIGHT_GAIN = "weight_gain"      # Softening, scale increase
    WEIGHT_LOSS = "weight_loss"      # Sharpening, scale decrease


@dataclass
class VisualEffect:
    """Shader effect parameters"""
    effect_type: str
    intensity: float  # 0-1
    color: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    region: Optional[str] = None


class VisualFeedbackSystem:
    """
    Generates visual feedback for body changes.

    Uses shader parameters, highlighting, and annotations
    to make changes immediately understandable.
    """

    def __init__(self):
        self.effect_presets = self._init_effect_presets()

    def _init_effect_presets(self) -> Dict[ChangeVisualizationType, dict]:
        """Initialize visual effect presets"""
        return {
            ChangeVisualizationType.MUSCLE_GAIN: {
                'emissive_color': (0.2, 0.5, 1.0),  # Blue-white
                'emissive_intensity': 0.3,
                'specular_boost': 1.4,
                'rim_light': False,
                'pulse_frequency': 0.5,
                'description': 'Growing muscle appears with blue-white glow'
            },
            ChangeVisualizationType.FAT_LOSS: {
                'emissive_color': (1.0, 0.8, 0.2),  # Gold
                'emissive_intensity': 0.2,
                'specular_boost': 1.2,
                'rim_light': True,
                'rim_color': (0.9, 0.95, 1.0),
                'rim_intensity': 0.4,
                'description': 'Definition increases with gold edge lighting'
            },
            ChangeVisualizationType.PUMP: {
                'emissive_color': (1.0, 0.3, 0.2),  # Red-orange
                'emissive_intensity': 0.4,
                'specular_boost': 1.5,
                'rim_light': False,
                'vascularity_boost': 0.7,
                'description': 'Pump shows as red vascularity'
            },
            ChangeVisualizationType.WEIGHT_GAIN: {
                'emissive_color': (0.8, 0.7, 0.6),  # Neutral
                'emissive_intensity': 0.1,
                'specular_boost': 0.9,  # Softer
                'rim_light': False,
                'subsurface_scattering': 0.3,
                'description': 'Overall softening and scale increase'
            },
            ChangeVisualizationType.WEIGHT_LOSS: {
                'emissive_color': (0.6, 0.8, 0.7),  # Green tint
                'emissive_intensity': 0.15,
                'specular_boost': 1.1,
                'rim_light': True,
                'rim_color': (0.7, 0.9, 0.8),
                'rim_intensity': 0.3,
                'description': 'Sharpening and angular features'
            }
        }

    def get_shader_params(self, change_type: ChangeVisualizationType,
                         intensity: float = 1.0,
                         muscle_group: Optional[MuscleGroup] = None) -> dict:
        """
        Get shader parameters for a specific change type.

        Args:
            change_type: Type of body change
            intensity: Effect intensity (0-1)
            muscle_group: Specific muscle (if applicable)

        Returns:
            Dictionary of shader uniforms
        """
        preset = self.effect_presets.get(change_type, {})

        params = {
            'u_emissiveColor': preset.get('emissive_color', (1, 1, 1)),
            'u_emissiveIntensity': preset.get('emissive_intensity', 0) * intensity,
            'u_specularBoost': preset.get('specular_boost', 1.0),
            'u_rimLight': preset.get('rim_light', False),
            'u_rimColor': preset.get('rim_color', (1, 1, 1)),
            'u_rimIntensity': preset.get('rim_intensity', 0) * intensity,
            'u_vascularity': preset.get('vascularity_boost', 0) * intensity,
            'u_pulseSpeed': preset.get('pulse_frequency', 0),
            'u_subsurface': preset.get('subsurface_scattering', 0.1),
        }

        if muscle_group:
            params['u_targetMuscle'] = muscle_group.value

        return params

    def compare_states(self, before: BodyState, after: BodyState) -> dict:
        """
        Generate comparison between two body states.

        Returns:
            Dict with changes detected and visual effects to apply
        """
        changes = []

        # Weight change
        weight_delta = after.weight - before.weight
        if abs(weight_delta) > 0.5:
            if weight_delta > 0:
                changes.append({
                    'type': ChangeVisualizationType.WEIGHT_GAIN,
                    'magnitude': weight_delta,
                    'description': f'+{weight_delta:.1f} lbs'
                })
            else:
                changes.append({
                    'type': ChangeVisualizationType.WEIGHT_LOSS,
                    'magnitude': abs(weight_delta),
                    'description': f'{weight_delta:.1f} lbs'
                })

        # Muscle change
        muscle_delta = after.muscle_pct - before.muscle_pct
        if abs(muscle_delta) > 0.5:
            changes.append({
                'type': ChangeVisualizationType.MUSCLE_GAIN,
                'magnitude': muscle_delta,
                'description': f'+{muscle_delta:.1f}% muscle'
            })

        # Fat change
        fat_delta = after.fat_pct - before.fat_pct
        if fat_delta < -0.5:
            changes.append({
                'type': ChangeVisualizationType.FAT_LOSS,
                'magnitude': abs(fat_delta),
                'description': f'{fat_delta:.1f}% fat'
            })

        # Generate visual effects for each change
        effects = []
        for change in changes:
            effect = self.get_shader_params(
                change['type'],
                intensity=min(abs(change['magnitude']) / 5, 1.0)
            )
            effect['description'] = change['description']
            effect['change_type'] = change['type'].value
            effects.append(effect)

        return {
            'changes': changes,
            'effects': effects,
            'before_stats': before.to_dict(),
            'after_stats': after.to_dict()
        }

    def generate_heatmap(self, vertices_history: List[np.ndarray],
                        timeframe_days: int = 30) -> np.ndarray:
        """
        Generate color-coded heatmap of body changes.

        Returns per-vertex colors showing where changes occurred.

        Color coding:
        - Red = Growing (muscle gain)
        - Blue = Shrinking (fat loss)
        - Purple = Both (recomposition)
        - Gray = No change
        """
        if len(vertices_history) < 2:
            return np.zeros((len(vertices_history[0]), 3))

        # Calculate total displacement over timeframe
        start_vertices = vertices_history[0]
        end_vertices = vertices_history[-1]

        displacement = end_vertices - start_vertices
        displacement_mag = np.linalg.norm(displacement, axis=1)

        # Calculate direction relative to surface normal
        # This would need actual normals, approximating here
        outward_component = displacement[:, 2]  # Simplified Z-component

        # Color based on change type
        colors = np.zeros((len(start_vertices), 3))

        # Growing = Red (positive outward displacement)
        growing_mask = outward_component > 0.001
        colors[growing_mask] = [1.0, 0.3, 0.2]

        # Shrinking = Blue (negative outward displacement)
        shrinking_mask = outward_component < -0.001
        colors[shrinking_mask] = [0.2, 0.5, 1.0]

        # Scale intensity by magnitude
        max_disp = displacement_mag.max()
        if max_disp > 0:
            intensity = np.clip(displacement_mag / max_disp, 0.2, 1.0)
            colors = colors * intensity[:, np.newaxis]

        return colors

    def create_comparison_render(self, before_verts: np.ndarray,
                                 after_verts: np.ndarray,
                                 view_angle: str = 'front') -> dict:
        """
        Create side-by-side comparison render.

        Args:
            before_verts: Before mesh vertices
            after_verts: After mesh vertices
            view_angle: 'front', 'side', 'back', '3d'

        Returns:
            Render configuration and annotations
        """
        # Calculate changes for annotations
        volume_before = self._estimate_volume(before_verts)
        volume_after = self._estimate_volume(after_verts)
        volume_change = volume_after - volume_before

        return {
            'layout': 'split_screen',
            'before': {
                'vertices': before_verts,
                'label': 'Before',
                'position': 'left'
            },
            'after': {
                'vertices': after_verts,
                'label': 'After',
                'position': 'right'
            },
            'view_angle': view_angle,
            'annotations': [
                {
                    'type': 'stat_change',
                    'label': 'Volume Change',
                    'value': f'{volume_change:+.1f} L',
                    'position': 'bottom_center'
                }
            ],
            'effects': {
                'before': {'grayscale': False},
                'after': {'highlight_changes': True}
            }
        }

    def _estimate_volume(self, vertices: np.ndarray) -> float:
        """
        Rough volume estimate from vertices.

        Simplified - actual volume requires face information.
        """
        # Bounding box approximation
        mins = vertices.min(axis=0)
        maxs = vertices.max(axis=0)
        dimensions = maxs - mins

        # Rough ellipsoid volume
        volume = 4/3 * np.pi * np.prod(dimensions / 2)

        # Scale factor for body density
        return volume * 1000  # Convert to liters approximation

    def generate_progress_timeline(self,
                                  states: List[BodyState],
                                  interval: str = 'weekly') -> List[dict]:
        """
        Generate visual timeline of progress.

        Creates keyframes with effects for video/animation.
        """
        timeline = []

        for i, state in enumerate(states):
            if i == 0:
                effects = []
            else:
                # Compare to previous
                comparison = self.compare_states(states[i-1], state)
                effects = comparison['effects']

            timeline.append({
                'frame': i,
                'state': state.to_dict(),
                'effects': effects,
                'label': f'Week {i}' if interval == 'weekly' else f'Day {i}'
            })

        return timeline


# WebGL/Three.js shader code for reference
SHADER_CODE = {
    'vertex': """
        varying vec3 vNormal;
        varying vec3 vPosition;
        varying float vMuscleMask;

        uniform float u_time;
        uniform vec3 u_targetMuscleCenter;
        uniform float u_targetMuscleRadius;

        void main() {
            vNormal = normalize(normalMatrix * normal);
            vPosition = position;

            // Muscle region mask (simplified)
            float dist = distance(position, u_targetMuscleCenter);
            vMuscleMask = 1.0 - smoothstep(0.0, u_targetMuscleRadius, dist);

            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
    """,

    'fragment': """
        varying vec3 vNormal;
        varying vec3 vPosition;
        varying float vMuscleMask;

        uniform vec3 u_emissiveColor;
        uniform float u_emissiveIntensity;
        uniform float u_specularBoost;
        uniform bool u_rimLight;
        uniform vec3 u_rimColor;
        uniform float u_rimIntensity;
        uniform float u_vascularity;
        uniform float u_time;
        uniform float u_pulseSpeed;

        void main() {
            vec3 normal = normalize(vNormal);
            vec3 viewDir = normalize(cameraPosition - vPosition);

            // Base color
            vec3 baseColor = vec3(0.8, 0.7, 0.6);

            // Pulse effect for muscle gain
            float pulse = sin(u_time * u_pulseSpeed * 6.28) * 0.5 + 0.5;
            float pulseMask = u_pulseSpeed > 0.0 ? pulse * vMuscleMask : 0.0;

            // Emissive glow
            vec3 emissive = u_emissiveColor * u_emissiveIntensity * (1.0 + pulseMask);

            // Specular boost
            float specular = pow(max(dot(reflect(-viewDir, normal), viewDir), 0.0), 32.0);
            specular *= u_specularBoost;

            // Rim lighting for definition
            vec3 rim = vec3(0.0);
            if (u_rimLight) {
                float rimFactor = 1.0 - max(dot(viewDir, normal), 0.0);
                rim = u_rimColor * pow(rimFactor, 3.0) * u_rimIntensity;
            }

            // Vascularity (procedural veins)
            float veins = 0.0;
            if (u_vascularity > 0.0) {
                float noise = sin(vPosition.x * 50.0) * sin(vPosition.y * 50.0);
                veins = smoothstep(0.7, 0.9, noise) * u_vascularity;
            }

            // Combine
            vec3 finalColor = baseColor + emissive + vec3(specular) + rim;
            finalColor += vec3(veins * 0.5, 0.0, 0.0);  // Red veins

            gl_FragColor = vec4(finalColor, 1.0);
        }
    """
}


def demo_visual_feedback():
    """Demonstrate visual feedback system"""
    print("Visual Feedback System Demo")
    print("=" * 60)

    from body_mapper import BodyState

    feedback = VisualFeedbackSystem()

    # Show effect presets
    print("\nVisual Effect Presets:")
    print("-" * 60)

    for change_type in ChangeVisualizationType:
        preset = feedback.effect_presets[change_type]
        print(f"\n{change_type.value.upper()}:")
        print(f"  {preset['description']}")
        print(f"  Emissive: RGB{preset['emissive_color']}, "
              f"intensity: {preset['emissive_intensity']}")
        if preset.get('rim_light'):
            print(f"  Rim light: RGB{preset['rim_color']}, "
                  f"intensity: {preset['rim_intensity']}")

    # Compare two body states
    print("\n" + "=" * 60)
    print("\nComparing Body States:")
    print("-" * 60)

    before = BodyState(weight=180, muscle_pct=35, fat_pct=25)
    after = BodyState(weight=178, muscle_pct=38, fat_pct=20)

    comparison = feedback.compare_states(before, after)

    print(f"\nChanges detected: {len(comparison['changes'])}")
    for change in comparison['changes']:
        print(f"  • {change['type'].value}: {change['description']}")

    print(f"\nShader effects to apply:")
    for effect in comparison['effects']:
        print(f"  • {effect['change_type']}: "
              f"emissive={effect['u_emissiveIntensity']:.2f}, "
              f"rim={effect['u_rimLight']}")


if __name__ == "__main__":
    demo_visual_feedback()
