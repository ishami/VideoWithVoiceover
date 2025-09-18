#!/bin/bash

# Function to check and create logs directory
setup_logs_directory() {
    if [ -d "logs" ]; then
        if [ -w "logs" ]; then
            echo "Logs directory exists and is writable."
        else
            echo "ERROR: Logs directory exists but is not writable!"
            exit 1
        fi
    else
        echo "Logs directory doesn't exist. Creating it..."
        if mkdir -p logs; then
            echo "Logs directory created successfully."
        else
            echo "ERROR: Failed to create logs directory!"
            exit 1
        fi
    fi
}

# Setup logs directory
setup_logs_directory

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Log files
APP_LOG="logs/app_${TIMESTAMP}.log"
ERROR_LOG="logs/error_${TIMESTAMP}.log"
COMBINED_LOG="logs/combined_${TIMESTAMP}.log"

echo "Starting application at $(date)" | tee "${COMBINED_LOG}"
echo "Logs will be saved to:"
echo "  - stdout: ${APP_LOG}"
echo "  - stderr: ${ERROR_LOG}"
echo "  - combined: ${COMBINED_LOG}"
echo "----------------------------------------"

# Create named pipes
mkfifo stdout_pipe stderr_pipe

# Start tee processes in background
tee "${APP_LOG}" < stdout_pipe | tee -a "${COMBINED_LOG}" &
tee "${ERROR_LOG}" < stderr_pipe | tee -a "${COMBINED_LOG}" >&2 &

# Run the main script
./stop.sh
./run.sh prod > stdout_pipe 2> stderr_pipe

# Store exit code
EXIT_CODE=$?

# Clean up pipes
rm stdout_pipe stderr_pipe

# Create symlinks to latest logs
ln -sf "app_${TIMESTAMP}.log" "logs/app_latest.log"
ln -sf "error_${TIMESTAMP}.log" "logs/error_latest.log"
ln -sf "combined_${TIMESTAMP}.log" "logs/combined_latest.log"

echo "----------------------------------------" | tee -a "${COMBINED_LOG}"
echo "Application stopped at $(date) with exit code: ${EXIT_CODE}" | tee -a "${COMBINED_LOG}"

# Exit with the same code as the application
exit ${EXIT_CODE}
