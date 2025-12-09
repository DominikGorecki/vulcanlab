#!/bin/bash
set -e

echo "==================================================================="
echo "VulcanLab Docker Container Starting"
echo "==================================================================="

# Initialize PostgreSQL data directory if it doesn't exist
if [ ! -s "/var/lib/postgresql/data/PG_VERSION" ]; then
    echo "PostgreSQL data directory is empty. Initializing database cluster..."

    # Ensure postgres user owns the data directory
    chown -R postgres:postgres /var/lib/postgresql/data

    # Initialize database cluster as postgres user
    su - postgres -c "/usr/lib/postgresql/16/bin/initdb -D /var/lib/postgresql/data"

    echo "Database cluster initialized. Starting PostgreSQL for setup..."

    # Configure PostgreSQL to load AGE extension
    echo "shared_preload_libraries = 'age'" >> /var/lib/postgresql/data/postgresql.conf

    # Configure PostgreSQL to accept local connections during setup
    cat >> /var/lib/postgresql/data/pg_hba.conf <<EOF
# Allow local connections for initialization
local   all             all                                     trust
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust
EOF

    # Start PostgreSQL temporarily for setup
    su - postgres -c "/usr/lib/postgresql/16/bin/pg_ctl -D /var/lib/postgresql/data -o '-c listen_addresses=localhost' -w start"

    # Wait for PostgreSQL to be ready
    echo "Waiting for PostgreSQL to accept connections..."
    until su - postgres -c "psql -U postgres -c 'SELECT 1'" > /dev/null 2>&1; do
        echo "  Still waiting..."
        sleep 1
    done

    echo "PostgreSQL is ready. Running initialization scripts..."

    # Run initialization scripts from /docker-entrypoint-initdb.d/
    for f in /docker-entrypoint-initdb.d/*; do
        case "$f" in
            *.sh)
                echo "Running $f"
                if [ -x "$f" ]; then
                    bash "$f"
                else
                    chmod +x "$f"
                    bash "$f"
                fi
                ;;
            *.sql)
                echo "Running $f"
                su - postgres -c "psql -U postgres < $f"
                ;;
            *)
                echo "Ignoring $f (not .sh or .sql)"
                ;;
        esac
    done

    # Update pg_hba.conf for production use
    echo "Configuring PostgreSQL for production..."
    cat > /var/lib/postgresql/data/pg_hba.conf <<EOF
# PostgreSQL Client Authentication Configuration
# TYPE  DATABASE        USER            ADDRESS                 METHOD

# Allow local connections with password
local   all             all                                     md5

# Allow localhost connections with password
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5
EOF

    # Stop PostgreSQL (supervisord will start it properly)
    echo "Stopping temporary PostgreSQL instance..."
    su - postgres -c "/usr/lib/postgresql/16/bin/pg_ctl -D /var/lib/postgresql/data -m fast -w stop"

    echo "PostgreSQL initialization complete!"
else
    echo "PostgreSQL data directory exists. Skipping initialization."
fi

# Ensure log directory exists and has correct permissions
mkdir -p /var/log/supervisor
chmod 755 /var/log/supervisor

# Ensure data directories exist
mkdir -p /app/data/input /app/data/output
chmod 755 /app/data/input /app/data/output

# Display configuration
echo "-------------------------------------------------------------------"
echo "Configuration:"
echo "  - PostgreSQL Data: /var/lib/postgresql/data"
echo "  - Input Directory: /app/data/input"
echo "  - Output Directory: /app/data/output"
echo "  - Logs: /var/log/supervisor/"
echo "-------------------------------------------------------------------"

# Check for required environment variables
MISSING_ENV=0

if [ -z "$POSTGRES_ADMIN_PASSWORD" ]; then
    echo "WARNING: POSTGRES_ADMIN_PASSWORD not set. Database may fail to initialize."
    MISSING_ENV=1
fi

if [ -z "$POSTGRES_APP_PASSWORD" ]; then
    echo "WARNING: POSTGRES_APP_PASSWORD not set. Application user creation will fail."
    MISSING_ENV=1
fi

if [ -z "$LLM_GOOGLE_API_KEY" ] && [ -z "$LLM_OPENAI_API_KEY" ]; then
    echo "WARNING: No LLM API keys set. Backend may not function correctly."
    echo "  Set at least one of: LLM_GOOGLE_API_KEY, LLM_OPENAI_API_KEY"
    MISSING_ENV=1
fi

if [ $MISSING_ENV -eq 1 ]; then
    echo "-------------------------------------------------------------------"
    echo "IMPORTANT: Missing environment variables detected."
    echo "Please ensure you run the container with --env-file .env.docker"
    echo "-------------------------------------------------------------------"
fi

echo "Starting services with supervisord..."
echo "==================================================================="

# Set defaults for optional environment variables (supervisord requires all referenced vars to exist)
export LLM_GOOGLE_API_KEY="${LLM_GOOGLE_API_KEY:-}"
export LLM_OPENAI_API_KEY="${LLM_OPENAI_API_KEY:-}"
export POSTGRES_ADMIN_PASSWORD="${POSTGRES_ADMIN_PASSWORD:-}"
export POSTGRES_APP_PASSWORD="${POSTGRES_APP_PASSWORD:-}"

# Execute the main command (supervisord)
exec "$@"
