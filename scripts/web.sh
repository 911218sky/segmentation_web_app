#!/usr/bin/env bash
set -e

# 讓 conda 在 script 裡可用（如果有安裝）
if command -v conda >/dev/null 2>&1; then
  eval "$(conda shell.bash hook)"
  # 嘗試用 conda activate（如果 ./venv 是 conda env）
  conda activate ./venv 2>/dev/null || true
fi

# 若 conda 沒啟動，再嘗試 python venv
if [ -z "${CONDA_PREFIX:-}" ] && [ -f "./venv/bin/activate" ]; then
  source ./venv/bin/activate
fi

# 檢查 streamlit 是否在環境中
if ! command -v streamlit >/dev/null 2>&1; then
  echo "錯誤：streamlit 不在目前環境，請先安裝（pip install streamlit）"
  exit 1
fi

streamlit run app/main.py