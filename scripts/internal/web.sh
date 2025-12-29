#!/usr/bin/env bash
set -e

# Docker 內部 Web 啟動腳本
# 由 entrypoint.sh 呼叫

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# 建立必要資料夾
for d in "user_configs" "temp"; do
  mkdir -p "${PROJECT_ROOT}/${d}"
done

streamlit run "${PROJECT_ROOT}/app/main.py"
