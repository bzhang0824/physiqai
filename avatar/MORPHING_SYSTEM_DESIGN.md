# Body Parameter Morphing System Design

## Executive Summary

This document outlines a hybrid morphing system that combines **SMPL shape parameters (betas)** with **strategic vertex displacement** to create a realistic, controllable body transformation engine for PhysiqAI.

**Recommendation: Use SMPL betas as the foundation + vertex displacement for localized muscle details**

---

## 1. Body Parameters Definition

### 1.1 Core Physiological Parameters (3 Primary)

| Parameter | Range | Units | Data Source |
|-----------|-------|-------|-------------|
| **Total Body Weight** | 80-400 | lbs | User input / smart scale |
| **Muscle Mass %** | 15-60 | % | BIA scale / estimated from lifts |
| **Body Fat %** | 5-50 | % | BIA scale / visual estimation |

### 1.2 Key Measurements (7 Secondary)

| Measurement | Location | Units | Morph Target |
|-------------|----------|-------|--------------|
| **Chest** | Nipple line circumference | inches | Torso width |
| **Waist** | Narrowest abdominal point | inches | Waist taper |
| **Hips** | Widest glute point | inches | Hip width |
| **Shoulders** | Acromion-to-acromion | inches | Shoulder width |
| **Arms** | Flexed bicep peak | inches | Arm thickness |
| **Thighs** | Mid-thigh circumference | inches | Leg thickness |
| **Calves** | Widest calf point | inches | Lower leg thickness |

### 1.3 Derived Parameters (Calculated)

```python
# BMI (Body Mass Index)
bmi = (weight_lbs * 0.453592) / (height_m ** 2)

# FFMI (Fat-Free Mass Index) - key for muscle tracking
lean_mass_kg = (weight_lbs * 0.453592) * (1 - body_fat_pct / 100)
ffmi = lean_mass_kg / (height_m ** 2)

# Body Shape Index (ABSI) - health indicator
absi = waist_m / (bmi ** (2/3) * height_m ** (1/2))

# Somatotype classification
# Endomorphy (fat), Mesomorphy (muscle), Ectomorphy (slim)
```

---

## 2. SMPL Morphing Architecture

### 2.1 Why SMPL Betas (Shape Parameters)?

SMPL uses **10 principal shape coefficients (betas)** derived from PCA on thousands of body scans:

```
β₀ = Overall body size (scale)
β₁ = Height vs width ratio  
β₂ = Upper body proportion
β₃ = Lower body proportion
β₄ = Body fat distribution
β₅-β₉ = Fine shape details
```

**Advantages of using betas:**
- ✅ Mathematically valid body shapes (no impossible morphs)
- ✅ Captures realistic body proportions
- ✅ Smooth interpolation guaranteed
- ✅ Low-dimensional (10 params vs 6890 vertices)
- ✅ Gender-specific models (M/F/Neutral)

### 2.2 Mapping Body Parameters to SMPL Betas

