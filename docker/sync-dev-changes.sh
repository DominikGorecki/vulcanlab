#!/bin/bash
# ============================================================================
# VulcanLab Development Sync Script
# ============================================================================
# Sync local code changes to a running Docker container and rebuild services
# without requiring a full container rebuild.
#
# Usage:
#   ./sync-dev-changes.sh [backend|frontend|both] [container-name]
#
# Examples:
#   ./sync-dev-changes.sh backend           # Sync backend only
#   ./sync-dev-changes.sh frontend          # Sync frontend only
#   ./sync-dev-changes.sh both              # Sync both (default)
#   ./sync-dev-changes.sh backend my-container  # Custom container name
# ============================================================================

set -e

# Configuration
CONTAINER_NAME="${2:-vulcanlab}"
SYNC_TARGET="${1:-both}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

check_container_running() {
    if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        print_error "Container '${CONTAINER_NAME}' is not running"
        echo ""
        echo "Available running containers:"
        docker ps --format "  - {{.Names}}"
        echo ""
        echo "Usage: $0 [backend|frontend|both] [container-name]"
        exit 1
    fi
    print_success "Container '${CONTAINER_NAME}' is running"
}

restart_service() {
    local service_name=$1

    # Try supervisorctl first
    if docker exec "${CONTAINER_NAME}" supervisorctl status "${service_name}" &>/dev/null; then
        docker exec "${CONTAINER_NAME}" supervisorctl restart "${service_name}"
        return 0
    fi

    # Fallback: kill process and let supervisor restart it
    print_info "Using fallback restart method (searching and killing process)..."
    case "$service_name" in
        backend)
            # Find and kill uvicorn process
            PID=$(docker exec "${CONTAINER_NAME}" bash -c "ps aux | grep '[u]vicorn' | awk '{print \$2}' | head -1")
            if [ -n "$PID" ]; then
                docker exec "${CONTAINER_NAME}" kill -HUP "$PID" 2>/dev/null || true
            fi
            ;;
        frontend)
            # Find and kill node process
            PID=$(docker exec "${CONTAINER_NAME}" bash -c "ps aux | grep '[n]ode.*server.js' | awk '{print \$2}' | head -1")
            if [ -n "$PID" ]; then
                docker exec "${CONTAINER_NAME}" kill -HUP "$PID" 2>/dev/null || true
            fi
            ;;
    esac
    sleep 3
    return 0
}

check_service_status() {
    local service_name=$1

    # Try supervisorctl first
    if docker exec "${CONTAINER_NAME}" supervisorctl status "${service_name}" 2>/dev/null | grep -q "RUNNING"; then
        return 0
    fi

    # Fallback: check if process is running using ps
    case "$service_name" in
        backend)
            docker exec "${CONTAINER_NAME}" bash -c "ps aux | grep -q '[u]vicorn'" 2>/dev/null
            ;;
        frontend)
            docker exec "${CONTAINER_NAME}" bash -c "ps aux | grep -q '[n]ode.*server.js'" 2>/dev/null
            ;;
        *)
            return 1
            ;;
    esac
}

# ============================================================================
# Backend Sync
# ============================================================================

sync_backend() {
    print_header "Syncing Backend Changes"

    # Sync Python source code
    print_info "Copying Python modules..."
    docker cp "${PROJECT_ROOT}/src/vulcanlab/." "${CONTAINER_NAME}:/app/src/vulcanlab/"
    print_success "Python modules synced"

    print_info "Copying API code..."
    docker cp "${PROJECT_ROOT}/src/vulcanlab_api/." "${CONTAINER_NAME}:/app/src/vulcanlab_api/"
    print_success "API code synced"

    # Restart backend service
    print_info "Restarting backend service..."
    if restart_service backend; then
        sleep 2
        if check_service_status backend; then
            print_success "Backend service restarted successfully"
        else
            print_error "Backend service may not have restarted"
            print_info "Backend code synced - restart container or manually restart service"
        fi
    else
        print_info "Backend code synced - restart container to apply changes"
    fi
}

# ============================================================================
# Frontend Sync
# ============================================================================

