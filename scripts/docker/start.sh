#!/usr/bin/env bash
set -euo pipefail

# Docker Compose 啟動腳本
# 用法: ./scripts/docker/start.sh [foreground|background]

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

COMPOSE_FILE=${COMPOSE_FILE:-docker-compose.yml}

# 設定 UID/GID
export HOST_UID=${HOST_UID:-$(id -u)}
export HOST_GID=${HOST_GID:-$(id -g)}

# 檢查 docker
command -v docker &>/dev/null || { echo -e "${RED}錯誤: docker 未安裝${NC}"; exit 1; }
docker compose version &>/dev/null || { echo -e "${RED}錯誤: docker compose v2 未安裝${NC}"; exit 1; }
[ -f "$COMPOSE_FILE" ] || { echo -e "${RED}錯誤: $COMPOSE_FILE 不存在${NC}"; exit 1; }

# 解析模式
MODE=${1:-foreground}
case "$MODE" in
  f|foreground) DETACH="" ;;
  b|background) DETACH="-d" ;;
  *) echo "用法: $0 [foreground|background]"; exit 1 ;;
esac

echo -e "${BLUE}啟動服務 (UID=$HOST_UID, GID=$HOST_GID)...${NC}"
docker compose -f "$COMPOSE_FILE" up $DETACH

if [ -n "$DETACH" ]; then
  echo -e "${GREEN}✅ 服務已在背景啟動${NC}"
  echo -e "查看狀態: docker compose ps"
  echo -e "查看日誌: docker compose logs -f"
fi