```python
class BodyToSMPLMapper:
    """
    Maps high-level body parameters to SMPL beta coefficients
    """
    
    def __init__(self, gender='neutral'):
        self.gender = gender
        # Pre-trained mapping weights (from our dataset)
        self.weight_to_beta = np.array([0.8, 0.1, 0.05, 0.03, 0.02, 0, 0, 0, 0, 0])
        self.muscle_to_beta = np.array([0.1, 0.3, 0.4, 0.1, 0.05, 0.02, 0.02, 0.01, 0, 0])
        self.fat_to_beta = np.array([0.6, 0.1, 0.05, 0.1, 0.1, 0.02, 0.02, 0.01, 0, 0])
    
    def map_to_betas(self, weight, muscle_pct, fat_pct, measurements=None):
        """
        Convert body parameters to SMPL beta vector
        
        Args:
            weight: Total body weight (lbs)
            muscle_pct: Muscle mass percentage (0-100)
            fat_pct: Body fat percentage (0-100)
            measurements: Optional dict of 7 measurements
        
        Returns:
            betas: 10-element SMPL shape parameter vector
        """
        # Normalize inputs
        weight_norm = (weight - 180) / 100  # Center around 180 lbs
        muscle_norm = (muscle_pct - 30) / 30  # Center around 30%
        fat_norm = (fat_pct - 25) / 25  # Center around 25%
        
        # Linear combination approach
        betas = (
            self.weight_to_beta * weight_norm +
            self.muscle_to_beta * muscle_norm +
            self.fat_to_beta * fat_norm
        )
        
        # Apply measurement constraints if provided
        if measurements:
            betas = self._apply_measurement_constraints(betas, measurements)
        
        return betas
    
    def _apply_measurement_constraints(self, betas, measurements):
        """
        Fine-tune betas to match specific body measurements
        Uses iterative optimization to minimize measurement error
        """
        # Generate initial mesh
        vertices = self.smpl_model(betas=betas)
        
        # Calculate current measurements from mesh
        current = self._measure_from_mesh(vertices)
        
        # Compute deltas
        delta_chest = (measurements['chest'] - current['chest']) / current['chest']
        delta_waist = (measurements['waist'] - current['waist']) / current['waist']
        
        # Adjust betas based on deltas
        # This requires pre-computed Jacobian: ∂measurement/∂beta
        adjustment = self.jacobian_pseudoinverse @ np.array([
            delta_chest, delta_waist, delta_hips, 
            delta_shoulders, delta_arms, delta_thighs, delta_calves
        ])
        
        return betas + adjustment * 0.1  # Small step for stability
```

### 2.3 When to Use Vertex Displacement

**Use vertex displacement for:**
- Localized muscle hypertrophy (bicep peak, chest fullness)
- Pose-dependent muscle activation (flexing)
- Fine surface details (vascularity, muscle separation)
- Real-time "pump" effect during/after workouts

**DO NOT use for:**
- Overall body shape (use betas)
- Skeleton/proportions (use betas)
- Weight changes (use betas)

```python
class MuscleDisplacementSystem:
    """
    Adds localized muscle displacement on top of SMPL base mesh
    """
    
    def __init__(self):
        # Muscle region vertex indices (pre-computed from SMPL topology)
        self.muscle_regions = {
            'biceps': {'indices': [...], 'center': (x, y, z), 'radius': 0.15},
            'chest': {'indices': [...], 'center': (x, y, z), 'radius': 0.20},
            'shoulders': {'indices': [...], 'center': (x, y, z), 'radius': 0.18},
            'quads': {'indices': [...], 'center': (x, y, z), 'radius': 0.25},
            'lats': {'indices': [...], 'center': (x, y, z), 'radius': 0.22},
            'abs': {'indices': [...], 'center': (x, y, z), 'radius': 0.15},
        }
        
        # Maximum displacement per muscle (in meters)
        self.max_displacement = {
            'biceps': 0.015,
            'chest': 0.020,
            'shoulders': 0.018,
            'quads': 0.025,
            'lats': 0.015,
            'abs': 0.010,
        }
    
    def apply_muscle_pump(self, base_vertices, muscle_activations):
        """
        Apply localized vertex displacement based on muscle activation
        
        Args:
            base_vertices: SMPL mesh vertices (6890, 3)
            muscle_activations: Dict of activation levels (0-1) per muscle
        
        Returns:
            displaced_vertices: Modified vertices with muscle pump
        """
        displaced = base_vertices.copy()
        
        for muscle, activation in muscle_activations.items():
            if muscle not in self.muscle_regions:
                continue
            
            region = self.muscle_regions[muscle]
            max_disp = self.max_displacement[muscle] * activation
            
            for idx in region['indices']:
                vertex = displaced[idx]
                
                # Calculate distance from muscle center
                distance = np.linalg.norm(vertex - region['center'])
                
                # Gaussian falloff for smooth transition
                influence = np.exp(-(distance ** 2) / (2 * region['radius'] ** 2))
                
                # Displace along normal direction
                normal = self._get_vertex_normal(idx)
                displacement = normal * max_disp * influence
                
                displaced[idx] += displacement
        
        return displaced
```

