#!/bin/bash

# Script to create symbolic links from documentation/ai_context/dot_* to .* directories
# Ignores README.md files

set -e  # Exit on error

# Get the script directory and repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SOURCE_DIR="$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "Setting up symbolic links..."
echo "Source directory: $SOURCE_DIR"
echo "Repo root: $REPO_ROOT"
echo ""

# Function to create symlinks for a source directory
create_symlinks() {
    local source_base="$1"
    local dest_base="$2"
    local source_name="$3"
    
    if [ ! -d "$source_base" ]; then
        echo -e "${YELLOW}Warning: Source directory $source_base does not exist, skipping...${NC}"
        return
    fi
    
    echo -e "${GREEN}Processing $source_name -> $dest_base${NC}"
    
    # Find all files in source_base, excluding README.md files
    find "$source_base" -type f ! -name "README.md" | while read -r source_file; do
        # Get relative path from source_base
        rel_path="${source_file#$source_base/}"
        
        # Destination file path
        dest_file="$REPO_ROOT/$dest_base/$rel_path"
        dest_dir="$(dirname "$dest_file")"
        
        # Create destination directory if it doesn't exist
        mkdir -p "$dest_dir"
        
        # Calculate relative path from destination to source
        # We need to go from REPO_ROOT/dest_base/... to SOURCE_DIR/source_base/...
        # Get the directory path relative to repo root
        dest_dir_rel="${dest_dir#$REPO_ROOT/}"
        # Count slashes in directory path to determine depth
        # e.g., ".cursor/commands/" has 1 slash, need 2 ../ to reach repo root
        slash_count=$(echo "$dest_dir_rel" | tr -cd '/' | wc -c)
        # Number of ../ needed = slash_count + 1 (for each directory level)
        relative_path=""
        for ((i=0; i<=slash_count; i++)); do
            relative_path="../$relative_path"
        done
        relative_path="${relative_path}documentation/ai_context/$source_name/$rel_path"
        
        # Remove existing file/link if it exists
        if [ -e "$dest_file" ] || [ -L "$dest_file" ]; then
            echo -e "  ${YELLOW}Removing existing: $dest_file${NC}"
            rm -f "$dest_file"
        fi
        
        # Create symbolic link
        ln -s "$relative_path" "$dest_file"
        echo -e "  ${GREEN}Linked: $rel_path -> $dest_file${NC}"
    done
    
    echo ""
}

# Create destination directories
mkdir -p "$REPO_ROOT/.claude"
mkdir -p "$REPO_ROOT/.cursor"

# Process dot_claude -> .claude
create_symlinks "$SOURCE_DIR/dot_claude" ".claude" "dot_claude"

# Process dot_cursor -> .cursor
create_symlinks "$SOURCE_DIR/dot_cursor" ".cursor" "dot_cursor"

echo -e "${GREEN}Symbolic link setup complete!${NC}"

