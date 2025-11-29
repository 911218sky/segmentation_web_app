#!/usr/bin/env bash
set -euo pipefail

# Default parameters (override via env)
PROJECT_NAME=${PROJECT_NAME:-vessel_measure}
COMPOSE_FILE=${COMPOSE_FILE:-docker-compose.yml}
SERVICE=${SERVICE:-vessel}
IMAGE=${IMAGE:-sky1218/vessel-measure:latest}
PLATFORMS=${PLATFORMS:-}
DOCKERFILE=${DOCKERFILE:-Dockerfile}
BUILD_CACHE=${BUILD_CACHE:-true}
USE_REMOTE=${USE_REMOTE:-false}
PUSH=${PUSH:-true}

HOST_UID=${HOST_UID:-1234}
HOST_GID=${HOST_GID:-1234}
if [ -z "${HOST_UID}" ]; then HOST_UID=$(id -u); fi
if [ -z "${HOST_GID}" ]; then HOST_GID=$(id -g); fi

export HOST_UID HOST_GID

# ANSI colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# check required commands
command -v docker &>/dev/null || { echo -e "${RED}Error: docker not found${NC}"; exit 1; }
docker compose version &>/dev/null || { echo -e "${RED}Error: docker compose (v2) not found${NC}"; exit 1; }

# If USE_REMOTE=true, just pull and exit
if [ "${USE_REMOTE}" = "true" ]; then
  echo -e "${BLUE}🔄 USE_REMOTE=true: pulling remote image ${IMAGE}${NC}"
  if docker pull "${IMAGE}"; then
    echo -e "${GREEN}✅ Successfully pulled ${IMAGE}${NC}"
    exit 0
  else
    echo -e "${RED}❌ Failed to pull ${IMAGE}${NC}"
    exit 1
  fi
fi

# Enable BuildKit and docker compose CLI builds
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# If building multi-platform, ensure binfmt / buildx are ready
if [ -n "${PLATFORMS}" ]; then
  # Ensure docker buildx exists
  if ! docker buildx version &>/dev/null; then
    echo -e "${YELLOW}docker buildx not found or not available. Trying to continue...${NC}"
  fi

  # Create and use a builder if none active (safe to run repeatedly)
  if ! docker buildx inspect multi-builder &>/dev/null; then
    echo -e "${YELLOW}Creating docker buildx builder 'multi-builder'...${NC}"
    docker buildx create --name multi-builder --use || true
  else
    docker buildx use multi-builder 2>/dev/null || true
  fi

  # Register QEMU binfmt handlers to enable cross-platform emulation (only if not already)
  if ! docker run --rm --privileged tonistiigi/binfmt --version &>/dev/null; then
    echo -e "${YELLOW}Installing QEMU binfmt handlers (required for multi-platform) ...${NC}"
    docker run --rm --privileged tonistiigi/binfmt:latest --install all
  fi
fi

# Prepare cache flag
if [ "${BUILD_CACHE}" = "false" ]; then
  NO_CACHE_FLAG="--no-cache"
  echo -e "${YELLOW}⚠️  BUILD_CACHE=false: building without cache${NC}"
else
  NO_CACHE_FLAG=""
  echo -e "${GREEN}✅ BUILD_CACHE=true: building with cache${NC}"
fi

# Build command selection
if [ -n "${PLATFORMS}" ]; then
  # Determine Buildx output mode: use --push if PUSH=true, otherwise use --load (load to local docker)
  OUTPUT_FLAG="--load"
  if [ "${PUSH}" = "true" ]; then
    OUTPUT_FLAG="--push"
  fi

  echo -e "${BLUE}🔧 Building multi-platform image: ${PLATFORMS} (Output: ${OUTPUT_FLAG})${NC}"
  
  BUILD_CMD=(docker buildx build ${OUTPUT_FLAG} ${NO_CACHE_FLAG} --platform "${PLATFORMS}" --tag "${IMAGE}" -f "${DOCKERFILE}" --build-arg USER_ID="${HOST_UID}" --build-arg GROUP_ID="${HOST_GID}" .)
else
  echo -e "${BLUE}🔧 Building local image via docker compose (service=${SERVICE})${NC}"
  BUILD_CMD=(docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" build ${NO_CACHE_FLAG} --build-arg USER_ID="${HOST_UID}" --build-arg GROUP_ID="${HOST_GID}" "${SERVICE}")
fi

# Print and run build command
echo -e "${BLUE}>> ${BUILD_CMD[*]}${NC}"
if "${BUILD_CMD[@]}"; then
  echo -e "${GREEN}✅ Build succeeded: ${IMAGE}${NC}"

  # (If Buildx mode is used with PUSH=true, the command above already included --push)
  if [ "${PUSH}" = "true" ] && [ -z "${PLATFORMS}" ]; then
    echo -e "${BLUE}🚀 Pushing image to registry...${NC}"
    if docker push "${IMAGE}"; then
      echo -e "${GREEN}✅ Push succeeded${NC}"
    else
      echo -e "${RED}❌ Push failed${NC}"
      exit 1
    fi
  fi

else
  echo -e "${RED}❌ Build failed${NC}"
  exit 1
fi