---

## 3. Smooth Interpolation System

### 3.1 Interpolation Requirements

- **Visual smoothness**: 60fps minimum during morphs
- **Physical plausibility**: No body parts passing through each other
- **Temporal coherence**: Consistent speed, no jumps
- **User control**: Configurable morph duration

### 3.2 Multi-Level Interpolation Strategy

```python
class MorphInterpolator:
    """
    Handles smooth transitions between body states
    """
    
    def __init__(self, duration_seconds=2.0, fps=60):
        self.duration = duration_seconds
        self.fps = fps
        self.total_frames = int(duration_seconds * fps)
        
        # Easing functions for natural feel
        self.easings = {
            'linear': lambda t: t,
            'ease_in_out': lambda t: t**2 * (3 - 2*t),  # Smoothstep
            'ease_out_bounce': self._bounce_ease,
            'ease_out_elastic': self._elastic_ease,
        }
    
    def interpolate_states(self, state_a, state_b, easing='ease_in_out'):
        """
        Generate smooth transition between two body states
        
        Args:
            state_a: Starting BodyState (weight, muscle, fat, measurements)
            state_b: Target BodyState
            easing: Easing function name
        
        Returns:
            List of interpolated states for each frame
        """
        easing_fn = self.easings[easing]
        states = []
        
        for frame in range(self.total_frames + 1):
            t = frame / self.total_frames
            eased_t = easing_fn(t)
            
            # Interpolate each parameter
            state = BodyState(
                weight=self._lerp(state_a.weight, state_b.weight, eased_t),
                muscle_pct=self._lerp(state_a.muscle_pct, state_b.muscle_pct, eased_t),
                fat_pct=self._lerp(state_a.fat_pct, state_b.fat_pct, eased_t),
                measurements={
                    k: self._lerp(state_a.measurements[k], state_b.measurements[k], eased_t)
                    for k in state_a.measurements
                }
            )
            states.append(state)
        
        return states
    
    def interpolate_betas(self, betas_a, betas_b, easing='ease_in_out'):
        """
        Direct SMPL beta interpolation (most efficient)
        """
        easing_fn = self.easings[easing]
        beta_trajectory = []
        
        for frame in range(self.total_frames + 1):
            t = frame / self.total_frames
            eased_t = easing_fn(t)
            
            # Linear interpolation of beta vectors
            interp_betas = betas_a * (1 - eased_t) + betas_b * eased_t
            beta_trajectory.append(interp_betas)
        
        return beta_trajectory
```

### 3.3 Pre-computed Morph Targets

For real-time performance, pre-compute meshes at key body states:

```python
class MorphTargetCache:
    """
    Pre-computed meshes for common body states
    """
    
    def __init__(self, smpl_model):
        self.smpl = smpl_model
        self.cache = {}
        
        # Generate grid of body states
        weights = np.linspace(120, 300, 10)  # 10 weight levels
        muscle_pcts = np.linspace(15, 50, 5)  # 5 muscle levels
        fat_pcts = np.linspace(8, 45, 5)  # 5 fat levels
        
        for w in weights:
            for m in muscle_pcts:
                for f in fat_pcts:
                    betas = self._body_to_betas(w, m, f)
                    vertices = self.smpl(betas=betas)
                    key = (round(w), round(m), round(f))
                    self.cache[key] = vertices
    
    def get_nearest(self, weight, muscle_pct, fat_pct):
        """Get nearest cached mesh for fast preview"""
        w = round(weight / 20) * 20  # Quantize to nearest 20 lbs
        m = round(muscle_pct / 10) * 10  # Quantize to nearest 10%
        f = round(fat_pct / 10) * 10
        return self.cache.get((w, m, f))
    
    def interpolate_cached(self, state, k=4):
        """
        k-nearest interpolation from cached states
        Faster than full SMPL forward pass
        """
        # Find k nearest cached states
        neighbors = self._find_k_nearest(state, k)
        
        # Weighted average based on distance
        weights = [1 / (1 + self._state_distance(state, n)) for n in neighbors]
        total = sum(weights)
        weights = [w / total for w in weights]
        
        # Blend vertex positions
        result = np.zeros_like(neighbors[0].vertices)
        for neighbor, weight in zip(neighbors, weights):
            result += neighbor.vertices * weight
        
        return result
```

