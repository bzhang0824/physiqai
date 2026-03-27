#!/bin/bash
# Setup script for PhysiqAI SMPL-based 3D Avatar

echo "==================================="
echo "PhysiqAI Avatar Setup"
echo "==================================="

# Create directories
mkdir -p projects/physiqai/models/smpl
mkdir -p projects/physiqai/models/smplify-x
mkdir -p projects/physiqai/avatar/threejs
mkdir -p projects/physiqai/data/smpl_fits

echo "✅ Directories created"

# Check Python version
python3 --version

# Install dependencies
echo "Installing dependencies..."
pip3 install --user torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu 2>/dev/null || echo "PyTorch install skipped (may need GPU version)"
pip3 install --user numpy scipy chumpy opencv-python 2>/dev/null || echo "Some packages may need manual install"

echo "==================================="
echo "Setup complete!"
echo "Next steps:"
echo "1. Download SMPL model from https://smpl.is.tue.mpg.de/"
echo "2. Clone SMPLify-X repository"
echo "3. Start fitting 3D meshes to Reddit photos"
echo "==================================="