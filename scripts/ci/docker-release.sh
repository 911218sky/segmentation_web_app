#!/bin/bash
set -euo pipefail

# Docker Release Script - Auto trigger GitHub Actions to build Docker image
# Usage: bash ./scripts/ci/docker-release.sh

REPO="911218sky/segmentation_web_app"

# Check gh CLI
if ! command -v gh &> /dev/null; then
    echo "Error: Please install GitHub CLI (gh) first"
    echo "Installation: https://cli.github.com/"
    exit 1
fi

if ! gh auth status &> /dev/null; then
    echo "Error: Please run 'gh auth login' to login to GitHub first"
    exit 1
fi

# Get latest version
echo "Fetching latest version..."
LATEST_TAG=$(gh release list --repo "$REPO" --limit 1 --json tagName -q '.[0].tagName' 2>/dev/null || echo "v0.0.0")

if [ -z "$LATEST_TAG" ] || [ "$LATEST_TAG" == "null" ]; then
    LATEST_TAG="v0.0.0"
fi

# Parse version number
VERSION=${LATEST_TAG#v}
IFS='.' read -r MAJOR MINOR PATCH <<< "$VERSION"

echo ""
echo "Current version: $LATEST_TAG"
echo ""
echo "Select version bump type:"
echo "  1) Major: v$MAJOR.$MINOR.$PATCH -> v$((MAJOR + 1)).0.0"
echo "  2) Minor: v$MAJOR.$MINOR.$PATCH -> v$MAJOR.$((MINOR + 1)).0"
echo "  3) Patch: v$MAJOR.$MINOR.$PATCH -> v$MAJOR.$MINOR.$((PATCH + 1))"
echo ""
read -p "Enter option (1/2/3): " CHOICE

case $CHOICE in
    1)
        NEW_VERSION="v$((MAJOR + 1)).0.0"
        ;;
    2)
        NEW_VERSION="v$MAJOR.$((MINOR + 1)).0"
        ;;
    3)
        NEW_VERSION="v$MAJOR.$MINOR.$((PATCH + 1))"
        ;;
    *)
        echo "Invalid option"
        exit 1
        ;;
esac

echo ""
echo "New version: $NEW_VERSION"
read -p "Confirm trigger Docker build? (y/n): " CONFIRM

if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "Cancelled"
    exit 0
fi

# Trigger GitHub Actions
echo ""
echo "Triggering Docker build..."
gh workflow run docker-publish.yml --repo "$REPO" -f version="$NEW_VERSION"

echo ""
echo "=== Done! ==="
echo "Triggered build for version: $NEW_VERSION"
echo "View progress: https://github.com/$REPO/actions"