---

## 4. Real-Time Update System

### 4.1 Workout-to-Morph Pipeline

```python
class WorkoutMorphEngine:
    """
    Converts workout logs into real-time avatar updates
    """
    
    def __init__(self):
        self.muscle_recovery_model = MuscleRecoveryModel()
        self.fat_burn_model = FatBurnModel()
        self.water_retention_model = WaterRetentionModel()
    
    def process_workout(self, workout_data):
        """
        Calculate immediate and long-term body changes from workout
        
        Args:
            workout_data: {
                'exercises': [...],
                'volume': total_weight_lifted,
                'duration': minutes,
                'intensity': 1-10,
                'timestamp': datetime
            }
        
        Returns:
            morph_update: Immediate visual changes
            projected_changes: Long-term adaptation predictions
        """
        # Immediate effects (pump, water shift)
        immediate = self._calculate_immediate_effects(workout_data)
        
        # Long-term adaptations (muscle growth, fat loss)
        projected = self._calculate_adaptations(workout_data)
        
        return {
            'immediate': immediate,
            'projected': projected,
            'timeline': self._generate_adaptation_timeline(projected)
        }
    
    def _calculate_immediate_effects(self, workout):
        """
        Pump, vascularity, and temporary swelling
        Lasts 1-3 hours post-workout
        """
        muscle_pump = {}
        
        for exercise in workout['exercises']:
            muscle_group = exercise['muscle_group']
            volume = exercise['sets'] * exercise['reps'] * exercise['weight']
            
            # Pump factor based on volume and exercise type
            if exercise['type'] in ['isolation', 'hypertrophy']:
                pump_factor = min(volume / 1000, 1.0)  # Cap at 1.0
            else:
                pump_factor = min(volume / 2000, 0.7)  # Lower for compound
            
            muscle_pump[muscle_group] = {
                'swelling': pump_factor * 0.3,  # 30% max swelling
                'vascularity': pump_factor * 0.5,
                'duration_minutes': 60 + pump_factor * 120
            }
        
        return muscle_pump
    
    def _calculate_adaptations(self, workout):
        """
        Long-term muscle growth and fat loss projections
        """
        # Training stimulus calculation
        total_volume = workout['volume']
        intensity = workout['intensity']
        
        # Muscle protein synthesis (MPS) elevation
        # MPS elevated for 24-48 hours post-workout
        mps_elevation = min(intensity * 0.15, 2.0)  # Max 2x baseline
        
        # Predicted muscle gain (over weeks)
        # Simplified: ~0.25-0.5 lbs muscle per week for beginners
        # ~0.1-0.25 lbs for intermediate/advanced
        weekly_muscle_gain = self._estimate_muscle_gain_rate(workout)
        
        # Fat loss from workout (minimal directly, but contributes to deficit)
        calories_burned = self._estimate_calories_burned(workout)
        fat_loss_lbs = calories_burned / 3500  # 3500 calories = 1 lb fat
        
        return {
            'muscle_gain_per_week': weekly_muscle_gain,
            'fat_loss_per_session': fat_loss_lbs,
            'mps_elevation_duration_hours': 24 + intensity * 2,
            'recovery_time_hours': self._estimate_recovery(workout)
        }
```

### 4.2 Progressive Update Queue

