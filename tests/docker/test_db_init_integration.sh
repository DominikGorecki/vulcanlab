#!/bin/bash
set -e

echo "Testing Database Initialization..."

# Clean up any existing test containers/volumes
docker rm -f vulcanlab-t03-test 2>/dev/null || true
docker volume rm vulcanlab-t03-data 2>/dev/null || true

# Build the image
echo "Building image..."
docker build -f Dockerfile.allinone -t vulcanlab:t03-test .

# Create a test .env file
cat > .env.docker.test << EOF
POSTGRES_PASSWORD=test_pg_password_12345
POSTGRES_APP_PASSWORD=test_app_password_12345
POSTGRES_DB=vulcanlab_test
POSTGRES_APP_USER=vulcanlab_app_user_test
LLM_GOOGLE_API_KEY=test_key
EOF

# Start container with a fresh volume
echo "Starting container with fresh database..."
docker run -d \
  --name vulcanlab-t03-test \
  -v vulcanlab-t03-data:/var/lib/postgresql/data \
  --env-file .env.docker.test \
  vulcanlab:t03-test

# Wait for initialization to complete
echo "Waiting for database initialization (60 seconds)..."
sleep 60

# Test 1: PostgreSQL is running
echo "Test 1: PostgreSQL service status"
docker exec vulcanlab-t03-test supervisorctl status postgresql | grep RUNNING || {
    echo "FAIL: PostgreSQL not running"
    docker logs vulcanlab-t03-test
    exit 1
}

# Test 2: Database exists
echo "Test 2: Database 'vulcanlab_test' exists"
docker exec vulcanlab-t03-test psql -U postgres -lqt | cut -d \| -f 1 | grep -qw vulcanlab_test || {
    echo "FAIL: Database vulcanlab_test not found"
    exit 1
}

# Test 3: Extensions are installed
echo "Test 3: Extensions (vector, age) are installed"
docker exec vulcanlab-t03-test psql -U postgres -d vulcanlab_test -c "SELECT extname FROM pg_extension WHERE extname IN ('vector', 'age');" | tee /tmp/extensions.txt

grep -q "vector" /tmp/extensions.txt || {
    echo "FAIL: vector extension not installed"
    exit 1
}

grep -q "age" /tmp/extensions.txt || {
    echo "FAIL: age extension not installed"
    exit 1
}

# Test 4: Application user exists
echo "Test 4: Application user exists"
docker exec vulcanlab-t03-test psql -U postgres -c "\\du" | grep vulcanlab_app_user_test || {
    echo "FAIL: Application user not found"
    exit 1
}

# Test 5: Application user can connect
echo "Test 5: Application user can connect to database"
docker exec -e PGPASSWORD=test_app_password_12345 vulcanlab-t03-test \
    psql -U vulcanlab_app_user_test -d vulcanlab_test -c "SELECT 1;" || {
    echo "FAIL: Application user cannot connect"
    exit 1
}

# Test 6: Search path includes ag_catalog
echo "Test 6: Search path includes ag_catalog"
docker exec vulcanlab-t03-test psql -U postgres -d vulcanlab_test -c "SHOW search_path;" | grep ag_catalog || {
    echo "FAIL: ag_catalog not in search path"
    exit 1
}

# Test 7: Backend can connect (if it's running)
echo "Test 7: Backend service status"
docker exec vulcanlab-t03-test supervisorctl status backend | grep RUNNING && {
    echo "Backend is running (good sign - DB connection likely working)"
} || {
    echo "Backend not running (check logs - may have other issues)"
    docker exec vulcanlab-t03-test tail -n 50 /var/log/supervisor/backend_error.log
}

# Test 8: Test vector extension functionality
echo "Test 8: Test vector extension"
docker exec vulcanlab-t03-test psql -U postgres -d vulcanlab_test -c "
CREATE TABLE test_vectors (id serial PRIMARY KEY, embedding vector(3));
INSERT INTO test_vectors (embedding) VALUES ('[1,2,3]'), ('[4,5,6]');
SELECT * FROM test_vectors;
DROP TABLE test_vectors;
" || {
    echo "FAIL: Vector extension not working"
    exit 1
}

# Test 9: Test AGE extension functionality
echo "Test 9: Test AGE extension"
docker exec vulcanlab-t03-test psql -U postgres -d vulcanlab_test -c "
SELECT create_graph('test_graph');
SELECT drop_graph('test_graph', true);
" || {
    echo "FAIL: AGE extension not working"
    exit 1
}

# Cleanup
echo "Cleaning up..."
docker stop vulcanlab-t03-test
docker rm vulcanlab-t03-test
docker volume rm vulcanlab-t03-data
rm .env.docker.test

echo "All database initialization tests passed!"
