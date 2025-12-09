# VulcanLab Troubleshooting Guide

Common issues and solutions.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Service Issues](#service-issues)
- [Database Issues](#database-issues)
- [Performance Issues](#performance-issues)
- [Network Issues](#network-issues)

## Installation Issues

### Docker Not Found

**Symptom:** `docker: command not found`

**Solution:**
1. Install Docker Desktop
2. Ensure Docker is running (check system tray/menu bar)
3. Restart terminal after installation

### Image Load Fails

**Symptom:** `Error loading image: invalid tar header`

**Solution:**
- Re-download the image file (may be corrupted)
- Verify file integrity: `md5sum vulcanlab-latest.tar.gz`
- Ensure sufficient disk space (30GB+)

### Permission Denied

**Symptom:** `permission denied while trying to connect to the Docker daemon`

**Linux Solution:**
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Logout and login again
```

## Service Issues

### PostgreSQL Won't Start

**Check logs:**
```bash
docker exec vulcanlab tail -n 100 /var/log/supervisor/postgresql_error.log
```

**Common causes:**

1. **Data directory corrupted**
   ```bash
   # Remove volume and reinitialize
   docker stop vulcanlab
   docker rm vulcanlab
   docker volume rm vulcanlab_data
   # Re-run docker run command
   ```

2. **Port 5432 conflict** (internal only, shouldn't conflict)
   ```bash
   docker exec vulcanlab lsof -i :5432
   ```

### Backend Won't Start

**Check logs:**
```bash
docker exec vulcanlab tail -n 100 /var/log/supervisor/backend_error.log
```

**Common causes:**

1. **Missing API keys**
   ```bash
   # Verify environment variables
   docker exec vulcanlab env | grep LLM
   ```

2. **Database connection failed**
   ```bash
   # Test DB connectivity
   docker exec vulcanlab psql -U postgres -d vulcanlab_test -c "SELECT 1;"
   ```

3. **Python errors**
   ```bash
   # Check Python version and imports
   docker exec vulcanlab /opt/venv/bin/python --version
   docker exec vulcanlab /opt/venv/bin/python -c "import vulcanlab_api"
   ```

### Frontend Won't Start

**Check logs:**
```bash
docker exec vulcanlab tail -n 100 /var/log/supervisor/frontend_error.log
```

**Common causes:**

1. **Port 3000 in use on host**
   ```bash
   # Use different port
   docker stop vulcanlab
   docker rm vulcanlab
   # Re-run with -p 3001:3000
   ```

2. **Build artifacts missing**
   ```bash
   docker exec vulcanlab ls -la /app/vulcanlab_ui/.next/
   # Should show standalone/ and static/ directories
   ```

## Database Issues

### Cannot Connect to Database

**Test connection:**
```bash
docker exec vulcanlab psql -U postgres -l
```

**If fails:**
```bash
# Check PostgreSQL is running
docker exec vulcanlab supervisorctl status postgresql

# Check PostgreSQL logs
docker exec vulcanlab tail -n 50 /var/log/supervisor/postgresql_error.log
```

### Extensions Not Installed

**Verify extensions:**
```bash
docker exec vulcanlab psql -U postgres -d vulcanlab_test -c "SELECT * FROM pg_extension;"
```

**Should show:** vector, age, plpgsql

**If missing:**
```bash
# Reinitialize database
docker exec vulcanlab psql -U postgres -d vulcanlab_test -c "
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS age;
LOAD 'age';
"
```

## Performance Issues

### Slow Response Times

1. **Check resource usage:**
   ```bash
   docker stats vulcanlab
   ```

2. **Increase Docker memory:**
   - Docker Desktop → Settings → Resources → Memory → 16GB+

3. **Check disk I/O:**
   ```bash
   docker exec vulcanlab df -h
   ```

### High Memory Usage

**Normal:** VulcanLab uses 8-12GB of RAM

**If excessive (>16GB):**
```bash
# Restart container
docker restart vulcanlab
```

## Network Issues

### Cannot Access on Port 3000

1. **Check port is exposed:**
   ```bash
   docker port vulcanlab
   ```

2. **Check firewall:**
   ```bash
   # Linux
   sudo ufw status
   sudo ufw allow 3000

   # Mac
   # System Preferences → Security → Firewall → Allow

   # Windows
   # Windows Defender Firewall → Allow app through firewall
   ```

3. **Check container is running:**
   ```bash
   docker ps | grep vulcanlab
   ```

### Backend API Not Accessible

**Test from inside container:**
```bash
docker exec vulcanlab curl -v http://localhost:8000/health
```

**Test from host (if port exposed):**
```bash
curl -v http://localhost:8000/health
```

## Getting More Help

### Collect Diagnostic Information

Run this script to collect debug info:

```bash
#!/bin/bash
echo "=== VulcanLab Diagnostics ===" > vulcanlab-debug.txt
echo "" >> vulcanlab-debug.txt

echo "Container status:" >> vulcanlab-debug.txt
docker ps -a | grep vulcanlab >> vulcanlab-debug.txt
echo "" >> vulcanlab-debug.txt

echo "Service status:" >> vulcanlab-debug.txt
docker exec vulcanlab supervisorctl status >> vulcanlab-debug.txt
echo "" >> vulcanlab-debug.txt

echo "Health check:" >> vulcanlab-debug.txt
docker exec vulcanlab python /app/scripts/healthcheck.py >> vulcanlab-debug.txt
echo "" >> vulcanlab-debug.txt

echo "Backend logs:" >> vulcanlab-debug.txt
docker exec vulcanlab tail -n 100 /var/log/supervisor/backend_error.log >> vulcanlab-debug.txt
echo "" >> vulcanlab-debug.txt

echo "Frontend logs:" >> vulcanlab-debug.txt
docker exec vulcanlab tail -n 100 /var/log/supervisor/frontend_error.log >> vulcanlab-debug.txt
echo "" >> vulcanlab-debug.txt

echo "PostgreSQL logs:" >> vulcanlab-debug.txt
docker exec vulcanlab tail -n 100 /var/log/supervisor/postgresql_error.log >> vulcanlab-debug.txt

cat vulcanlab-debug.txt
```

### Report an Issue

When reporting issues on GitHub:

1. Include output from diagnostic script above
2. Specify your OS and Docker version
3. Describe steps to reproduce
4. Include relevant error messages

[Create an issue](https://github.com/yourusername/vulcanlab/issues/new)