```python
class ProgressiveMorphQueue:
    """
    Manages a queue of body changes to apply over time
    Simulates realistic body recomposition timeline
    """
    
    def __init__(self):
        self.pending_changes = []
        self.current_state = None
    
    def add_workout(self, workout_data):
        """
        Queue body changes from a workout
        """
        engine = WorkoutMorphEngine()
        effects = engine.process_workout(workout_data)
        
        # Add to queue with timestamps
        immediate = effects['immediate']
        projected = effects['projected']
        
        # Immediate pump (apply now)
        self.pending_changes.append({
            'type': 'pump',
            'effects': immediate,
            'start_time': datetime.now(),
            'duration_hours': 2
        })
        
        # Muscle growth (apply over weeks)
        self.pending_changes.append({
            'type': 'muscle_growth',
            'amount': projected['muscle_gain_per_week'] / 7,  # Daily rate
            'start_time': datetime.now() + timedelta(days=1),
            'duration_days': 30  # Visible over a month
        })
        
        # Fat loss (apply over time)
        if projected['fat_loss_per_session'] > 0:
            self.pending_changes.append({
                'type': 'fat_loss',
                'amount': projected['fat_loss_per_session'],
                'start_time': datetime.now() + timedelta(hours=6),
                'duration_days': 1
            })
    
    def update(self, current_time):
        """
        Apply pending changes up to current time
        Called every frame or every few seconds
        """
        active_changes = [
            c for c in self.pending_changes 
            if c['start_time'] <= current_time
        ]
        
        for change in active_changes:
            progress = self._calculate_progress(change, current_time)
            self._apply_change(change, progress)
    
    def _apply_change(self, change, progress):
        if change['type'] == 'pump':
            # Apply vertex displacement for pump effect
            self.current_state.apply_muscle_pump(change['effects'], progress)
        
        elif change['type'] == 'muscle_growth':
            # Update body composition
            self.current_state.muscle_mass += change['amount'] * progress
            self.current_state.recalculate_betas()
        
        elif change['type'] == 'fat_loss':
            self.current_state.fat_mass -= change['amount'] * progress
            self.current_state.recalculate_betas()
```

---

## 5. Visual Feedback: Muscle Gain vs Fat Loss

### 5.1 Differentiating Visual Changes

| Change Type | Visual Cues | Shader Effects |
|-------------|-------------|----------------|
| **Muscle Gain** | Fullness, roundness, definition | Increased specular highlight on peaks, subtle edge lighting |
| **Fat Loss** | Sharper jawline, visible abs, vascularity | Enhanced normal map detail, reduced SSS (subsurface scattering) |
| **Pump (Temporary)** | Swelling, vascularity, skin tightness | Emissive veins, increased specular, slight redness tint |
| **Weight Gain** | Overall scale increase, softer features | Uniform scale, increased SSS, softer shadows |
| **Weight Loss** | Shrinking, more angular features | Reduced scale, sharper contours |

### 5.2 Visual Feedback System

```python
class VisualFeedbackSystem:
    """
    Adds visual cues to help users understand body changes
    """
    
    def __init__(self, renderer):
        self.renderer = renderer
        self.highlight_regions = {
            'muscle_gain': ['biceps', 'chest', 'shoulders', 'lats'],
            'fat_loss': ['waist', 'face', 'thighs'],
            'pump': []  # Dynamic based on workout
        }
    
    def apply_muscle_gain_feedback(self, mesh, muscle_groups):
        """
        Highlight areas where muscle is growing
        """
        feedback = {}
        
        for muscle in muscle_groups:
            # Add subtle glow to muscle peaks
            feedback[muscle] = {
                'emissive': (0.1, 0.3, 0.5),  # Blue-white glow
                'emissive_intensity': 0.2,
                'specular_boost': 1.3,
                'pulse_speed': 0.5  # Slow pulse
            }
        
        return feedback
    
    def apply_fat_loss_feedback(self, mesh, body_regions):
        """
        Show definition improvements from fat loss
        """
        feedback = {}
        
        for region in body_regions:
            # Sharper shadows, more defined contours
            feedback[region] = {
                'normal_strength': 1.5,  # Enhanced normal map
                'rim_light': True,  # Edge lighting
                'rim_color': (0.8, 0.9, 1.0),
                'rim_intensity': 0.4
            }
        
        return feedback
    
    def generate_comparison_render(self, before_state, after_state, angle='front'):
        """
        Generate side-by-side comparison render
        """
        # Create split-screen effect
        before_img = self.renderer.render(before_state, angle, crop='left_half')
        after_img = self.renderer.render(after_state, angle, crop='right_half')
        
        # Add annotations
        changes = self._detect_changes(before_state, after_state)
        
        return {
            'image': self._combine_halves(before_img, after_img),
            'annotations': changes,
            'stats_comparison': self._format_stats(before_state, after_state)
        }
```

