#!/bin/bash
set -euo pipefail

# Start Web Interface in a new thread
(
    bash /app/scripts/web-docker.sh
) &
WEB_PID=$!

# Wait for Web Interface thread to finish
wait $WEB_PID