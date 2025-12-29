#!/bin/bash
set -euo pipefail

# Docker 容器入口點
# 由 Dockerfile CMD 呼叫

bash /app/scripts/internal/web.sh
