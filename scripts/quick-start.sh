#!/bin/bash
set -e

echo "=========================================="
echo "VulcanLab Quick Start"
echo "=========================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker is not running."
    echo "Please start Docker Desktop and try again."
    exit 1
fi

# Check if .env.docker exists
if [ ! -f ".env.docker" ]; then
    echo "Creating .env.docker from template..."
    cp docker/.env.docker.example .env.docker

    echo ""
    echo "IMPORTANT: Edit .env.docker with your API keys before continuing."
    echo ""
    echo "  nano .env.docker     # Linux/Mac"
    echo "  notepad .env.docker  # Windows"
    echo ""
    echo "Press Enter when ready..."
    read
fi

# Create data directories
echo "Creating data directories..."
mkdir -p data/input data/output

# Check if vulcanlab container exists
if docker ps -a --format '{{.Names}}' | grep -q '^vulcanlab$'; then
    echo "Container 'vulcanlab' already exists."
    echo "Starting existing container..."
    docker start vulcanlab
else
    echo "Starting VulcanLab for the first time..."
    echo "This may take 60 seconds for database initialization..."

    docker run -d \
      --name vulcanlab \
      -p 3000:3000 \
      -v vulcanlab_data:/var/lib/postgresql/data \
      -v "$(pwd)/data/input:/app/data/input" \
      -v "$(pwd)/data/output:/app/data/output" \
      --env-file .env.docker \
      vulcanlab/vulcanlab:latest

    echo "Waiting for services to start..."
    sleep 60
fi

# Run health check
echo ""
echo "Running health check..."
docker exec vulcanlab python /app/scripts/healthcheck.py

echo ""
echo "=========================================="
echo "VulcanLab is ready!"
echo "=========================================="
echo ""
echo "Access the web interface at:"
echo "  http://localhost:3000"
echo ""
echo "To view logs:"
echo "  docker logs -f vulcanlab"
echo ""
echo "To stop:"
echo "  docker stop vulcanlab"
echo "=========================================="
