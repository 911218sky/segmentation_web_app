#!/usr/bin/env bash
# Usage: ./clean-unused.sh [--dry-run] [--yes] [--aggressive] [-h|--help]

set -euo pipefail
IFS=$'\n\t'

DRY_RUN=false
FORCE=false
AGGRESSIVE=false

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
--aggressive  額外移除所有未被任何 container 使用的影像（images）
EOF
      exit 0
      ;;
    *) echo "未知參數: $arg" >&2; exit 1 ;;
  esac
done

# 檢查 docker CLI 與 daemon
if ! command -v docker >/dev/null 2>&1; then
  echo "錯誤：找不到 docker CLI。請先安裝 Docker。" >&2
  exit 2
fi
if ! docker info >/dev/null 2>&1; then
  echo "錯誤：無法連線到 Docker daemon。請確認 docker 已啟動且有權限。" >&2
  exit 2
fi

# helper - count lines safely
count_lines() {
  if [ -z "${1-}" ]; then
    echo 0
  else
    # $1 may contain newlines; count them
    printf "%s\n" "$1" | sed '/^$/d' | wc -l | tr -d ' '
  fi
}

# 收集要刪除的項目（只抓「沒用到」的）
stopped_containers=$(docker ps -a -f "status=exited" -q || true)
dangling_images=$(docker images -f "dangling=true" -q || true)
dangling_volumes=$(docker volume ls -f "dangling=true" -q || true)

# networks: 自訂 network 且沒有任何 container（排除預設的 bridge/host/none）
unused_networks=""
all_networks=$(docker network ls --format '{{.Name}}' || true)
for net in $all_networks; do
  case "$net" in
    bridge|host|none) continue ;;
  esac
  cnt=$(docker network inspect -f '{{len .Containers}}' "$net" 2>/dev/null || echo 0)
  if [ "${cnt}" = "0" ]; then
    unused_networks="${unused_networks}${net}"$'\n'
  fi
done

# aggressive: 找出「未被任何 container 使用的所有 image」
unused_images=""
if [ "$AGGRESSIVE" = true ]; then
  # 取得所有 image IDs（no-trunc 以取得完整 id）
  mapfile -t all_images_arr < <(docker images -a -q --no-trunc | sort -u)
  # 取得 container 使用的 image IDs（inspect .Image 回傳 image ID）
  used_images=""
  if [ "$(docker ps -aq | wc -l | tr -d ' ')" -ne 0 ]; then
    # 確保當沒有 container 時不執行 inspect 導致錯誤
    used_images=$(docker inspect -f '{{.Image}}' $(docker ps -aq) 2>/dev/null || true)
  fi

  # 建立一個暫時 file 便於差集
  tmp_all=$(mktemp)
  tmp_used=$(mktemp)
  printf "%s\n" "${all_images_arr[@]}" | sed '/^$/d' | sort -u > "$tmp_all"
  printf "%s\n" "$used_images" | sed '/^$/d' | sort -u > "$tmp_used"
  # 差集：all - used
  if [ -s "$tmp_all" ]; then
    unused_images=$(comm -23 "$tmp_all" "$tmp_used" || true)
  else
    unused_images=""
  fi
  rm -f "$tmp_all" "$tmp_used"
fi

# Count & preview
stopped_cnt=$(count_lines "$stopped_containers")
dangling_images_cnt=$(count_lines "$dangling_images")
dangling_volumes_cnt=$(count_lines "$dangling_volumes")
unused_networks_cnt=$(count_lines "$unused_networks")
unused_images_cnt=$(count_lines "$unused_images")

echo "預覽："
echo "  已停止的容器 (Exited)： $stopped_cnt"
echo "  懸空影像 (dangling images)： $dangling_images_cnt"
echo "  未使用的 volumes (dangling volumes)： $dangling_volumes_cnt"
echo "  未使用的自訂 networks： $unused_networks_cnt"
if [ "$AGGRESSIVE" = true ]; then
  echo "  額外未被任何 container 使用的 images（aggressive）： $unused_images_cnt"
fi
echo

# 列出每項的範例（最多 10 個）
show_sample() {
  title="$1"; list="$2"
  if [ "$(count_lines "$list")" -gt 0 ]; then
    echo "  $title (最多列出 10 個)："
    printf "%s\n" "$list" | sed '/^$/d' | head -n 10 | sed 's/^/    /'
  fi
}
show_sample "Stopped containers" "$stopped_containers"
show_sample "Dangling images (IDs)" "$dangling_images"
show_sample "Dangling volumes" "$dangling_volumes"
show_sample "Unused networks" "$unused_networks"
if [ "$AGGRESSIVE" = true ]; then
  show_sample "Unused images (IDs)" "$unused_images"
fi
echo

# 確認（除非 --yes 或 --dry-run）
if [ "$FORCE" = false ] && [ "$DRY_RUN" = false ]; then
  read -r -p "確定要繼續清除上述「沒被使用」的資源嗎？輸入 y 繼續： " ans
  case "$ans" in
    y|Y) ;;
    *) echo "已取消。" ; exit 0 ;;
  esac
fi

# dry-run 模式只顯示要做的事
if [ "$DRY_RUN" = true ]; then
  echo "[DRY-RUN] 將會刪除以下資源（若有）："
  [ "$stopped_cnt" -gt 0 ] && printf "  Will remove stopped containers:\n%s\n" "$stopped_containers"
  [ "$dangling_images_cnt" -gt 0 ] && printf "  Will remove dangling images (IDs):\n%s\n" "$dangling_images"
  [ "$dangling_volumes_cnt" -gt 0 ] && printf "  Will remove dangling volumes:\n%s\n" "$dangling_volumes"
  [ "$unused_networks_cnt" -gt 0 ] && printf "  Will remove unused networks:\n%s\n" "$unused_networks"
  [ "$AGGRESSIVE" = true ] && [ "$unused_images_cnt" -gt 0 ] && printf "  Will remove unused images (IDs):\n%s\n" "$unused_images"
  echo "[DRY-RUN] 並會執行 docker builder prune -f 清理 build cache（若有可清除項目）"
  exit 0
fi

# 執行刪除：注意空集合時避免錯誤
if [ "$stopped_cnt" -gt 0 ]; then
  echo "移除已停止容器（含其匿名 volumes）..."
  # -v 會刪除與 container 相關聯的 anonymous volumes
  docker rm -v $(printf "%s " $stopped_containers) || true
fi

if [ "$dangling_images_cnt" -gt 0 ]; then
  echo "移除 dangling images..."
  docker rmi $(printf "%s " $dangling_images) || true
fi

if [ "$dangling_volumes_cnt" -gt 0 ]; then
  echo "移除 dangling volumes..."
  docker volume rm $(printf "%s " $dangling_volumes) || true
fi

if [ "$unused_networks_cnt" -gt 0 ]; then
  echo "移除未使用的自訂 networks..."
  # docker network rm 接受名稱
  docker network rm $(printf "%s " $unused_networks) || true
fi

if [ "$AGGRESSIVE" = true ] && [ "$unused_images_cnt" -gt 0 ]; then
  echo "激進模式：移除所有未被任何 container 使用的 images（注意：可能會移除你想保留的未被 container 使用的 image）..."
  # rmi 可用 image ID
  docker rmi $(printf "%s " $unused_images) || true
fi

# Builder cache prune（非破壞性）
echo "執行 docker builder prune -f（清理 build cache）..."
docker builder prune -f || true

echo "清理完成。"