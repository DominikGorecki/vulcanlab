#!/bin/bash
set -e

echo "Testing Dockerfile.allinone build..."

# Test 1: Build completes without errors
echo "Test 1: Full build completes"
docker build -f Dockerfile.allinone -t vulcanlab:build-test . || exit 1

# Test 2: Python is accessible
echo "Test 2: Python virtual environment"
docker run --rm vulcanlab:build-test /opt/venv/bin/python --version | grep "3.11" || exit 1

# Test 3: Node.js is accessible
echo "Test 3: Node.js installation"
docker run --rm vulcanlab:build-test node --version | grep "v20" || exit 1

# Test 4: spaCy model is installed
echo "Test 4: spaCy model"
docker run --rm vulcanlab:build-test /opt/venv/bin/python -c "import spacy; spacy.load('en_core_web_sm')" || exit 1

# Test 5: Next.js standalone build exists
echo "Test 5: Next.js standalone output"
docker run --rm vulcanlab:build-test ls /app/vulcanlab_ui/server.js || exit 1

# Test 6: Configuration files exist
echo "Test 6: Configuration files"
docker run --rm vulcanlab:build-test cat /app/vulcanlab.config.json | grep "vulcanlab_test" || exit 1

# Test 7: Required directories exist
echo "Test 7: Directory structure"
docker run --rm vulcanlab:build-test ls -la /app/data/input /app/data/output || exit 1

echo "All build tests passed!"
