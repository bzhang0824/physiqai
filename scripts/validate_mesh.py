#!/usr/bin/env python3
"""
PhysiqAI Mesh Validator
Validates Three.js BufferGeometry format compatibility
"""

import json
import sys
from pathlib import Path


class MeshValidator:
    """Validates mesh files for Three.js compatibility"""

    def __init__(self, filepath):
        self.filepath = Path(filepath)
        self.errors = []
        self.warnings = []
        self.data = None
        self.stats = {}

    def validate(self):
        """Run all validation checks"""
        print(f"\n{'='*60}")
        print(f"Validating: {self.filepath}")
        print(f"{'='*60}\n")

        # Step 1: Check file exists
        if not self._check_file_exists():
            return self._report()

        # Step 2: Parse JSON
        if not self._parse_json():
            return self._report()

        # Step 3: Validate structure
        self._validate_structure()

        # Step 4: Validate attributes
        self._validate_attributes()

        # Step 5: Validate indices
        self._validate_indices()

        # Step 6: Compute stats
        self._compute_stats()

        # Step 7: Three.js specific checks
        self._check_threejs_compatibility()

        return self._report()

    def _check_file_exists(self):
        """Check if file exists"""
        if not self.filepath.exists():
            self.errors.append(f"File not found: {self.filepath}")
            return False
        return True

    def _parse_json(self):
        """Parse JSON file"""
        try:
            with open(self.filepath, 'r') as f:
                self.data = json.load(f)
            return True
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Error reading file: {e}")
            return False

    def _validate_structure(self):
        """Validate top-level structure"""
        # Required top-level keys
        if 'type' not in self.data:
            self.errors.append("Missing required field: 'type'")
        elif self.data['type'] != 'BufferGeometry':
            self.errors.append(f"Type must be 'BufferGeometry', got: {self.data['type']}")

        if 'data' not in self.data:
            self.errors.append("Missing required field: 'data'")
            return

        data = self.data['data']
        if 'attributes' not in data:
            self.errors.append("Missing required field: 'data.attributes'")
            return

        # Optional metadata
        if 'metadata' in self.data:
            meta = self.data['metadata']
            if meta.get('type') != 'BufferGeometry':
                self.warnings.append("Metadata type should be 'BufferGeometry'")
            if meta.get('version') != 4.5:
                self.warnings.append(f"Metadata version is {meta.get('version')}, expected 4.5")
        else:
            self.warnings.append("Missing metadata (optional but recommended)")

    def _validate_attributes(self):
        """Validate geometry attributes"""
        attrs = self.data['data']['attributes']

        # Position is required
        if 'position' not in attrs:
            self.errors.append("Missing required attribute: 'position'")
            return

        pos = attrs['position']

        # Check position structure
        if 'itemSize' not in pos:
            self.errors.append("Position missing 'itemSize'")
        elif pos['itemSize'] != 3:
            self.errors.append(f"Position itemSize must be 3, got: {pos['itemSize']}")

        if 'type' not in pos:
            self.errors.append("Position missing 'type'")
        elif pos['type'] not in ['Float32Array', 'Float64Array']:
            self.warnings.append(f"Position type '{pos['type']}' may not be fully supported")

        if 'array' not in pos:
            self.errors.append("Position missing 'array'")
        else:
            arr = pos['array']
            if len(arr) % 3 != 0:
                self.errors.append(f"Position array length ({len(arr)}) not divisible by 3")
            self.stats['vertex_count'] = len(arr) // 3

        # Check normal (optional but recommended)
        if 'normal' in attrs:
            normal = attrs['normal']
            if normal.get('itemSize') != 3:
                self.warnings.append("Normal attribute should have itemSize=3")
            if len(normal.get('array', [])) != len(pos.get('array', [])):
                self.warnings.append("Normal array length doesn't match position")
        else:
            self.warnings.append("Missing normal attribute (optional but recommended)")

        # Check UV (optional)
        if 'uv' in attrs:
            uv = attrs['uv']
            if uv.get('itemSize') != 2:
                self.warnings.append("UV attribute should have itemSize=2")

    def _validate_indices(self):
        """Validate index data"""
        data = self.data['data']

        if 'index' not in data:
            self.warnings.append("No indices found - geometry will use non-indexed drawing")
            return

        idx = data['index']

        if 'type' not in idx:
            self.warnings.append("Index missing 'type'")
        elif idx['type'] not in ['Uint16Array', 'Uint32Array']:
            self.warnings.append(f"Index type '{idx['type']}' - Uint16Array or Uint32Array recommended")

        if 'array' not in idx:
            self.errors.append("Index missing 'array'")
        else:
            arr = idx['array']
            self.stats['index_count'] = len(arr)
            if len(arr) % 3 != 0:
                self.warnings.append(f"Index count ({len(arr)}) not divisible by 3 - may not be valid triangles")

    def _compute_stats(self):
        """Compute geometry statistics"""
        attrs = self.data['data']['attributes']
        pos = attrs['position']['array']

        # Compute bounds
        xs = pos[0::3]
        ys = pos[1::3]
        zs = pos[2::3]

        self.stats['bounds'] = {
            'x': {'min': min(xs), 'max': max(xs)},
            'y': {'min': min(ys), 'max': max(ys)},
            'z': {'min': min(zs), 'max': max(zs)}
        }

        # Center
        self.stats['center'] = {
            'x': (min(xs) + max(xs)) / 2,
            'y': (min(ys) + max(ys)) / 2,
            'z': (min(zs) + max(zs)) / 2
        }

        # Size
        self.stats['size'] = {
            'x': max(xs) - min(xs),
            'y': max(ys) - min(ys),
            'z': max(zs) - min(zs)
        }

    def _check_threejs_compatibility(self):
        """Check Three.js specific compatibility"""
        # Three.js r128+ supports this format
        # Main concern: boundingSphere and boundingBox are optional
        # Three.js will compute them if missing

        data = self.data['data']
        if 'boundingSphere' not in data:
            self.warnings.append("Missing boundingSphere (Three.js will compute automatically)")
        if 'boundingBox' not in data:
            self.warnings.append("Missing boundingBox (Three.js will compute automatically)")

        # Groups are optional
        if 'groups' not in data:
            self.warnings.append("No draw groups defined (will render entire geometry)")

    def _report(self):
        """Generate validation report"""
        print("VALIDATION RESULTS")
        print("-" * 60)

        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for err in self.errors:
                print(f"   • {err}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warn in self.warnings:
                print(f"   • {warn}")

        if not self.errors and not self.warnings:
            print("\n✅ Perfect! No issues found.")
        elif not self.errors:
            print("\n✅ Valid for Three.js (with warnings)")
        else:
            print("\n❌ INVALID - Fix errors before using with Three.js")

        if self.stats:
            print(f"\n📊 STATISTICS:")
            print(f"   Vertices: {self.stats.get('vertex_count', 'N/A'):,}")
            print(f"   Indices: {self.stats.get('index_count', 'N/A'):,}")
            if 'bounds' in self.stats:
                b = self.stats['bounds']
                print(f"   Bounds X: [{b['x']['min']:.3f}, {b['x']['max']:.3f}]")
                print(f"   Bounds Y: [{b['y']['min']:.3f}, {b['y']['max']:.3f}]")
                print(f"   Bounds Z: [{b['z']['min']:.3f}, {b['z']['max']:.3f}]")
            if 'center' in self.stats:
                c = self.stats['center']
                print(f"   Center: ({c['x']:.3f}, {c['y']:.3f}, {c['z']:.3f})")

        print(f"\n{'='*60}")

        return len(self.errors) == 0


def main():
    if len(sys.argv) < 2:
        print("Usage: validate_mesh.py <mesh_file.json>")
        print("\nExample:")
        print("  python3 validate_mesh.py storage/meshes/admin_bz_001_front_mesh.json")
        sys.exit(1)

    filepath = sys.argv[1]
    validator = MeshValidator(filepath)
    is_valid = validator.validate()

    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
