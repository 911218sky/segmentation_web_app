#!/usr/bin/env bash
set -euo pipefail

# Docker Cleanup Script
# Usage: ./scripts/docker/clean.sh [--dry-run] [--aggressive]

DRY_RUN=false
AGGRESSIVE=false

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    --aggressive) AGGRESSIVE=true ;;
    -h|--help)
      echo "Usage: $0 [--dry-run] [--aggressive]"
      echo "  --dry-run     Show what would be done without executing"
      echo "  --aggressive  Remove all unused images and volumes"
      exit 0
      ;;
  esac
done

# Check docker
command -v docker >/dev/null 2>&1 || { echo "Error: docker is not installed"; exit 1; }
docker info >/dev/null 2>&1 || { echo "Error: docker daemon is not running"; exit 1; }

# Preview
echo "Preview:"
echo "  Stopped containers: $(docker ps -aq -f status=exited | wc -l)"
echo "  Dangling images: $(docker images -qf dangling=true | wc -l)"
echo "  Unused volumes: $(docker volume ls -qf dangling=true | wc -l)"

if [ "$DRY_RUN" = true ]; then
  echo "[DRY-RUN] No actual cleanup performed"
  exit 0
fi

# Execute cleanup
if [ "$AGGRESSIVE" = true ]; then
  docker system prune -af --volumes
else
  docker system prune -f --volumes
fi

docker builder prune -f
echo "✅ Cleanup complete"
