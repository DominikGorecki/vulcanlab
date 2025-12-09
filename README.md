# VulcanLab

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)

**A Retrieval-Augmented Generation system.**
</div>

## Setup

### 1. Environment and Packages Install

Activate setup and activate the environment (recommended):

```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# or: source venv/bin/activate  # Unix/Mac
```

Install the packages--this will take some time and requires ~2GB of space just for the install -- probably close to 15GB more when running and different models are downloaded on the fly. 

```
# Install package in development mode
venv\Scripts\pip install -e .
```

### 2. Configuration

| Note: Currently supporting both Gemini and OpenAI APIs.

#### Configuration Files

VulcanLab uses two configuration files:

1. **`vulcanlab.config.json`** - Non-secret settings (database, LLM models, paths)
2. **`.env`** - Secrets only (API keys, passwords)

#### A. Application Configuration (vulcanlab.config.json)

The `vulcanlab.config.json` file in the project root contains all non-secret configuration settings. A default file is provided with the repository.

**View current configuration:**
```bash
python -m vulcanlab.config.app_config_cli show
```

**Modify configuration:**
```bash
# Change LLM provider
python -m vulcanlab.config.app_config_cli set --provider openai

# Change model names
python -m vulcanlab.config.app_config_cli set --gemini-light gemini-2.0-flash-exp

# Change database settings
python -m vulcanlab.config.app_config_cli set --db-host localhost --db-port 5433
```

**Default configuration:**
```json
{
  "database": {
    "admin_user": "postgres",
    "host": "127.0.0.1",
    "port": 5432,
    "db_name": "vulcanlab_test",
    "app_user": "vulcanlab_app_user_test"
  },
  "llm": {
    "provider": "gemini",
    "models": {
      "openai": {
        "light": "gpt-4o-mini",
        "full": "gpt-4o"
      },
      "gemini": {
        "light": "gemini-flash-latest",
        "full": "gemini-2.5-pro"
      }
    }
  }
}
```

You can edit this file directly or use the CLI commands above.

#### B. Secrets Configuration (.env)

**⚠️ REQUIRED:** Create a `.env` file in the root folder for secrets (API keys and passwords).

The application will **fail to start** if required environment variables are missing. This is a security feature to prevent accidentally using default passwords.

**Quick Start:**
```bash
# Copy the template
cp .env.example .env

# Edit .env and replace placeholder values with your actual credentials
```

**Example `.env` file:**
```bash
# PostgreSQL Passwords (REQUIRED)
POSTGRES_ADMIN_PASSWORD=your_secure_admin_password
POSTGRES_APP_PASSWORD=your_secure_app_password

# LLM API Keys (at least one required)
LLM_OPENAI_API_KEY=sk-your-openai-key
LLM_GOOGLE_API_KEY=your-google-api-key
```

**Important Security Notes:**
- ✅ Only passwords and API keys go in `.env`. All other settings are in `vulcanlab.config.json`
- ✅ The `.env` file is gitignored - never commit it to version control
- ✅ Use strong, unique passwords for both database users
- ✅ Change default passwords in production environments
- ❌ No fallback passwords - missing variables will cause clear error messages

**Validate Your Configuration:**
Before running the application, you can validate your configuration:
```bash
python -m vulcanlab.data.validate_config_cli
```

This will check:
- `.env` file exists
- All required environment variables are set
- Database connectivity (optional)

**Troubleshooting:**
If you see an error like "Environment variable 'POSTGRES_APP_PASSWORD' is not set":
1. Ensure `.env` file exists in the project root
2. Check that the variable is defined in `.env` without quotes: `POSTGRES_APP_PASSWORD=your_password`
3. See `.env.example` for a complete template
4. Run the validation tool: `python -m vulcanlab.data.validate_config_cli` 

### 3. Initiate the Database and Filesystem

Use the `init_db` module to initiate the DB:

```bash
python -m vulcanlab.data.init_db -v
```

Add an `output` folder to the root of the repo.

```bash
mkdir output
``` 

## Useful Commands When Hangs

```powershell
Stop-Process -Name "python" -Force  # Replace with the actual name
```

## Starting

1. Ensure docker is running with DB

1. Enable virtual python environment

Windows Cmd:

```bash
venv\Scripts\activate
```

1. Start the backend server

```bash
uvicorn vulcanlab_api.main:app --reload
```



# Docker Notes

## CPU-Only Deployment

```
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

## GPU-Accelerated Deployment

For faster ML operations (reranking, document processing), use GPU support:

```bash
# Build GPU-enabled image
bash scripts/build-gpu.sh

# Or manually:
docker build -f docker/Dockerfile.allinone.gpu -t vulcanlab:gpu .

# Run with GPU support
docker run -d \
  --name vulcanlab \
  --gpus all \
  -p 3000:3000 \
  -v vulcanlab_data:/var/lib/postgresql/data \
  -v $(pwd)/data/input:/app/data/input \
  -v $(pwd)/data/output:/app/data/output \
  --env-file .env.docker \
  vulcanlab:gpu

# Verify GPU is detected
docker exec vulcanlab /opt/venv/bin/python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

See [docs/GPU_SETUP.md](docs/GPU_SETUP.md) for detailed GPU setup instructions.

```

```
# Create .env file
cat > .env.docker << EOF
POSTGRES_PASSWORD=secure_password
POSTGRES_APP_PASSWORD=app_password
POSTGRES_DB=vulcanlab_test
POSTGRES_APP_USER=vulcanlab_app_user_test
LLM_GOOGLE_API_KEY=your_key_here
EOF

# Build and start
docker build -f docker/Dockerfile.allinone -t vulcanlab:latest .
docker run -d --name vulcanlab -v vulcanlab_data:/var/lib/postgresql/data \
  --env-file .env.docker -p 3000:3000 vulcanlab:latest

# Watch initialization (wait ~60 seconds)
docker logs -f vulcanlab

# Verify database
docker exec vulcanlab psql -U postgres -d vulcanlab_test -c "SELECT extname FROM pg_extension WHERE extname IN ('vector', 'age');"
```

---------------------------------------------------------------

What You Need to Do:
Update your .env.docker file to match the new template:
# Change this line:
POSTGRES_PASSWORD=your_password
# To this:
POSTGRES_ADMIN_PASSWORD=your_password
Rebuild the Docker image with the updated configuration:
docker build -f docker/Dockerfile.allinone -t vulcanlab/vulcanlab:latest .
Stop and remove the existing container:
docker stop vulcanlab
docker rm vulcanlab
Run the new container:
docker run -d \
  --name vulcanlab \
  -p 3000:3000 \
  -p 8000:8000 \
  -v vulcanlab_data:/var/lib/postgresql/data \
  -v $(pwd)/data/input:/app/data/input \
  -v $(pwd)/data/output:/app/data/output \
  --env-file .env.docker \
  vulcanlab/vulcanlab:latest
Verify the backend starts successfully:
# Wait about 60 seconds for initialization, then check:
docker exec vulcanlab supervisorctl status

# All three services should show RUNNING
# Run the health check:
docker exec vulcanlab python /app/scripts/healthcheck.py