sync_frontend() {
    print_header "Syncing Frontend Changes"

    # Check if container is using standalone mode
    if docker exec "${CONTAINER_NAME}" test -f /app/vulcanlab_ui/server.js 2>/dev/null && \
       ! docker exec "${CONTAINER_NAME}" test -f /app/vulcanlab_ui/node_modules/.bin/next 2>/dev/null; then
        print_info "Container using standalone mode - building locally first..."

        # Build locally
        print_info "Running local Next.js build..."
        cd "${PROJECT_ROOT}/vulcanlab_ui"

        # Use correct npm (prefer nvm if available)
        if [ -f "$HOME/.nvm/nvm.sh" ]; then
            source "$HOME/.nvm/nvm.sh"
        fi

        npm run build
        print_success "Local build complete"

        # Sync built output (standalone mode)
        print_info "Copying standalone build output..."
        docker cp "${PROJECT_ROOT}/vulcanlab_ui/.next/standalone/." "${CONTAINER_NAME}:/app/vulcanlab_ui/"
        print_success "Standalone files synced"

        print_info "Copying static assets..."
        docker cp "${PROJECT_ROOT}/vulcanlab_ui/.next/static/." "${CONTAINER_NAME}:/app/vulcanlab_ui/.next/static/"
        print_success "Static assets synced"

        print_info "Copying public assets..."
        docker cp "${PROJECT_ROOT}/vulcanlab_ui/public/." "${CONTAINER_NAME}:/app/vulcanlab_ui/public/"
        print_success "Public assets synced"
    else
        # Full dev mode with node_modules
        print_info "Copying frontend source code..."
        docker cp "${PROJECT_ROOT}/vulcanlab_ui/src/." "${CONTAINER_NAME}:/app/vulcanlab_ui/src/"
        print_success "Source code synced"

        # Check if package.json changed
        if [ -f "${PROJECT_ROOT}/vulcanlab_ui/package.json" ]; then
            print_info "Checking package.json..."
            TEMP_PKG=$(mktemp)
            docker cp "${CONTAINER_NAME}:/app/vulcanlab_ui/package.json" "$TEMP_PKG" 2>/dev/null || true

            if ! diff -q "${PROJECT_ROOT}/vulcanlab_ui/package.json" "$TEMP_PKG" &>/dev/null; then
                print_info "package.json changed - copying and reinstalling dependencies..."
                docker cp "${PROJECT_ROOT}/vulcanlab_ui/package.json" "${CONTAINER_NAME}:/app/vulcanlab_ui/package.json"
                docker cp "${PROJECT_ROOT}/vulcanlab_ui/package-lock.json" "${CONTAINER_NAME}:/app/vulcanlab_ui/package-lock.json"
                docker exec "${CONTAINER_NAME}" bash -c "cd /app/vulcanlab_ui && npm ci --omit=dev --ignore-scripts"
                print_success "Dependencies reinstalled"
            fi
            rm -f "$TEMP_PKG"
        fi

        # Rebuild in container
        print_info "Rebuilding Next.js application in container..."
        docker exec "${CONTAINER_NAME}" bash -c "cd /app/vulcanlab_ui && npm run build"
        print_success "Frontend rebuilt"
    fi

    # Restart frontend service
    print_info "Restarting frontend service..."
    if restart_service frontend; then
        sleep 3
        if check_service_status frontend; then
            print_success "Frontend service restarted successfully"
        else
            print_error "Frontend service may not have restarted"
            print_info "Frontend code synced - restart container or manually restart service"
        fi
    else
        print_info "Frontend code synced - restart container to apply changes"
    fi
}

# ============================================================================
# Main Script
# ============================================================================

main() {
    print_header "VulcanLab Development Sync"

    # Validate sync target
    if [[ ! "$SYNC_TARGET" =~ ^(backend|frontend|both)$ ]]; then
        print_error "Invalid sync target: $SYNC_TARGET"
        echo ""
        echo "Usage: $0 [backend|frontend|both] [container-name]"
        exit 1
    fi

    # Check if container is running
    check_container_running

    # Perform sync based on target
    case "$SYNC_TARGET" in
        backend)
            sync_backend
            ;;
        frontend)
            sync_frontend
            ;;
        both)
            sync_backend
            sync_frontend
            ;;
    esac

    # Final status
    print_header "Service Status"
    if docker exec "${CONTAINER_NAME}" supervisorctl status 2>/dev/null; then
        : # supervisorctl worked
    else
        print_info "Service status check:"
        if check_service_status backend; then
            print_success "Backend: Running"
        else
            print_error "Backend: Not running"
        fi
        if check_service_status frontend; then
            print_success "Frontend: Running"
        else
            print_error "Frontend: Not running"
        fi
    fi

    print_header "Sync Complete!"
    print_success "Changes synced to container '${CONTAINER_NAME}'"
    echo ""
    print_info "Frontend: http://localhost:3000"
    print_info "Backend API: http://localhost:8000"
    print_info "API Docs: http://localhost:8000/docs"
    echo ""
}

# Run main function
main
