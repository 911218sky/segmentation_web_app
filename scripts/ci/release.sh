#!/bin/bash
set -euo pipefail

# GitHub Release Upload Script
# Usage: bash ./scripts/ci/release.sh v1.0.0

if [ $# -eq 0 ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 v1.0.0"
    exit 1
fi

VERSION=$1
REPO="911218sky/segmentation_web_app"

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "Error: Please install GitHub CLI (gh) first"
    echo "Installation: https://cli.github.com/"
    exit 1
fi

# Check if logged in
if ! gh auth status &> /dev/null; then
    echo "Error: Please run 'gh auth login' to login to GitHub first"
    exit 1
fi

echo "=== Starting packaging ==="

# Package wheels
echo "Packaging wheels..."
zip -r wheels.zip wheels/

# Package models
echo "Packaging models..."
zip -r models.zip models/

echo "=== Creating Release and uploading ==="

# Create tag if not exists
if ! git rev-parse "$VERSION" &> /dev/null; then
    echo "Creating tag: $VERSION"
    git tag "$VERSION"
    git push origin "$VERSION"
fi

# Create release and upload files
gh release create "$VERSION" \
    --repo "$REPO" \
    --title "$VERSION" \
    --generate-notes \
    wheels.zip \
    models.zip

# Cleanup
rm -f wheels.zip models.zip

echo "=== Done! ==="
echo "Release: https://github.com/$REPO/releases/tag/$VERSION"
