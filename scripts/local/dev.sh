#!/usr/bin/env bash
set -e

# 本地開發啟動腳本（不使用 Docker）
# 用法: ./scripts/local/dev.sh

# 啟用 conda 或 venv
if command -v conda >/dev/null 2>&1; then
  eval "$(conda shell.bash hook)"
  conda activate ./venv 2>/dev/null || true
fi

if [ -z "${CONDA_PREFIX:-}" ] && [ -f "./venv/bin/activate" ]; then
  source ./venv/bin/activate
fi

# 檢查 streamlit
if ! command -v streamlit >/dev/null 2>&1; then
  echo "錯誤: streamlit 未安裝，請執行 pip install streamlit"
  exit 1
fi

streamlit run app/main.py
