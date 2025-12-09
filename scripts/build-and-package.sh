#!/bin/bash
set -e

# VulcanLab Distribution Packaging Script
# This script builds the Docker image and creates a distributable .tar.gz file

VERSION=${1:-latest}
IMAGE_NAME="vulcanlab/vulcanlab"
OUTPUT_DIR="dist"

echo "=========================================="
echo "VulcanLab Distribution Builder"
echo "=========================================="
echo "Version: $VERSION"
echo "Image: $IMAGE_NAME:$VERSION"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Build the Docker image
echo "Building Docker image..."
docker build -f docker/Dockerfile.allinone -t "$IMAGE_NAME:$VERSION" .

# Also tag as latest if building a version
if [ "$VERSION" != "latest" ]; then
    docker tag "$IMAGE_NAME:$VERSION" "$IMAGE_NAME:latest"
fi

# Get image size
IMAGE_SIZE=$(docker images "$IMAGE_NAME:$VERSION" --format "{{.Size}}")
echo ""
echo "Image built successfully!"
echo "Size: $IMAGE_SIZE"
echo ""

# Save image to tar.gz
OUTPUT_FILE="$OUTPUT_DIR/vulcanlab-${VERSION}.tar.gz"
echo "Saving image to: $OUTPUT_FILE"
docker save "$IMAGE_NAME:$VERSION" | gzip > "$OUTPUT_FILE"

# Get file size
FILE_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
echo ""
echo "=========================================="
echo "Distribution package created!"
echo "=========================================="
echo "File: $OUTPUT_FILE"
echo "Size: $FILE_SIZE"
echo ""
echo "To distribute:"
echo "  - Upload to GitHub releases"
echo "  - Or push to Docker Hub (see docs/DOCKER_HUB_DEPLOYMENT.md)"
echo ""
echo "Users can load with:"
echo "  docker load -i $OUTPUT_FILE"
echo "=========================================="
