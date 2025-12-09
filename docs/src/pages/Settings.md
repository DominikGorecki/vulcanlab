# Settings Page Documentation

## Overview

The Settings page manages system configuration including database settings, LLM models, file paths, templates, and RAG configuration presets. Users can view and update configuration through organized tabs.

### Pages

- **Main Page**: `/settings` - Configuration management with multiple tabs
- **Edit Template**: `/settings/templates/[function_tag]` - Edit specific prompt template

### User Workflow

1. View current configuration across tabs (Database, LLM, Paths, Templates, RAG Config)
2. Check database health and connection status
3. Initialize database (create tables and schema)
4. Update database settings (host, port, database name, users)
5. Update LLM settings (provider, model names)
6. Update file paths (input directory, output directory)
7. Edit prompt templates (query expansion, augmentation, etc.)
8. Manage RAG configuration presets

## API Calls

### GET `/settings/`

**Called By**: Main page (`/settings`) on component mount

**Request**: No parameters

**Response**:
```json
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "db_name": "vulcanLab",
    "app_user": "vulcanLab_app",
    "admin_user": "postgres"
  },
  "llm": {
    "provider": "openai",
    "models": {
      "openai": {
        "light": "gpt-4o-mini",
        "full": "gpt-4o"
      },
      "gemini": {
        "light": "gemini-1.5-flash",
        "full": "gemini-1.5-pro"
      }
    }
  },
  "paths": {
    "input_dir": "/path/to/input",
    "output_dir": "/path/to/output"
  }
}
```

**Purpose**: Get full application configuration.

### GET `/settings/database`

**Called By**: Database tab on component mount

**Request**: No parameters

**Response**:
```json
{
  "host": "localhost",
  "port": 5432,
  "db_name": "vulcanLab",
  "app_user": "vulcanLab_app",
  "admin_user": "postgres"
}
```

**Purpose**: Get database configuration only.

### PUT `/settings/database`

**Called By**: Database tab when user saves changes

**Request**:
```json
{
  "host": "localhost",
  "port": 5432,
  "db_name": "vulcanLab",
  "app_user": "vulcanLab_app",
  "admin_user": "postgres"
}
```

**Response**: Same as GET, with updated values

**Purpose**: Update database configuration.

### GET `/settings/llm`

**Called By**: LLM tab on component mount

**Request**: No parameters

**Response**:
```json
{
  "provider": "openai",
  "models": {
    "openai": {
      "light": "gpt-4o-mini",
      "full": "gpt-4o"
    },
    "gemini": {
      "light": "gemini-1.5-flash",
      "full": "gemini-1.5-pro"
    }
  }
}
```

**Purpose**: Get LLM configuration only.

### PUT `/settings/llm`

**Called By**: LLM tab when user saves changes

**Request**:
```json
{
  "provider": "openai",
  "models": {
    "openai": {
      "light": "gpt-4o-mini",
      "full": "gpt-4o"
    },
    "gemini": {
      "light": "gemini-1.5-flash",
      "full": "gemini-1.5-pro"
    }
  }
}
```

**Response**: Same as GET, with updated values

**Purpose**: Update LLM configuration.

### GET `/settings/paths`

**Called By**: Paths tab on component mount

**Request**: No parameters

**Response**:
```json
{
  "input_dir": "/path/to/input",
  "output_dir": "/path/to/output"
}
```

**Purpose**: Get paths configuration only.

### PUT `/settings/paths`

**Called By**: Paths tab when user saves changes

**Request**:
```json
{
  "input_dir": "/path/to/input",
  "output_dir": "/path/to/output"
}
```

**Response**: Same as GET, with updated values

**Purpose**: Update paths configuration.

### GET `/init/db-health`

**Called By**: Database tab when user clicks "Check Health"

**Request**: No parameters

**Response**:
```json
{
  "connection_ok": true,
  "database_exists": true,
  "tables_exist": true,
  "message": "Database is healthy"
}
```

**Purpose**: Check database health and connection status.

### POST `/init/database`

**Called By**: Database tab when user clicks "Initialize Database"

**Request**:
```json
{
  "force": false
}
```

**Response**:
```json
{
  "success": true,
  "message": "Database initialized successfully",
  "tables_created": 8
}
```

**Purpose**: Initialize database (create tables and schema).

## API Implementation Details

### GET `/settings/`

**Router**: `src/vulcanlab_api/routers/settings.py` → `get_full_config()`

**Processing Steps**:

1. **Load Config**: Calls `load_config()` from `vulcanLab.config.app_config`
2. **Convert to Schema**: Converts `AppConfig` to `AppConfigSchema` for API response
3. **Return Response**: Returns full configuration object

**Modules Called**:
- `vulcanLab.config.app_config.load_config()`

**File System Operations**: Reads `vulcanLab.config.json` file

**Tables Accessed**: None (configuration stored in JSON file)

### PUT `/settings/database`

**Router**: `src/vulcanlab_api/routers/settings.py` → `update_database_config(request)`

**Processing Steps**:

