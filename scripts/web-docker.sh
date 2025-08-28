#!/usr/bin/env bash
set -e

# 取得專案根目錄（假設 run.sh 在 scripts/）
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 要建立的資料夾（會在專案根目錄下）
DIRS=("user_configs" "temp")

for d in "${DIRS[@]}"; do
  if [ ! -d "${PROJECT_ROOT}/${d}" ]; then
    echo "建立資料夾： ${PROJECT_ROOT}/${d}"
    mkdir -p "${PROJECT_ROOT}/${d}"
  else
    echo "已存在： ${PROJECT_ROOT}/${d}"
  fi
done

# 啟動 streamlit（使用專案裡的 app/main.py）
streamlit run "${PROJECT_ROOT}/app/main.py"