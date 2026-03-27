#!/usr/bin/env python3
"""
SMPL Model Converter - Pure pickle approach, no scipy/chumpy
"""

import pickle
import numpy as np
import warnings
import sys
from types import ModuleType
warnings.filterwarnings('ignore')

# Create a proper class to replace chumpy.Ch
class ChumpyCh(np.ndarray):
    """Class that mimics chumpy.Ch - proper ndarray subclass"""
    def __new__(cls, input_array=None, *args, **kwargs):
        if input_array is None:
            input_array = []
        obj = np.asarray(input_array).view(cls)
        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return

class BlockChumpy:
    """Fake chumpy module"""
    Ch = ChumpyCh

sys.modules['chumpy'] = BlockChumpy()
sys.modules['chumpy.ch'] = BlockChumpy()

def load_smpl_pickle(model_path):
    """Load SMPL model using raw pickle inspection"""

    # Read the pickle file
    with open(model_path, 'rb') as f:
        try:
            data = pickle.load(f, encoding='latin1', fix_imports=True)
            return data
        except Exception as e:
            print(f"Pickle load error: {e}")
            return None

def convert_smpl_model(pkl_path, npz_path):
    """Convert SMPL pickle to NPZ format"""
    print(f"Loading {pkl_path}...")

    data = load_smpl_pickle(pkl_path)
    if data is None:
        print("  ❌ Failed to load")
        return None

    print(f"Loaded {len(data)} keys")

    # Convert to numpy arrays
    converted = {}
    for key, val in data.items():
        try:
            if isinstance(val, np.ndarray):
                converted[key] = np.array(val)  # Ensure it's a regular ndarray
                print(f"  {key}: ndarray {val.shape}")
            elif hasattr(val, 'toarray'):
                arr = val.toarray()
                converted[key] = arr
                print(f"  {key}: sparse -> {arr.shape}")
            elif isinstance(val, (str, dict, float, int)):
                print(f"  {key}: {type(val).__name__} (skipped)")
            else:
                print(f"  {key}: {type(val).__name__} (skipped)")
        except Exception as e:
            print(f"  {key}: error - {e}")

    # Save to NPZ
    np.savez_compressed(npz_path, **converted)
    print(f"✅ Saved to {npz_path}")
    return converted

if __name__ == "__main__":
    # Convert both models
    models = [
        ('/home/clawd/.openclaw/workspace/projects/physiqai/models/smpl/basicModel_f_lbs_10_207_0_v1.0.0.pkl',
         '/home/clawd/.openclaw/workspace/projects/physiqai/models/smpl/smpl_female.npz'),
        ('/home/clawd/.openclaw/workspace/projects/physiqai/models/smpl/basicmodel_m_lbs_10_207_0_v1.0.0.pkl',
         '/home/clawd/.openclaw/workspace/projects/physiqai/models/smpl/smpl_male.npz')
    ]

    for pkl_path, npz_path in models:
        print(f"\n{'='*60}")
        print(f"Converting {pkl_path}")
        print('='*60)
        try:
            convert_smpl_model(pkl_path, npz_path)
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
