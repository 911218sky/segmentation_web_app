#!/usr/bin/env bash
set -e

# Local Development Start Script (without Docker)
# Usage: ./scripts/local/dev.sh

# Activate conda or venv
if command -v conda >/dev/null 2>&1; then
  eval "$(conda shell.bash hook)"
  conda activate ./venv 2>/dev/null || true
fi

if [ -z "${CONDA_PREFIX:-}" ] && [ -f "./venv/bin/activate" ]; then
  source ./venv/bin/activate
fi

# Check streamlit
if ! command -v streamlit >/dev/null 2>&1; then
  echo "Error: streamlit is not installed, please run pip install streamlit"
  exit 1
fi

streamlit run app/main.py
