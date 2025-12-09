# Docker Hub Deployment Guide

**Audience:** VulcanLab maintainers preparing to publish releases to Docker Hub.

This guide covers how to publish VulcanLab images to Docker Hub as an open source project.

## Prerequisites

1. **Docker Hub Account**
   - Create account at [hub.docker.com](https://hub.docker.com)
   - Create organization or use personal account
   - Recommended: Create `vulcanlab` organization

2. **Repository Setup**
   - Create repository: `vulcanlab/vulcanlab`
   - Set visibility: **Public** (for open source)
   - Add description and README on Docker Hub

3. **Local Setup**
   - Docker Desktop installed
   - Git repository cloned
   - All tests passing (T01-T04 complete)

## One-Time Setup

### 1. Login to Docker Hub

```bash
docker login
```

Enter your Docker Hub username and password.

Verify login:
```bash
docker info | grep Username
```

### 2. Configure Repository

Set the image name in your environment:

```bash
export DOCKER_REPO="vulcanlab/vulcanlab"
```

Add to your shell profile to persist:

```bash
echo 'export DOCKER_REPO="vulcanlab/vulcanlab"' >> ~/.bashrc  # or ~/.zshrc
```

## Release Process

### Step 1: Prepare Release

Before building, ensure:

1. All code changes are committed
2. All tests pass
3. Documentation is updated
4. Version number is decided (e.g., `v1.0.0`)

### Step 2: Build Image

```bash
# Set version
VERSION="v1.0.0"

# Build image with version tag
docker build -f docker/Dockerfile.allinone -t "$DOCKER_REPO:$VERSION" .

# Also tag as latest
docker tag "$DOCKER_REPO:$VERSION" "$DOCKER_REPO:latest"
```

**Build time:** 15-30 minutes

### Step 3: Test Image Locally

Before pushing, thoroughly test the image:

```bash
# Run health checks
docker run -d --name vulcanlab-test \
  --env-file .env.docker \
  "$DOCKER_REPO:$VERSION"

sleep 60

docker exec vulcanlab-test python /app/scripts/healthcheck.py

# Cleanup
docker stop vulcanlab-test
docker rm vulcanlab-test
```

All health checks must pass before pushing.

### Step 4: Push to Docker Hub

```bash
# Push version tag
docker push "$DOCKER_REPO:$VERSION"

# Push latest tag
docker push "$DOCKER_REPO:latest"
```

**Upload time:** 10-20 minutes (depending on connection speed)

### Step 5: Verify on Docker Hub

1. Go to https://hub.docker.com/r/vulcanlab/vulcanlab
2. Verify tags appear: `latest`, `v1.0.0`
3. Check image size (should be ~8-10GB)
4. Update repository description

### Step 6: Test Pull

Test that users can pull the image:

```bash
# From a different machine or fresh environment
docker pull vulcanlab/vulcanlab:latest
docker pull vulcanlab/vulcanlab:v1.0.0

# Verify
docker images | grep vulcanlab
```

### Step 7: Create GitHub Release

1. Go to GitHub repository
2. Click "Releases" → "Create a new release"
3. Tag: `v1.0.0`
4. Title: `VulcanLab v1.0.0`
5. Description:
   ```markdown
   ## Installation

   ```bash
   docker pull vulcanlab/vulcanlab:v1.0.0
   ```

   See [INSTALLATION.md](docs/INSTALLATION.md) for complete instructions.

   ## What's New

   - Initial release
   - All-in-one Docker container
   - PostgreSQL with pgvector + Apache AGE
   - FastAPI backend
   - Next.js frontend

   ## Docker Hub

   Image: [vulcanlab/vulcanlab:v1.0.0](https://hub.docker.com/r/vulcanlab/vulcanlab)
   ```

6. Optionally attach `vulcanlab-v1.0.0.tar.gz` for offline installation
7. Click "Publish release"

## Version Tagging Strategy

### Semantic Versioning

Use semantic versioning: `vMAJOR.MINOR.PATCH`

- **MAJOR:** Breaking changes (e.g., v2.0.0)
- **MINOR:** New features, backwards compatible (e.g., v1.1.0)
- **PATCH:** Bug fixes (e.g., v1.0.1)

### Docker Tags

For each release, create:

1. **Full version:** `v1.0.0`
2. **Minor version:** `v1.0` (points to latest patch)
3. **Major version:** `v1` (points to latest minor)
4. **Latest:** `latest` (points to most recent release)

Example:

```bash
VERSION="v1.2.3"

docker tag "$DOCKER_REPO:$VERSION" "$DOCKER_REPO:v1.2"
docker tag "$DOCKER_REPO:$VERSION" "$DOCKER_REPO:v1"
docker tag "$DOCKER_REPO:$VERSION" "$DOCKER_REPO:latest"

docker push "$DOCKER_REPO:$VERSION"
docker push "$DOCKER_REPO:v1.2"
docker push "$DOCKER_REPO:v1"
docker push "$DOCKER_REPO:latest"
```

## Multi-Architecture Builds (Optional)

To support both AMD64 and ARM64 (e.g., Apple Silicon):

### Setup Buildx

```bash
# Create builder
docker buildx create --name multiarch --use

# Verify
docker buildx inspect --bootstrap
```

### Build and Push Multi-Arch

```bash
VERSION="v1.0.0"

docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f docker/Dockerfile.allinone \
  -t "$DOCKER_REPO:$VERSION" \
  -t "$DOCKER_REPO:latest" \
  --push \
  .
```

**Note:** Multi-arch builds take significantly longer (30-60 minutes).

## Automated Builds with GitHub Actions

### Create Workflow File

**File:** `.github/workflows/docker-publish.yml`

```yaml
name: Publish Docker Image

on:
  release:
    types: [published]

jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Extract version
        id: version
        run: echo "VERSION=${GITHUB_REF#refs/tags/}" >> $GITHUB_OUTPUT

      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          file: ./docker/Dockerfile.allinone
          platforms: linux/amd64,linux/arm64
          push: true
          tags: |
            vulcanlab/vulcanlab:${{ steps.version.outputs.VERSION }}
            vulcanlab/vulcanlab:latest
```

### Setup Secrets

1. Go to GitHub repository settings
2. Secrets and variables → Actions
3. Add secrets:
   - `DOCKERHUB_USERNAME`: Your Docker Hub username
   - `DOCKERHUB_TOKEN`: Docker Hub access token ([create one](https://hub.docker.com/settings/security))

### Usage

Create a GitHub release → Workflow automatically builds and pushes to Docker Hub.

## Maintenance

### Updating an Existing Tag

**Warning:** Avoid updating existing version tags (breaks reproducibility).

If absolutely necessary:

```bash
# Rebuild
docker build -f docker/Dockerfile.allinone -t "$DOCKER_REPO:v1.0.0" .

# Force push (dangerous!)
docker push "$DOCKER_REPO:v1.0.0"
```

Better approach: Release a new patch version (v1.0.1).

### Deleting a Tag

```bash
# Delete locally
docker rmi "$DOCKER_REPO:v1.0.0"

# Delete from Docker Hub (via web UI only)
# Go to hub.docker.com → Repository → Tags → Delete
```

### Image Size Optimization

If image size is too large:

1. Review .dockerignore (exclude unnecessary files)
2. Multi-stage builds (already implemented)
3. Remove build dependencies after compilation
4. Use smaller base images (currently using pgvector/pgvector:pg16)

Current size: ~8-10GB (acceptable for all-in-one container)

## Monitoring

### Download Statistics

View on Docker Hub:
- https://hub.docker.com/r/vulcanlab/vulcanlab/tags

### Automated Scanning

Docker Hub automatically scans images for vulnerabilities.

View results:
- Repository → Tags → Security scan

## Support

### Updating Docker Hub README

The repository README on Docker Hub should include:

```markdown
# VulcanLab - All-in-One RAG System

VulcanLab is a complete Retrieval-Augmented Generation system in a single Docker container.

## Quick Start

```bash
docker pull vulcanlab/vulcanlab:latest

docker run -d \
  --name vulcanlab \
  -p 3000:3000 \
  -e POSTGRES_PASSWORD=your_password \
  -e LLM_GOOGLE_API_KEY=your_key \
  vulcanlab/vulcanlab:latest
```

Open http://localhost:3000

## Documentation

- [Installation Guide](https://github.com/yourusername/vulcanlab/blob/main/docs/INSTALLATION.md)
- [GitHub Repository](https://github.com/yourusername/vulcanlab)

## What's Included

- PostgreSQL 16 + pgvector + Apache AGE
- FastAPI backend
- Next.js frontend
- Automatic service management

## License

[Your License] - See [LICENSE](https://github.com/yourusername/vulcanlab/blob/main/LICENSE)
```

Then sync to Docker Hub:
1. Copy content
2. Go to hub.docker.com → Repository → Description
3. Paste and save

---

**That's it!** VulcanLab is now published and available worldwide via:

```bash
docker pull vulcanlab/vulcanlab:latest
```