### 5.3 Heatmap Visualization

```python
class BodyChangeHeatmap:
    """
    Generates heatmap showing where body is changing
    """
    
    def generate_heatmap(self, state_history, timeframe_days=30):
        """
        Create color-coded heatmap of body changes
        
        Red = Growing (muscle)
        Blue = Shrinking (fat loss)
        Yellow = Both (recomposition)
        """
        # Calculate change rate per vertex
        changes = np.zeros((6890, 3))  # SMPL has 6890 vertices
        
        for i in range(len(state_history) - 1):
            state_a = state_history[i]
            state_b = state_history[i + 1]
            
            # Vertex displacement over time
            delta = state_b.vertices - state_a.vertices
            changes += delta
        
        # Normalize by timeframe
        changes /= timeframe_days
        
        # Classify changes
        growth_mask = np.linalg.norm(changes, axis=1) > 0.001
        
        # Color mapping
        colors = np.zeros((6890, 3))
        colors[growth_mask] = [1.0, 0.3, 0.3]  # Red for growth
        
        return colors
```

---

## 6. Implementation Plan

### Phase 1: Foundation (Week 1-2)

**Goals:**
- Set up SMPL model loading
- Implement basic beta parameter mapping
- Create interpolation system

**Tasks:**
1. Download SMPL models (M/F/Neutral)
2. Implement SMPL forward pass in PyTorch/NumPy
3. Create `BodyToSMPLMapper` class
4. Build interpolation system with easing functions
5. Export meshes to GLTF for web viewer

**Deliverables:**
- `smpl_core.py` - SMPL model wrapper
- `body_mapper.py` - Parameter mapping
- `interpolator.py` - Smooth transitions
- Test: Morph between 5 preset body types

### Phase 2: Real-Time System (Week 3-4)

**Goals:**
- Integrate with workout logging
- Implement vertex displacement for muscle pump
- Build progressive update queue

**Tasks:**
1. Create `WorkoutMorphEngine`
2. Implement muscle region vertex displacement
3. Build `ProgressiveMorphQueue` for time-based updates
4. Connect to workout database
5. Add pump effect visualization

**Deliverables:**
- `workout_morph.py` - Workout-to-body pipeline
- `vertex_displacement.py` - Localized muscle effects
- `update_queue.py` - Progressive changes
- Test: Log workout, see pump effect fade over 2 hours

### Phase 3: Visual Feedback (Week 5-6)

**Goals:**
- Add shader-based visual cues
- Build comparison tools
- Implement heatmap visualization

**Tasks:**
1. Create Three.js shader for muscle highlighting
2. Build side-by-side comparison renderer
3. Implement change heatmap generation
4. Add stats overlay system
5. Create progress visualization modes

**Deliverables:**
- `visual_feedback.js` - Shader effects
- `comparison_renderer.py` - Before/after generation
- `heatmap.py` - Change visualization
- Test: Generate 30-day progress comparison

### Phase 4: Optimization (Week 7-8)

**Goals:**
- Optimize for 60fps on mobile
- Add pre-computed morph targets
- Implement LOD system

**Tasks:**
1. Build `MorphTargetCache` for fast preview
2. Implement LOD (Level of Detail) meshes
3. Add GPU instancing for multiple avatars
4. Optimize shader complexity
5. Add WebWorker for heavy calculations

**Deliverables:**
- `morph_cache.py` - Pre-computed states
- `lod_system.py` - Detail levels
- Performance: 60fps on mid-range mobile

---

## 7. Technical Specifications

