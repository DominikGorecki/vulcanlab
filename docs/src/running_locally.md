# Running VulcanLab Locally for Development

This guide covers how to run VulcanLab locally for development without using Docker containers for the application itself.

## Prerequisites

### Required Software

1. **Python 3.10 or higher**
   ```bash
   python --version  # Should be 3.10+
   ```

2. **Node.js** (for the frontend)
   ```bash
   node --version
   npm --version
   ```

3. **PostgreSQL 16** with pgvector extension
   - Option A: Run PostgreSQL in Docker (recommended for development)
   - Option B: Install PostgreSQL locally

4. **Docker** (if using Option A for PostgreSQL)

### API Keys

You need at least one LLM API key:
- **Google Gemini** (recommended): [Get API key](https://ai.google.dev/)
- **OR OpenAI**: [Get API key](https://platform.openai.com/api-keys)

---

## PostgreSQL Setup

Choose one of the following options:

### Option A: PostgreSQL in Docker (Recommended)

This uses the pre-configured Docker setup in the `/migrations/docker_db` folder.

**1. Navigate to the migrations folder:**
```bash
cd migrations/docker_db
```

**2. Build and run the PostgreSQL container:**
```bash
# Build the image
docker build -t vulcanlab-postgres .

# Run the container
docker run -d \
  --name vulcanlab-db \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=your_admin_password \
  -v vulcanlab_pgdata:/var/lib/postgresql/data \
  vulcanlab-postgres
```

**3. Verify the database is running:**
```bash
docker exec vulcanlab-db psql -U postgres -c "SELECT version();"
```

**4. Return to project root:**
```bash
cd ../..
```

---

### Option B: Local PostgreSQL Installation

If you prefer to install PostgreSQL locally:

**1. Install PostgreSQL 16:**
- **Windows:** [Download PostgreSQL](https://www.postgresql.org/download/windows/)
- **Mac:** `brew install postgresql@16`
- **Linux:** Follow [official instructions](https://www.postgresql.org/download/linux/)

**2. Install pgvector extension:**
```bash
# Mac
brew install pgvector

# Linux (Ubuntu/Debian)
sudo apt install postgresql-16-pgvector

# Or compile from source
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

**3. Start PostgreSQL:**
```bash
# Mac
brew services start postgresql@16

# Linux
sudo systemctl start postgresql
```

**4. Verify installation:**
```bash
psql -U postgres -c "SELECT version();"
```

---

## Backend Setup

### 1. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate
```

### 2. Install Python Dependencies

```bash
# Install the package in development mode
pip install -e .
```

This will take some time and requires ~2GB of space for the installation.

### 3. Configure Environment Variables

**Create a `.env` file in the project root:**

```bash
# Copy from template
cp .env.example .env
```

**Edit `.env` with your credentials:**

```bash
# PostgreSQL Passwords (REQUIRED)
POSTGRES_ADMIN_PASSWORD=your_secure_admin_password
POSTGRES_APP_PASSWORD=your_secure_app_password

# LLM API Keys (at least one required)
LLM_OPENAI_API_KEY=sk-your-openai-key
LLM_GOOGLE_API_KEY=your-google-api-key
```

### 4. Configure Application Settings

The `vulcanlab.config.json` file contains non-secret settings. The default configuration should work for local development:

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

**If you need to change settings:**
```bash
# View current configuration
python -m vulcanlab.config.app_config_cli show

# Change database port (if using non-standard port)
python -m vulcanlab.config.app_config_cli set --db-port 5433

# Change LLM provider
python -m vulcanlab.config.app_config_cli set --provider openai
```

### 5. Validate Configuration

```bash
python -m vulcanlab.data.validate_config_cli
```

This checks that your `.env` file exists and all required variables are set.

### 6. Initialize the Database

```bash
python -m vulcanlab.data.init_db -v
```

This creates the database schema and necessary extensions.

### 7. Create Output Directory

```bash
mkdir output
```

### 8. Start the Backend Server

```bash
uvicorn vulcanlab_api.main:app --reload
```

The backend API will be available at **http://localhost:8000**

---

## Frontend Setup

### 1. Navigate to Frontend Directory

```bash
cd vulcanlab_ui
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Start Development Server

```bash
npm run dev
```

The frontend will be available at **http://localhost:3000**

---

## Verifying Installation

### Check Backend

Visit **http://localhost:8000/docs** to see the FastAPI interactive documentation.

### Check Frontend

Visit **http://localhost:3000** to see the VulcanLab UI.

### Check Database Connection

```bash
# If using Docker PostgreSQL
docker exec vulcanlab-db psql -U postgres -d vulcanlab_test -c "\dt"

# If using local PostgreSQL
psql -U postgres -d vulcanlab_test -c "\dt"
```

You should see the VulcanLab database tables.

---

## Development Workflow

### Starting Everything

**Terminal 1 - PostgreSQL (if using Docker):**
```bash
docker start vulcanlab-db
```

**Terminal 2 - Backend:**
```bash
# From project root
venv\Scripts\activate  # Windows
# or: source venv/bin/activate  # Linux/Mac

uvicorn vulcanlab_api.main:app --reload
```

**Terminal 3 - Frontend:**
```bash
# From project root
cd vulcanlab_ui
npm run dev
```

### Stopping Everything

- **Backend:** Press `Ctrl+C` in the backend terminal
- **Frontend:** Press `Ctrl+C` in the frontend terminal
- **PostgreSQL (Docker):** `docker stop vulcanlab-db`

---

## Troubleshooting

### Port Already in Use

**Backend (port 8000):**
```bash
# Find what's using port 8000
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Use a different port
uvicorn vulcanlab_api.main:app --reload --port 8001
```

**Frontend (port 3000):**
```bash
# Next.js will automatically try port 3001 if 3000 is busy
# Or set PORT environment variable
PORT=3001 npm run dev
```

**PostgreSQL (port 5432):**
```bash
# Use a different port when starting Docker
docker run -d --name vulcanlab-db -p 5433:5432 ...

# Update vulcanlab.config.json
python -m vulcanlab.config.app_config_cli set --db-port 5433
```

### Database Connection Errors

```bash
# Check if PostgreSQL is running
docker ps | grep vulcanlab-db  # If using Docker
pg_isready  # If using local PostgreSQL

# Check connection settings
python -m vulcanlab.data.validate_config_cli

# Check database logs (Docker)
docker logs vulcanlab-db
```

### Python Module Not Found

```bash
# Ensure virtual environment is activated
# You should see (venv) in your terminal prompt

# Reinstall dependencies
pip install -e .
```

### Frontend Build Errors

```bash
# Clear Next.js cache
cd vulcanlab_ui
rm -rf .next
npm install
npm run dev
```