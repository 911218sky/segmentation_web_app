#!/usr/bin/env bash
set -euo pipefail

# Docker Compose Start Script
# Usage: ./scripts/docker/start.sh [foreground|background]

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

COMPOSE_FILE=${COMPOSE_FILE:-docker-compose.yml}

# Set UID/GID
export HOST_UID=${HOST_UID:-$(id -u)}
export HOST_GID=${HOST_GID:-$(id -g)}

# Check docker
command -v docker &>/dev/null || { echo -e "${RED}Error: docker is not installed${NC}"; exit 1; }
docker compose version &>/dev/null || { echo -e "${RED}Error: docker compose v2 is not installed${NC}"; exit 1; }
[ -f "$COMPOSE_FILE" ] || { echo -e "${RED}Error: $COMPOSE_FILE does not exist${NC}"; exit 1; }

# Parse mode
MODE=${1:-foreground}
case "$MODE" in
  f|foreground) DETACH="" ;;
  b|background) DETACH="-d" ;;
  *) echo "Usage: $0 [foreground|background]"; exit 1 ;;
esac

echo -e "${BLUE}Starting service (UID=$HOST_UID, GID=$HOST_GID)...${NC}"
docker compose -f "$COMPOSE_FILE" up $DETACH

if [ -n "$DETACH" ]; then
  echo -e "${GREEN}✅ Service started in background${NC}"
  echo -e "View status: docker compose ps"
  echo -e "View logs: docker compose logs -f"
fi
