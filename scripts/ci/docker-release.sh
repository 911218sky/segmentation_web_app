#!/bin/bash
set -euo pipefail

# Docker Release 腳本 - 自動觸發 GitHub Actions 建置 Docker 映像
# 用法: bash ./scripts/ci/docker-release.sh

REPO="911218sky/segmentation_web_app"

# 檢查 gh CLI
if ! command -v gh &> /dev/null; then
    echo "錯誤: 請先安裝 GitHub CLI (gh)"
    echo "安裝方式: https://cli.github.com/"
    exit 1
fi

if ! gh auth status &> /dev/null; then
    echo "錯誤: 請先執行 'gh auth login' 登入 GitHub"
    exit 1
fi

# 取得最新版本
echo "正在取得最新版本..."
LATEST_TAG=$(gh release list --repo "$REPO" --limit 1 --json tagName -q '.[0].tagName' 2>/dev/null || echo "v0.0.0")

if [ -z "$LATEST_TAG" ] || [ "$LATEST_TAG" == "null" ]; then
    LATEST_TAG="v0.0.0"
fi

# 解析版本號
VERSION=${LATEST_TAG#v}
IFS='.' read -r MAJOR MINOR PATCH <<< "$VERSION"

echo ""
echo "目前版本: $LATEST_TAG"
echo ""
echo "請選擇版本更新類型:"
echo "  1) Major (主版本): v$MAJOR.$MINOR.$PATCH -> v$((MAJOR + 1)).0.0"
echo "  2) Minor (次版本): v$MAJOR.$MINOR.$PATCH -> v$MAJOR.$((MINOR + 1)).0"
echo "  3) Patch (修補版): v$MAJOR.$MINOR.$PATCH -> v$MAJOR.$MINOR.$((PATCH + 1))"
echo ""
read -p "請輸入選項 (1/2/3): " CHOICE

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
        echo "無效選項"
        exit 1
        ;;
esac

echo ""
echo "新版本: $NEW_VERSION"
read -p "確認觸發 Docker 建置? (y/n): " CONFIRM

if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "已取消"
    exit 0
fi

# 觸發 GitHub Actions
echo ""
echo "正在觸發 Docker 建置..."
gh workflow run docker-publish.yml --repo "$REPO" -f version="$NEW_VERSION"

echo ""
echo "=== 完成！ ==="
echo "已觸發建置版本: $NEW_VERSION"
echo "查看進度: https://github.com/$REPO/actions"
