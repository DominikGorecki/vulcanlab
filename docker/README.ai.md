# docker (AI README)

## Purpose
- All-in-one containerized deployment of VulcanLab running PostgreSQL, FastAPI backend, and Next.js frontend in a single container
- Managed by supervisord for process coordination and automatic restarts
- Supports both CPU and GPU-enabled variants for ML workloads

## Quick start
```bash
# Build the image
docker build -f docker/Dockerfile.allinone -t vulcanlab:latest .

# Create .env.docker from example
cp docker/.env.docker.example docker/.env.docker
# Edit .env.docker with your credentials

# Run the container
docker run -d --name vulcanlab \
  -p 3000:3000 \
  -v vulcanlab_data:/var/lib/postgresql/data \
  --env-file docker/.env.docker \
  vulcanlab:latest

# Access frontend at http://localhost:3000

# Development: sync code changes without rebuilding
./docker/sync-dev-changes.sh both vulcanlab
```

For GPU support, use Dockerfile.allinone.gpu and add --gpus all flag.

## Architecture overview
- Single container runs three services via supervisord: PostgreSQL (priority 1), FastAPI backend (priority 10), Next.js frontend (priority 20)
- Multi-stage Docker build: base stage installs system deps and AGE extension, python-deps creates venv, frontend-build produces standalone Next.js output, final stage combines all artifacts
- PostgreSQL 16 with pgvector and Apache AGE extensions for vector similarity search and graph queries
- Only frontend port 3000 exposed to host; backend (8000) and database (5432) are internal to container
- Data persistence via volumes: database at /var/lib/postgresql/data, input/output at /app/data/
- Environment-driven configuration via .env.docker file for credentials and API keys
- Development workflow accelerated by sync-dev-changes.sh script for hot-reloading code changes
- GPU variant adds CUDA 12.6 libraries and environment variables for PyTorch acceleration

## Entry points and main flows
- Entry points:
  - [docker-entrypoint.sh](docker/docker-entrypoint.sh) - Container initialization, runs at startup
  - [supervisord.conf](docker/supervisord.conf) - Process manager configuration
  - [Dockerfile.allinone](docker/Dockerfile.allinone) - CPU build definition
  - [Dockerfile.allinone.gpu](docker/Dockerfile.allinone.gpu) - GPU build definition

- Typical flows:
  - Container startup: docker-entrypoint.sh checks if PostgreSQL data directory exists, if not runs initdb and initialization scripts from /docker-entrypoint-initdb.d/, updates pg_hba.conf for production, then starts supervisord
  - Database initialization: init-db.sh sets postgres superuser password, enable-extensions.sql creates vector and age extensions
  - Service startup: supervisord starts PostgreSQL first (priority 1), waits for it to be ready, then starts backend (priority 10), then frontend (priority 20)
  - Development cycle: developer edits code locally, runs sync-dev-changes.sh which copies changed files to container and restarts appropriate service via supervisorctl
  - Request flow: User -> Frontend (port 3000) -> Backend (port 8000) -> PostgreSQL (port 5432)

## Key conventions
- Multi-stage builds for smaller final image: build deps removed in final stage
- Next.js standalone mode reduces node_modules size by 70-90 percent
- Supervisord log rotation: 50MB per log file, 10 backups kept
- Database runs as postgres user, backend and frontend run as root (within container)
- Environment variables must exist even if empty (supervisord requirement), entrypoint exports empty defaults
- .dockerignore excludes tests, docs, data directories, secrets, and build artifacts
- All paths in configuration use /app as base: /app/vulcanlab.config.json, /app/data/input, /app/data/output
- Services restart automatically on failure via supervisord autorestart=true
- Port exposure follows least-privilege: only frontend exposed, backend and database internal only

## Dependencies overview
- Runtime dependencies: pgvector/pgvector:pg16 base image, Python 3.11 with packages from pyproject.toml installed in /opt/venv, Node.js 20.x LTS, PostgreSQL 16, Apache AGE v1.5.0-rc0, supervisord
- Dev dependencies and tooling: Docker for containerization, sync-dev-changes.sh script for development hot-reload, spaCy en_core_web_sm model downloaded at build time
- External services: Google Gemini API or OpenAI API for LLM features (at least one required)
- GPU variant adds: CUDA 12.6 runtime and libraries (cuda-cudart-12-6, cuda-libraries-12-6, libcublas-12-6, libcudnn9-cuda-12)

