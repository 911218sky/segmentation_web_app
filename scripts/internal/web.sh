#!/usr/bin/env bash
set -e

# Docker Internal Web Start Script
# Called by entrypoint.sh

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Create required directories
for d in "user_configs" "temp"; do
  mkdir -p "${PROJECT_ROOT}/${d}"
done

streamlit run "${PROJECT_ROOT}/app/main.py"