1. **Load Current Config**: Calls `load_config()` to get current configuration
2. **Update Database Config**: Updates `config.database` with request values:
   - `host`, `port`, `db_name`, `app_user`, `admin_user`
3. **Save Config**: Calls `save_config(config)` to write to JSON file
4. **Reload Config**: Calls `load_config(force_reload=True)` to refresh cache
5. **Return Response**: Returns updated database configuration

**Modules Called**:
- `vulcanLab.config.app_config.load_config()`
- `vulcanLab.config.app_config.save_config()`

**File System Operations**: Reads and writes `vulcanLab.config.json` file

**Tables Accessed**: None

### PUT `/settings/llm`

**Router**: `src/vulcanlab_api/routers/settings.py` → `update_llm_config(request)`

**Processing Steps**:

1. **Load Current Config**: Calls `load_config()` to get current configuration
2. **Update LLM Config**: Updates `config.llm` with request values:
   - `provider`: "openai" or "gemini"
   - `models.openai.light`, `models.openai.full`
   - `models.gemini.light`, `models.gemini.full`
3. **Save Config**: Calls `save_config(config)` to write to JSON file
4. **Reload Config**: Calls `load_config(force_reload=True)` to refresh cache
5. **Return Response**: Returns updated LLM configuration

**Modules Called**:
- `vulcanLab.config.app_config.load_config()`
- `vulcanLab.config.app_config.save_config()`

**File System Operations**: Reads and writes `vulcanLab.config.json` file

**Tables Accessed**: None

### PUT `/settings/paths`

**Router**: `src/vulcanlab_api/routers/settings.py` → `update_paths_config(request)`

**Processing Steps**:

1. **Load Current Config**: Calls `load_config()` to get current configuration
2. **Validate Paths**: Validates paths are absolute (if provided)
3. **Update Paths Config**: Updates `config.paths` with request values:
   - `input_dir`: absolute path to input directory
   - `output_dir`: absolute path to output directory
4. **Save Config**: Calls `save_config(config)` to write to JSON file
5. **Reload Config**: Calls `load_config(force_reload=True)` to refresh cache
6. **Return Response**: Returns updated paths configuration

**Modules Called**:
- `vulcanLab.config.app_config.load_config()`
- `vulcanLab.config.app_config.save_config()`

**File System Operations**: Reads and writes `vulcanLab.config.json` file

**Tables Accessed**: None

### GET `/init/db-health`

**Router**: `src/vulcanlab_api/routers/init.py` → `check_db_health()`

**Processing Steps**:

1. **Call Module Function**: Calls `check_database_health()` from `vulcanLab.data.db_health_check`
2. **Module Processing**:
   - Attempts to connect to database using current configuration
   - Checks if database exists
   - Checks if tables exist (queries `information_schema.tables`)
   - Returns health status
3. **Return Response**: Returns health check results

**Modules Called**:
- `vulcanLab.data.db_health_check.check_database_health()`

**Database Queries**:
- Connection test (implicit)
- `SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema = 'public')` (check tables)

**Tables Accessed**: `information_schema.tables` (PostgreSQL system table)

### POST `/init/database`

**Router**: `src/vulcanlab_api/routers/init.py` → `init_database(request)`

**Processing Steps**:

1. **Call Module Function**: Calls `init_database()` from `vulcanLab.data.init_db`
2. **Module Processing**:
   - Creates database if it doesn't exist (using admin connection)
   - Creates application user if it doesn't exist
   - Grants permissions to application user
   - Creates all tables using SQLAlchemy `Base.metadata.create_all()`
   - Creates pgvector extension if not exists
   - Returns initialization results
3. **Return Response**: Returns success status and tables created count

**Modules Called**:
- `vulcanLab.data.init_db.init_database()`
- `vulcanLab.data.database.Base.metadata.create_all()`

