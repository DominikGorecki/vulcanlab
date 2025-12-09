# VulcanLab Docker Installation Guide

Get VulcanLab running on your machine with Docker.

> **Note:** All Docker-related files are located in the `/docker` folder. When building images, make sure to reference them from that location (e.g., `docker/Dockerfile.allinone`).

## Prerequisites

### Required Software

1. **Docker Desktop**
   - **Windows:** [Download Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
   - **Mac:** [Download Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
   - **Linux:** [Install Docker Engine](https://docs.docker.com/engine/install/)

   After installing, verify Docker is running:
   ```bash
   docker --version
   ```

2. **System Requirements**
   - **RAM:** 16GB minimum (32GB recommended)
   - **Disk Space:** 30GB free
   - **CPU:** Modern multi-core processor

3. **API Keys**

   You need at least one LLM API key:

   - **Google Gemini** (recommended): [Get API key](https://ai.google.dev/)
   - **OR OpenAI:** [Get API key](https://platform.openai.com/api-keys) <- Not supported yet

   Note: Right now you need a Gemini key. It's the only options for embeddings at this point. 

---

## Getting the Image

Choose one of the following methods to obtain the VulcanLab Docker image:

### Method A: Load Pre-built Image (Coming Soon)

**Best for:** End users who want the simplest installation.

Download `vulcanlab-latest.tar.gz` from the [latest release](https://github.com/DominikGorecki/vulcanlab/releases).

**Linux/Mac:**
```bash
docker load -i vulcanlab-latest.tar.gz
```

**Windows (PowerShell):**
```powershell
docker load -i vulcanlab-latest.tar.gz
```

This takes 5-10 minutes depending on your disk speed.

---

### Method B: Pull from Docker Hub (Coming Soon)

**Best for:** Quick installation once published.

```bash
docker pull vulcanlab/vulcanlab:latest
```

---

### Method C: Build from Source

**Best for:** Developers or users who want to customize VulcanLab.

#### Clone Repository

```bash
git clone https://github.com/DominikGorecki/vulcanlab.git
cd vulcanlab
```

#### Build Image

```bash
docker build -f docker/Dockerfile.allinone -t vulcanlab/vulcanlab:latest .
```

This takes 15-30 minutes (downloading and compiling dependencies).

---

## Configuration Setup

Before running the container, you need to create a configuration file with your API keys and database passwords.

### Create .env.docker File

**Linux/Mac:**
```bash
# Copy from template
cp docker/.env.docker.example .env.docker

# Or create directly
cat > .env.docker << 'EOF'
POSTGRES_PASSWORD=change_this_password
POSTGRES_APP_PASSWORD=change_this_password_too
LLM_GOOGLE_API_KEY=your_gemini_api_key_here
# Optional: LLM_OPENAI_API_KEY=your_openai_api_key_here
EOF
```

**Windows (PowerShell):**
```powershell
# Copy from template
Copy-Item docker\.env.docker.example .env.docker

# Or create directly
@"
POSTGRES_PASSWORD=change_this_password
POSTGRES_APP_PASSWORD=change_this_password_too
LLM_GOOGLE_API_KEY=your_gemini_api_key_here
"@ | Out-File -FilePath .env.docker -Encoding ASCII
```

**⚠️ Important:** Replace the placeholder values with:
- Strong passwords for database security
- Your actual Google Gemini or OpenAI API key

### Create Data Directories

**Linux/Mac:**
```bash
mkdir -p data/input data/output
```

**Windows (PowerShell):**
```powershell
New-Item -ItemType Directory -Force -Path data\input, data\output
```

---

## Running the Container

Now that you have the image and configuration ready, you can start the VulcanLab container.

### Understanding the docker run Command

Here's what each option does:

- **`-d`** - Detached mode. Runs the container in the background and prints the container ID. Without this, the container runs in the foreground and you'll see all logs in your terminal.

- **`--name vulcanlab`** - Assigns a name to the container so you can easily reference it (e.g., `docker stop vulcanlab` instead of using the container ID).

- **`-p 3000:3000`** - Port mapping for the frontend. Maps port 3000 on your host machine to port 3000 inside the container. Format is `HOST_PORT:CONTAINER_PORT`.

- **`-p 8000:8000`** - Port mapping for the backend API. Maps port 8000 on your host to port 8000 in the container.

- **`-v vulcanlab_data:/var/lib/postgresql/data`** - Creates a named Docker volume called `vulcanlab_data` and mounts it to the PostgreSQL data directory. This persists your database data even if the container is removed.

- **`-v $(pwd)/data/input:/app/data/input`** - Mounts your local `data/input` directory to `/app/data/input` inside the container. This allows you to add files from your host system.

- **`-v $(pwd)/data/output:/app/data/output`** - Mounts your local `data/output` directory to `/app/data/output` inside the container. Processed files will appear here.

- **`--env-file .env.docker`** - Loads environment variables from the `.env.docker` file (API keys, passwords, etc.).

- **`vulcanlab/vulcanlab:latest`** - The image name and tag to run.

### Run Command

**Linux/Mac:**
```bash
docker run -d \
  --name vulcanlab \
  -p 3000:3000 \
  -p 8000:8000 \
  -v vulcanlab_data:/var/lib/postgresql/data \
  -v $(pwd)/data/input:/app/data/input \
  -v $(pwd)/data/output:/app/data/output \
  --env-file .env.docker \
  vulcanlab/vulcanlab:latest
```

**Windows (PowerShell):**
```powershell
docker run -d `
  --name vulcanlab `
  -p 3000:3000 `
  -p 8000:8000 `
  -v vulcanlab_data:/var/lib/postgresql/data `
  -v ${PWD}\data\input:/app/data/input `
  -v ${PWD}\data\output:/app/data/output `
  --env-file .env.docker `
  vulcanlab/vulcanlab:latest
```

**Windows (Command Prompt):**
```cmd
docker run -d ^
  --name vulcanlab ^
  -p 3000:3000 ^
  -p 8000:8000 ^
  -v vulcanlab_data:/var/lib/postgresql/data ^
  -v %cd%\data\input:/app/data/input ^
  -v %cd%\data\output:/app/data/output ^
  --env-file .env.docker ^
  vulcanlab/vulcanlab:latest
```

### Using Custom Ports

If ports 3000 or 8000 are already in use on your system, you can map to different ports:

```bash
# Example: Use port 3001 for frontend and 8001 for backend
docker run -d \
  --name vulcanlab \
  -p 3001:3000 \
  -p 8001:8000 \
  ... \
  vulcanlab/vulcanlab:latest

# Then access at http://localhost:3001 (frontend) and http://localhost:8001 (API)
```

---

## Verifying Installation

### Wait for Initialization

First-time startup takes about 60 seconds to initialize the database.

Watch the logs:
```bash
docker logs -f vulcanlab
```

Press `Ctrl+C` when you see "Starting services with supervisord..."

### Run Health Check

```bash
docker exec vulcanlab python /app/scripts/healthcheck.py
```

You should see: **"All 6 health checks passed!"**

### Access VulcanLab

Open your web browser and go to:

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000

🎉 **VulcanLab is now running!**

---

## Managing the Container

### Starting VulcanLab

If you stopped the container, start it again:

```bash
docker start vulcanlab
```

### Stopping VulcanLab

```bash
docker stop vulcanlab
```

### Viewing Logs

```bash
# All logs
docker logs vulcanlab

# Follow logs in real-time
docker logs -f vulcanlab

# Specific service logs
docker exec vulcanlab tail -f /var/log/supervisor/backend.log
docker exec vulcanlab tail -f /var/log/supervisor/frontend.log
```

### Checking System Health

```bash
docker exec vulcanlab python /app/scripts/healthcheck.py
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check if container exists
docker ps -a | grep vulcanlab

# Check logs for errors
docker logs vulcanlab

# Remove and recreate
docker rm vulcanlab
# Then re-run the docker run command
```

### Port Already in Use

If you get "port is already allocated":

```bash
# Find what's using the port
lsof -i :3000  # Linux/Mac
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :3000  # Windows
netstat -ano | findstr :8000  # Windows

# Either stop that service, or use a different port:
docker run ... -p 3001:3000 -p 8001:8000 ... vulcanlab/vulcanlab:latest
# Then access at http://localhost:3001 (frontend) and http://localhost:8001 (API)
```

### Services Not Running

```bash
# Check service status
docker exec vulcanlab supervisorctl status

# Restart a specific service
docker exec vulcanlab supervisorctl restart backend
docker exec vulcanlab supervisorctl restart frontend
docker exec vulcanlab supervisorctl restart postgresql
```

### Database Connection Errors

```bash
# Test database connectivity
docker exec vulcanlab psql -U postgres -d vulcanlab_test -c "SELECT version();"

# Check PostgreSQL logs
docker exec vulcanlab tail -n 100 /var/log/supervisor/postgresql_error.log
```

### Health Check Fails

```bash
# Run health check with full output
docker exec vulcanlab python /app/scripts/healthcheck.py

# Check individual service logs
docker exec vulcanlab supervisorctl status
```

### Out of Memory

If Docker runs out of memory:

1. Open Docker Desktop settings
2. Go to Resources → Memory
3. Increase to at least 16GB
4. Click "Apply & Restart"

---

## Updating VulcanLab

### To a New Version

```bash
# Stop current version
docker stop vulcanlab
docker rm vulcanlab

# Load new version (Method A)
docker load -i vulcanlab-v2.0.tar.gz

# Or pull new version (Method B)
docker pull vulcanlab/vulcanlab:v2.0

# Start with same data volume (preserves your database)
docker run -d \
  --name vulcanlab \
  -p 3000:3000 \
  -p 8000:8000 \
  -v vulcanlab_data:/var/lib/postgresql/data \
  -v $(pwd)/data/input:/app/data/input \
  -v $(pwd)/data/output:/app/data/output \
  --env-file .env.docker \
  vulcanlab/vulcanlab:v2.0
```

**Note:** Your data persists in the `vulcanlab_data` volume and `data/` directories.

---

## Uninstalling VulcanLab

### Remove Container Only (Keep Data)

```bash
docker stop vulcanlab
docker rm vulcanlab
```

### Remove Everything (Including Data)

```bash
# Stop and remove container
docker stop vulcanlab
docker rm vulcanlab

# Remove Docker volume (database)
docker volume rm vulcanlab_data

# Remove Docker image
docker rmi vulcanlab/vulcanlab:latest

# Remove data directories (optional)
rm -rf data/
```

---

## Advanced Topics

### Backing Up Your Data

```bash
# Backup database volume
docker run --rm \
  -v vulcanlab_data:/source \
  -v $(pwd):/backup \
  alpine tar czf /backup/vulcanlab-backup.tar.gz -C /source .

# Backup input/output directories
tar czf data-backup.tar.gz data/
```

### Restoring from Backup

```bash
# Restore database volume
docker run --rm \
  -v vulcanlab_data:/target \
  -v $(pwd):/backup \
  alpine tar xzf /backup/vulcanlab-backup.tar.gz -C /target

# Restore data directories
tar xzf data-backup.tar.gz
```

---

## Getting Help

- **GitHub Issues:** [Report bugs or request features](https://github.com/DominikGorecki/vulcanlab/issues)
- **Discussions:** [Ask questions](https://github.com/DominikGorecki/vulcanlab/discussions)
- **Documentation:** [Full documentation](https://github.com/DominikGorecki/vulcanlab/tree/main/docs)
