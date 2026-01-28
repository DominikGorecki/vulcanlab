#!/bin/bash

# Target path for the Python executable
TARGET_PYTHON="/home/dardawk/python/vulcanlab/venv/bin/python"

# Optional: List matching processes first (uncomment to enable)
# echo "Listing matching processes:"
# ps aux | grep "[/]"${TARGET_PYTHON} || echo "No matching processes found."

# Force kill all matching processes
pkill -9 -f "${TARGET_PYTHON}"

# Check if the kill was successful
if [ $? -eq 0 ]; then
    echo "All matching Python processes have been force-killed."
else
    echo "No processes were found or killed. If permission denied, try running with sudo."
fi