**Database Queries**:
- `CREATE DATABASE IF NOT EXISTS ...` (if database doesn't exist)
- `CREATE USER IF NOT EXISTS ...` (if user doesn't exist)
- `GRANT ALL PRIVILEGES ON DATABASE ... TO ...` (grant permissions)
- `CREATE EXTENSION IF NOT EXISTS vector` (create pgvector extension)
- `CREATE TABLE ...` (create all tables)

**Tables Accessed**: Creates all application tables (`works`, `chunks`, `queries`, `results`, `io_files`, `rag_config`, `prompt_meta`)

## Modules Used

### `vulcanLab.config.app_config`

**Purpose**: Manage application configuration stored in JSON file

**Key Functions**:
- `load_config(force_reload=False)`: Load configuration from JSON file
  - Uses singleton pattern to cache configuration
  - Reads `vulcanLab.config.json` file
  - Returns `AppConfig` object
  - Returns default config if file doesn't exist
- `save_config(config)`: Save configuration to JSON file
  - Writes `AppConfig` to `vulcanLab.config.json`
  - Updates cache
- `get_config_path()`: Get path to config file
  - Returns `vulcanLab.config.json` path in project root
- `get_default_config()`: Get default configuration
  - Returns `AppConfig` with default values

**Configuration Structure**:
- `database`: Database settings (host, port, db_name, app_user, admin_user)
- `llm`: LLM settings (provider, models for OpenAI and Gemini)
- `paths`: File paths (input_dir, output_dir)

**File System Operations**: Reads and writes `vulcanLab.config.json` file

### `vulcanLab.data.db_health_check`

**Purpose**: Check database health and connection status

**Key Functions**:
- `check_database_health()`: Check database health
  - Attempts to connect to database
  - Checks if database exists
  - Checks if tables exist
  - Returns health status dict

**Database Queries**: Connection test and system table queries

**Tables Accessed**: `information_schema.tables` (PostgreSQL system table)

### `vulcanLab.data.init_db`

**Purpose**: Initialize database schema

**Key Functions**:
- `init_database(force=False, verbose=False)`: Initialize database
  - Creates database if it doesn't exist
  - Creates application user if it doesn't exist
  - Grants permissions
  - Creates all tables using SQLAlchemy
  - Creates pgvector extension
  - Returns initialization results

**Database Queries**: CREATE DATABASE, CREATE USER, GRANT, CREATE TABLE, CREATE EXTENSION

**Tables Accessed**: Creates all application tables

### `vulcanLab.data.template_loader`

**Purpose**: Load prompt templates from database

**Key Functions**: See Sanitization documentation

**Database Tables**: `prompt_meta`

## Database Tables

### Configuration Storage

Configuration is stored in `vulcanLab.config.json` file (not in database):

- **Location**: Project root (`vulcanLab.config.json`)
- **Format**: JSON file
- **Structure**: Nested object with `database`, `llm`, `paths` sections
- **Secrets**: API keys and passwords stored in `.env` file (not in config JSON)

### `prompt_meta`

**Schema**: See Sanitization documentation for full schema

**Usage in Settings**:
- Stores prompt templates for various operations
- Can be edited via `/settings/templates/[function_tag]` page
- Templates include: query_expansion, rag_augmentation, heading_improvement, etc.

**Query Patterns**:
- `SELECT * FROM prompt_meta WHERE function_tag = ?` (get template)
- `UPDATE prompt_meta SET template = ? WHERE function_tag = ?` (update template)
- `INSERT INTO prompt_meta (function_tag, template) VALUES (?, ?)` (create template)

### `rag_config`

**Schema**: See RAG documentation for full schema

**Usage in Settings**:
- Stores RAG configuration presets
- Default preset: "default"
- Can be managed via Settings page (if UI supports it)

**Query Patterns**:
- `SELECT * FROM rag_config WHERE preset_name = 'default'` (get default config)
- `SELECT * FROM rag_config` (list all presets)
- `UPDATE rag_config SET config = ? WHERE preset_name = ?` (update preset)
- `INSERT INTO rag_config (preset_name, config) VALUES (?, ?)` (create preset)

## Configuration File Structure

### `vulcanLab.config.json`

```json
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "db_name": "vulcanLab",
    "app_user": "vulcanLab_app",
    "admin_user": "postgres"
  },
  "llm": {
    "provider": "openai",
    "models": {
      "openai": {
        "light": "gpt-4o-mini",
        "full": "gpt-4o"
      },
      "gemini": {
        "light": "gemini-1.5-flash",
        "full": "gemini-1.5-pro"
      }
    }
  },
  "paths": {
    "input_dir": "/absolute/path/to/input",
    "output_dir": "/absolute/path/to/output"
  }
}
```

### `.env` File (Secrets)

Secrets are stored in `.env` file (not in config JSON):

```
POSTGRES_APP_PASSWORD=your_app_password
POSTGRES_ADMIN_PASSWORD=your_admin_password
OPENAI_API_KEY=your_openai_key
GEMINI_API_KEY=your_gemini_key
```

## Configuration Management

### Singleton Pattern

- Configuration loaded once and cached
- `load_config()` returns cached config unless `force_reload=True`
- `save_config()` updates cache after saving

### Validation

- Database settings validated on connection attempts
- Paths validated to be absolute paths
- LLM provider validated to be "openai" or "gemini"
- Model names validated but not checked against API

### Default Values

- If config file doesn't exist, `load_config()` returns default config
- Default values defined in `AppConfig` class
- Database defaults: localhost:5432, database name "vulcanLab"
- LLM defaults: OpenAI provider, standard model names
- Paths defaults: None (must be configured)

## Database Initialization

### Initialization Steps

1. **Create Database**: Creates PostgreSQL database if it doesn't exist
2. **Create User**: Creates application user if it doesn't exist
3. **Grant Permissions**: Grants necessary permissions to application user
4. **Create Extension**: Creates pgvector extension for vector operations
5. **Create Tables**: Creates all application tables using SQLAlchemy metadata

### Tables Created

- `works` - Bibliographic works
- `chunks` - Document chunks with embeddings
- `queries` - RAG queries with expansions
- `results` - LLM responses
- `io_files` - Input/output file tracking
- `rag_config` - RAG configuration presets
- `prompt_meta` - Prompt templates

### Health Check

Health check verifies:
- Database connection works
- Database exists
- Tables exist
- Application user has permissions

