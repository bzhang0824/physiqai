#!/usr/bin/env python3
"""
Minimal Chumpy Compatibility Module
====================================

Provides just enough chumpy functionality to load SMPL pickle files.
"""

import numpy as np
import sys
from functools import partial

class Ch(np.ndarray):
    """Minimal chumpy Ch array class - inherits from ndarray"""

    def __new__(cls, input_array=None):
        if input_array is None:
            input_array = []
        obj = np.asarray(input_array).view(cls)
        return obj

    def __array_finalize__(self, obj):
        pass

    # Support pickle protocol
    def __reduce__(self):
        return (Ch, (self.tolist(),))


# Create module-like object
class ChumpyModule:
    pass

chumpy_mod = ChumpyModule()
chumpy_mod.Ch = Ch
chumpy_mod.__dict__['Ch'] = Ch

# Install as modules
sys.modules['chumpy'] = chumpy_mod
sys.modules['chumpy.ch'] = chumpy_mod

# Export
__all__ = ['Ch']
