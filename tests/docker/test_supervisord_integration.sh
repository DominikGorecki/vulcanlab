#!/bin/bash
set -e

echo "Testing Supervisord Integration..."

# Test 1: Build image with supervisord
echo "Test 1: Building image with supervisord support"
docker build -f Dockerfile.allinone -t vulcanlab:supervisord-test . || exit 1

# Test 2: Container starts without crashing
echo "Test 2: Starting container (will fail without env vars - expected)"
docker run --rm --name vulcanlab-test-startup \
    -e POSTGRES_PASSWORD=test123 \
    -e LLM_GOOGLE_API_KEY=test_key \
    vulcanlab:supervisord-test &
CONTAINER_PID=$!

# Wait for initialization
sleep 5

# Check if container is still running
if ps -p $CONTAINER_PID > /dev/null; then
    echo "✓ Container started successfully"
    kill $CONTAINER_PID 2>/dev/null || true
    wait $CONTAINER_PID 2>/dev/null || true
else
    echo "✗ Container crashed during startup"
    exit 1
fi

# Test 3: Verify supervisord.conf is in the image
echo "Test 3: Checking supervisord.conf presence"
docker run --rm vulcanlab:supervisord-test cat /etc/supervisor/conf.d/supervisord.conf | grep "program:postgresql" || exit 1

# Test 4: Verify docker-entrypoint.sh is executable
echo "Test 4: Checking entrypoint script"
docker run --rm vulcanlab:supervisord-test test -x /usr/local/bin/docker-entrypoint.sh || exit 1

# Test 5: Verify log directories can be created
echo "Test 5: Checking log directory creation"
docker run --rm vulcanlab:supervisord-test ls -la /var/log/supervisor || exit 1

# Test 6: Verify data directories exist
echo "Test 6: Checking data directories"
docker run --rm vulcanlab:supervisord-test ls -la /app/data/input /app/data/output || exit 1

# Test 7: Verify PostgreSQL binaries are accessible
echo "Test 7: Checking PostgreSQL installation"
docker run --rm vulcanlab:supervisord-test /usr/lib/postgresql/16/bin/postgres --version | grep "16" || exit 1

# Test 8: Verify supervisord is accessible
echo "Test 8: Checking supervisord installation"
docker run --rm vulcanlab:supervisord-test /usr/bin/supervisord --version || exit 1

echo ""
echo "All supervisord integration tests passed!"
echo ""
echo "Note: Full startup test (with all 3 services) requires:"
echo "  docker run -d -p 3000:3000 \\"
echo "    -e POSTGRES_PASSWORD=yourpassword \\"
echo "    -e LLM_GOOGLE_API_KEY=your_api_key \\"
echo "    -v vulcanlab_data:/var/lib/postgresql/data \\"
echo "    vulcanlab:supervisord-test"
