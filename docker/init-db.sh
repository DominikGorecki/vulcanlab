#!/bin/bash
set -e

echo "==================================================================="
echo "Initializing VulcanLab Database"
echo "==================================================================="

# This script runs inside the PostgreSQL context during first-time setup
# It's called from docker-entrypoint.sh when PostgreSQL is running temporarily

# Environment variables (with defaults)
# DB_NAME="${POSTGRES_DB:-vulcanlab_test}"
# DB_USER="${POSTGRES_APP_USER:-vulcanlab_app_user_test}"
DB_PASSWORD="${POSTGRES_APP_PASSWORD}"
ADMIN_PASSWORD="${POSTGRES_ADMIN_PASSWORD}"


# Check for required environment variables
if [ -z "$DB_PASSWORD" ]; then
    echo "ERROR: POSTGRES_APP_PASSWORD environment variable is not set!"
    exit 1
fi

# if [ -z "$ADMIN_PASSWORD" ]; then
#     echo "ERROR: POSTGRES_ADMIN_PASSWORD environment variable is not set!"
#     exit 1
# fi

# Set password for postgres superuser
echo "Setting password for postgres superuser"
psql -v ON_ERROR_STOP=1 --username "postgres" <<-EOSQL
    ALTER USER postgres WITH PASSWORD '$ADMIN_PASSWORD';
EOSQL

echo "Postgres superuser password set"

# # Create database
# echo "Creating database: $DB_NAME"
# psql -v ON_ERROR_STOP=1 --username "postgres" <<-EOSQL
#     -- Check if database exists first
#     SELECT 'CREATE DATABASE $DB_NAME ENCODING ''UTF8'' LC_COLLATE ''en_US.UTF-8'' LC_CTYPE ''en_US.UTF-8'' TEMPLATE template0'
#     WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec
# EOSQL

# echo "Database '$DB_NAME' created (or already exists)"

# # Connect to the new database and set up extensions
# echo "Setting up extensions in database: $DB_NAME"
# psql -v ON_ERROR_STOP=1 --username "postgres" --dbname "$DB_NAME" <<-EOSQL
#     -- Enable pgvector extension
#     CREATE EXTENSION IF NOT EXISTS vector;

#     -- Enable Apache AGE extension
#     CREATE EXTENSION IF NOT EXISTS age;

#     -- Load AGE shared library
#     LOAD 'age';

#     -- Set search path for AGE to work properly
#     -- This makes ag_catalog functions available by default
#     ALTER DATABASE $DB_NAME SET search_path = ag_catalog, "\$user", public;
# EOSQL

# echo "Extensions enabled: vector, age"

# # Create application user if it doesn't exist
# echo "Creating application user: $DB_USER"
# psql -v ON_ERROR_STOP=1 --username "postgres" --dbname "$DB_NAME" <<-EOSQL
#     -- Create user if not exists
#     DO \$\$
#     BEGIN
#         IF NOT EXISTS (SELECT FROM pg_user WHERE usename = '$DB_USER') THEN
#             CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
#         END IF;
#     END
#     \$\$;

#     -- Grant database privileges
#     GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;

#     -- Grant schema privileges
#     GRANT ALL ON SCHEMA public TO $DB_USER;
#     GRANT ALL ON SCHEMA ag_catalog TO $DB_USER;

#     -- Grant permissions on all tables (current and future)
#     GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;
#     GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;
#     GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO $DB_USER;

#     -- Set default privileges for future objects
#     ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
#     ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;
#     ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO $DB_USER;
# EOSQL

# echo "User '$DB_USER' created with full privileges"

# # Verify extensions are installed
# echo "Verifying extensions..."
# psql -v ON_ERROR_STOP=1 --username "postgres" --dbname "$DB_NAME" <<-EOSQL
#     SELECT extname, extversion FROM pg_extension WHERE extname IN ('vector', 'age');
# EOSQL

# echo "==================================================================="
# echo "Database initialization complete!"
# echo "Database: $DB_NAME"
# echo "User: $DB_USER"
# echo "Extensions: vector, age"
# echo "==================================================================="
