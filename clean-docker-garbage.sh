#!/usr/bin/env bash
# clean-docker.sh - 簡單清理 Docker 垃圾
# 用法: ./clean-docker.sh [--dry-run] [--yes] [--aggressive]

set -euo pipefail
IFS=$'\n\t'

DRY_RUN=false
FORCE=false
AGGRESSIVE=false

# 解析參數（超簡單）
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    --yes)     FORCE=true ;;
    --aggressive) AGGRESSIVE=true ;;
    -h|--help)
      cat <<EOF
Usage: $0 [--dry-run] [--yes] [--aggressive]

--dry-run     只顯示會做的動作（不刪除）
--yes         不要求確認，直接執行
--aggressive  激進模式：包含未被任何 container 使用的影像與 volumes（等同 docker system prune -a --volumes）
EOF
      exit 0
      ;;
    *)
      echo "未知參數: $arg"
      exit 1
      ;;
  esac
done

# 檢查 docker CLI 與 daemon
if ! command -v docker >/dev/null 2>&1; then
  echo "錯誤：找不到 docker CLI。請先安裝 Docker。"
  exit 2
fi
if ! docker info >/dev/null 2>&1; then
  echo "錯誤：無法連線到 Docker daemon。請確認 docker 已啟動且有權限。"
  exit 2
fi

# 預覽要刪除的項目（數量）
stopped_cnt=$(docker ps -a -f "status=exited" -q | wc -l)
dangling_images_cnt=$(docker images -f "dangling=true" -q | wc -l)
dangling_volumes_cnt=$(docker volume ls -f "dangling=true" -q | wc -l)

echo "預覽："
echo "  已停止的容器 (Exited)： $stopped_cnt"
echo "  懸空影像 (dangling images)： $dangling_images_cnt"
echo "  未使用的 volumes (dangling volumes)： $dangling_volumes_cnt"
if [ "$AGGRESSIVE" = true ]; then
  echo "  模式：激進（會移除所有未被任何容器使用的影像與未使用的 volumes）"
else
  echo "  模式：安全（只移除 dangling resources 與 build cache）"
fi
echo

# 確認（除非 --yes 或 --dry-run）
if [ "$FORCE" = false ] && [ "$DRY_RUN" = false ]; then
  read -r -p "確定要繼續清除嗎？這會刪除上面列出的資源。輸入 y 繼續： " ans
  case "$ans" in
    y|Y) ;; 
    *) echo "已取消。"; exit 0 ;;
  esac
fi

# 組裝要執行的命令
if [ "$AGGRESSIVE" = true ]; then
  prune_cmd="docker system prune -a --volumes -f"
else
  prune_cmd="docker system prune --volumes -f"
fi
builder_cmd="docker builder prune -f"

# 執行或顯示（dry-run）
if [ "$DRY_RUN" = true ]; then
  echo "[DRY-RUN] 將會執行： $prune_cmd"
  echo "[DRY-RUN] 將會執行： $builder_cmd"
  echo "（未實際刪除）"
  exit 0
fi

# 執行
echo "執行： $prune_cmd"
eval "$prune_cmd"

echo "執行： $builder_cmd"
eval "$builder_cmd"

echo "清理完成。"