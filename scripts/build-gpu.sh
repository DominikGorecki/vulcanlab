#!/bin/bash
# Build VulcanLab with GPU support

set -e

echo "============================================"
echo "VulcanLab GPU Build Script"
echo "============================================"
echo ""

# Check if nvidia-smi is available on host
if ! command -v nvidia-smi &> /dev/null; then
    echo "WARNING: nvidia-smi not found on host system."
    echo "GPU support requires NVIDIA drivers installed."
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if NVIDIA Container Toolkit is installed
if ! docker run --rm --gpus all nvidia/cuda:12.6.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
    echo "ERROR: NVIDIA Container Toolkit not detected."
    echo ""
    echo "Please install it first:"
    echo "  See docs/GPU_SETUP.md for installation instructions"
    echo ""
    exit 1
fi

echo "✓ NVIDIA drivers detected"
echo "✓ NVIDIA Container Toolkit detected"
echo ""

# Show GPU info
echo "Available GPUs:"
nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader
echo ""

# Build the image
echo "Building GPU-enabled Docker image..."
docker build -f docker/Dockerfile.allinone.gpu -t vulcanlab:gpu .

echo ""
echo "============================================"
echo "Build complete!"
echo "============================================"
echo ""
echo "To run with GPU support:"
echo "  docker run -d --name vulcanlab --gpus all -p 3000:3000 -v \$(pwd)/data:/app/data --env-file .env.docker vulcanlab:gpu"
echo ""
echo "To verify GPU is working:"
echo "  docker exec vulcanlab /opt/venv/bin/python -c 'import torch; print(f\"CUDA available: {torch.cuda.is_available()}\")'"
echo ""
