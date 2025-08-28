#!/usr/bin/env bash
set -euo pipefail

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Defaults (can override via environment variables)
COMPOSE_FILE=${COMPOSE_FILE:-docker-compose.yml}
PROJECT_NAME=${PROJECT_NAME:-vessel_measure}
SERVICE=${SERVICE:-vessel}

# --------------------------------------------------------------------
# Prerequisite checks
# --------------------------------------------------------------------
echo -e "${YELLOW}Checking prerequisites...${NC}"
command -v docker &>/dev/null || { echo -e "${RED}Error: docker not installed${NC}"; exit 1; }
docker compose version &>/dev/null || { echo -e "${RED}Error: docker compose (V2) not installed${NC}"; exit 1; }
[ -f "$COMPOSE_FILE" ] || { echo -e "${RED}Error: Compose file '$COMPOSE_FILE' not found${NC}"; exit 1; }
echo -e "${GREEN}Prerequisites OK${NC}"

# --------------------------------------------------------------------
# Show what will be used
# --------------------------------------------------------------------
echo
echo -e "${BLUE}Using compose file: ${GREEN}${COMPOSE_FILE}${NC}"
echo -e "${BLUE}Project name:      ${GREEN}${PROJECT_NAME}${NC}"
echo -e "${BLUE}Target service:    ${GREEN}${SERVICE}${NC}"
echo

# --------------------------------------------------------------------
# Prompt: foreground or background
# --------------------------------------------------------------------
echo -e "${YELLOW}How would you like to start the service '${SERVICE}'?${NC}"
echo "  [f] foreground (attach logs)"
echo "  [b] background (detached mode)"
read -r -p "Enter choice (f/b) [f]: " MODE
MODE=${MODE:-f}

case "$MODE" in
  f|F)
    DETACH_FLAG=""
    ATTACH_AFTER_START=false
    echo -e "${GREEN}You chose: foreground (will attach logs)${NC}"
    ;;
  b|B)
    DETACH_FLAG="-d"
    ATTACH_AFTER_START=false
    echo -e "${GREEN}You chose: background (detached)${NC}"
    ;;
  *)
    echo -e "${YELLOW}Invalid choice, defaulting to foreground${NC}"
    DETACH_FLAG=""
    ;;
esac

# --------------------------------------------------------------------
# Start services
# --------------------------------------------------------------------
echo
echo -e "${BLUE}Starting service '${SERVICE}' now...${NC}"
# Use set -x style printing but more readable
echo -e "${BLUE}>> docker compose -p \"$PROJECT_NAME\" -f \"$COMPOSE_FILE\" up $DETACH_FLAG $SERVICE${NC}"

docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" up $DETACH_FLAG "$SERVICE"

if [ -n "$DETACH_FLAG" ]; then
  echo
  echo -e "${GREEN}✅ Service '${SERVICE}' started in detached mode.${NC}"
  echo -e "${BLUE}To view status: ${NC}docker compose -p \"$PROJECT_NAME\" -f \"$COMPOSE_FILE\" ps"
  echo -e "${BLUE}To follow logs: ${NC}docker compose -p \"$PROJECT_NAME\" -f \"$COMPOSE_FILE\" logs -f $SERVICE"
else
  echo
  echo -e "${GREEN}✅ Foreground run ended (compose exited).${NC}"
fi

# --------------------------------------------------------------------
# End message
# --------------------------------------------------------------------
echo
echo -e "${GREEN}Done. If you started detached, use the commands above to inspect or stop.${NC}"