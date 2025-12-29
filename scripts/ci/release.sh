#!/bin/bash
set -euo pipefail

# GitHub Release 上傳腳本
# 用法: bash ./scripts/ci/release.sh v1.0.0

if [ $# -eq 0 ]; then
    echo "用法: $0 <version>"
    echo "範例: $0 v1.0.0"
    exit 1
fi

VERSION=$1
REPO="911218sky/segmentation_web_app"

# 檢查 gh CLI 是否安裝
if ! command -v gh &> /dev/null; then
    echo "錯誤: 請先安裝 GitHub CLI (gh)"
    echo "安裝方式: https://cli.github.com/"
    exit 1
fi

# 檢查是否已登入
if ! gh auth status &> /dev/null; then
    echo "錯誤: 請先執行 'gh auth login' 登入 GitHub"
    exit 1
fi

echo "=== 開始打包 ==="

# 打包 wheels
echo "打包 wheels..."
zip -r wheels.zip wheels/

# 打包 models
echo "打包 models..."
zip -r models.zip models/

echo "=== 建立 Release 並上傳 ==="

# 建立 tag（如果不存在）
if ! git rev-parse "$VERSION" &> /dev/null; then
    echo "建立 tag: $VERSION"
    git tag "$VERSION"
    git push origin "$VERSION"
fi

# 建立 release 並上傳檔案
gh release create "$VERSION" \
    --repo "$REPO" \
    --title "$VERSION" \
    --generate-notes \
    wheels.zip \
    models.zip

# 清理
rm -f wheels.zip models.zip

echo "=== 完成！ ==="
echo "Release: https://github.com/$REPO/releases/tag/$VERSION"