## APIs and contracts
- Configuration file: vulcanlab.config.docker.json at project root defines database connection (host: localhost, port: 5432, db_name: vulcanlab_test), LLM models (gemini: gemini-2.0-flash-exp/gemini-2.5-pro-preview, openai: gpt-4o-mini/gpt-4o), paths (input_dir: /app/data/input, output_dir: /app/data/output)
- Environment variables: POSTGRES_ADMIN_PASSWORD (required), POSTGRES_APP_PASSWORD (required), LLM_GOOGLE_API_KEY or LLM_OPENAI_API_KEY (at least one required), POSTGRES_DB, POSTGRES_USER, POSTGRES_APP_USER, LLM_PROVIDER
- Backend API: FastAPI running at http://localhost:8000 (internal), accessed by frontend via NEXT_PUBLIC_API_URL
- Database connection: PostgreSQL at localhost:5432, authentication via md5 password, pgvector extension provides vector type, Apache AGE provides ag_catalog schema with graph functions
- Volume mounts: /var/lib/postgresql/data for database persistence (required), /app/data/input and /app/data/output for data files (optional), /var/log/supervisor for service logs (optional)

## File tree (depth 1)
```
docker/
  .dockerignore               # Build context exclusions (Python, Node, data dirs, secrets)
  .env.docker.example         # Environment variable template with placeholders
  Dockerfile.allinone         # CPU multi-stage build: base + python-deps + frontend-build + final
  Dockerfile.allinone.gpu     # GPU variant adds CUDA 12.6 libraries and env vars
  README.ai.md                # This file
  docker-entrypoint.sh        # Container initialization: initdb, run init scripts, start supervisord
  enable-extensions.sql       # Creates pgvector and age extensions, sets search_path
  init-db.sh                  # Sets postgres password (database/user creation commented out)
  supervisord.conf            # Process manager: postgresql (priority 1), backend (priority 10), frontend (priority 20)
  sync-dev-changes.sh         # Development hot-reload: rsync code, restart services via supervisorctl
```

## LLM handoff
- When asking an LLM to work in this folder, include:
  - [docker-entrypoint.sh](docker/docker-entrypoint.sh) - Understand container initialization flow
  - [supervisord.conf](docker/supervisord.conf) - Service startup order and configuration
  - [Dockerfile.allinone](docker/Dockerfile.allinone) - Build process and dependencies
  - [vulcanlab.config.docker.json](../vulcanlab.config.docker.json) - Runtime configuration structure
  - [sync-dev-changes.sh](docker/sync-dev-changes.sh) - Development workflow acceleration
  - [.dockerignore](docker/.dockerignore) - What gets excluded from build context
  - [init-db.sh](docker/init-db.sh) and [enable-extensions.sql](docker/enable-extensions.sql) - Database setup logic

- Good first questions to ask:
  - How do I add a new environment variable to the container?
  - What happens when a service crashes inside the container?
  - How can I debug why the backend is not starting?
  - What is the difference between the CPU and GPU Dockerfiles?
  - How do I modify the database initialization to create additional users or schemas?
  - What files are needed to change the Next.js build configuration?

- Guardrails:
  - Never commit .env.docker with real credentials to version control
  - Always test multi-stage build changes with docker build before pushing
  - Verify sync-dev-changes.sh works after modifying supervisord service names
  - Run docker exec vulcanlab supervisorctl status after changes to verify all services running
  - Ensure POSTGRES_ADMIN_PASSWORD and at least one LLM API key set before running container
  - Do not expose backend port 8000 or database port 5432 to host unless explicitly needed

## Gotchas
- init-db.sh has most database setup code commented out (database creation, app user creation, privilege grants) - likely handled elsewhere in application lifecycle
- supervisord requires all environment variables referenced in config to exist even if empty - docker-entrypoint.sh exports empty defaults at line 135-138
- Next.js standalone mode requires .next/static and public folders copied separately from .next/standalone - see Dockerfile.allinone lines 115-117
- sync-dev-changes.sh frontend sync rebuilds Next.js locally then copies to container, increasing sync time compared to backend sync which just copies Python files
- GPU Dockerfile does not remove build-essential and git in cleanup stage (line 72 vs CPU line 50) - intentional for potential runtime compilation needs
