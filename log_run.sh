#!/bin/bash

# Function to check and create logs directory
setup_logs_directory() {
    if [ -d "logs" ]; then
        [ -w "logs" ] || { echo "ERROR: Logs directory exists but is not writable!" >&2; exit 1; }
    else
        mkdir -p logs || { echo "ERROR: Failed to create logs directory!" >&2; exit 1; }
    fi
}

# Setup logs directory
setup_logs_directory

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ERROR_LOG="logs/error_${TIMESTAMP}.log"

echo "Starting application at $(date)"
echo "Errors will be saved to: ${ERROR_LOG}"
echo "----------------------------------------"

# Run your commands
./stop.sh
./run.sh prod 2> >(tee -a "${ERROR_LOG}" >&2)

EXIT_CODE=$?

echo "----------------------------------------"
echo "Application stopped at $(date) with exit code: ${EXIT_CODE}"

exit $EXIT_CODE

