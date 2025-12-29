#!/usr/bin/env bash
set -euo pipefail

# Docker 清理腳本
# 用法: ./scripts/docker/clean.sh [--dry-run] [--aggressive]

DRY_RUN=false
AGGRESSIVE=false

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    --aggressive) AGGRESSIVE=true ;;
    -h|--help)
      echo "用法: $0 [--dry-run] [--aggressive]"
      echo "  --dry-run     只顯示會做的動作"
      echo "  --aggressive  移除所有未使用的映像和 volumes"
      exit 0
      ;;
  esac
done

# 檢查 docker
command -v docker >/dev/null 2>&1 || { echo "錯誤: docker 未安裝"; exit 1; }
docker info >/dev/null 2>&1 || { echo "錯誤: docker daemon 未啟動"; exit 1; }

# 預覽
echo "預覽:"
echo "  已停止容器: $(docker ps -aq -f status=exited | wc -l)"
echo "  懸空映像: $(docker images -qf dangling=true | wc -l)"
echo "  未使用 volumes: $(docker volume ls -qf dangling=true | wc -l)"

if [ "$DRY_RUN" = true ]; then
  echo "[DRY-RUN] 不執行實際清理"
  exit 0
fi

# 執行清理
if [ "$AGGRESSIVE" = true ]; then
  docker system prune -af --volumes
else
  docker system prune -f --volumes
fi

docker builder prune -f
echo "✅ 清理完成"