### 7.1 Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Morph FPS | 60fps | Smooth animations |
| Initial Load | <3s | SMPL model + shaders |
| Memory | <500MB | Mobile-friendly |
| Mesh Resolution | 6890 vertices | Full SMPL resolution |
| Pre-computed States | 250 | 10W × 5M × 5F grid |

### 7.2 File Structure

```
physiqai/
├── avatar/
│   ├── morphing/
│   │   ├── __init__.py
│   │   ├── smpl_core.py          # SMPL model wrapper
│   │   ├── body_mapper.py        # Body → SMPL mapping
│   │   ├── interpolator.py       # Smooth transitions
│   │   ├── vertex_displacement.py # Muscle displacement
│   │   ├── workout_morph.py      # Workout integration
│   │   ├── update_queue.py       # Progressive updates
│   │   └── morph_cache.py        # Pre-computed states
│   │
│   ├── visual/
│   │   ├── shaders/
│   │   │   ├── muscle_glow.frag
│   │   │   ├── fat_loss.frag
│   │   │   └── vascularity.frag
│   │   ├── feedback_system.py
│   │   ├── heatmap.py
│   │   └── comparison_renderer.py
│   │
│   └── viewer-v3.html            # SMPL-based 3D viewer
│
├── models/
│   └── smpl/
│       ├── basicmodel_m.pkl
│       ├── basicmodel_f.pkl
│       └── basicmodel_neutral.pkl
│
└── tests/
    └── test_morphing.py
```

### 7.3 Dependencies

```txt
# Core
torch>=2.0.0
numpy>=1.24.0
pillow>=10.0.0

# 3D
pyrender>=0.1.45
trimesh>=3.20.0

# Web export
gltflib>=1.0.0
draco-py>=1.0.0  # Compression

# Optional (for training)
scikit-learn>=1.3.0  # PCA for custom betas
```

---

## 8. Research Recommendations

### 8.1 Custom Beta Training

Train custom shape parameters on PhysiqAI dataset for better body composition mapping:

```python
# Train PCA on our progress pic dataset
def train_custom_betas(body_scans, n_components=10):
    """
    Learn shape space from real progress pictures
    after SMPL fitting
    """
    from sklearn.decomposition import PCA
    
    # Stack all fitted meshes
    vertices = np.array([scan['vertices'] for scan in body_scans])
    
    # Center
    mean_shape = vertices.mean(axis=0)
    centered = vertices - mean_shape
    
    # PCA
    pca = PCA(n_components=n_components)
    pca.fit(centered.reshape(len(vertices), -1))
    
    return {
        'mean': mean_shape,
        'components': pca.components_,
        'variance': pca.explained_variance_ratio_
    }
```

### 8.2 Neural Morphing

Consider a learned neural network for end-to-end body parameter → mesh:

```python
class NeuralMorphNet(nn.Module):
    """
    Direct parameter to vertex mapping
    Trained on SMPL data for fast inference
    """
    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(10, 64),  # 10 body params
            nn.ReLU(),
            nn.Linear(64, 128),
            nn.ReLU(),
            nn.Linear(128, 6890 * 3)  # Full mesh
        )
    
    def forward(self, body_params):
        return self.encoder(body_params).view(-1, 6890, 3)
```

---

## 9. Summary

### Key Decisions

1. **Use SMPL betas** for overall body shape (weight, proportions)
2. **Use vertex displacement** for localized muscle details (pump, hypertrophy)
3. **Pre-compute morph targets** for real-time preview
4. **Progressive update queue** for realistic time-based changes
5. **Shader-based feedback** for visual differentiation

### Success Metrics

- [ ] Morph between any two body states in <2 seconds
- [ ] 60fps during slider interaction
- [ ] Real-time pump effect visible within 1 second of workout log
- [ ] Clear visual distinction between muscle gain and fat loss
- [ ] <3 second initial load on 4G mobile

---

*Document Version: 1.0*  
*Created: 2026-02-23*  
*Author: Morphing Engineer*  
*Status: Design Complete, Ready for Implementation*
