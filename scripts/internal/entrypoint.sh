#!/bin/bash
set -euo pipefail

# Docker Container Entrypoint
# Called by Dockerfile CMD

bash /app/scripts/internal/web.sh
