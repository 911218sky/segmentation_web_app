from typing import Optional
from pathlib import Path
import gdown
import streamlit as st
import re
from utils.file import clean_folder
from config import TEMP_DIR

def _is_video_magic(path: Path) -> bool:
    """
    用 magic bytes 做簡單檢查（支援常見 mp4/mov/m4v/mkv/webm/avi/flv）。
    不是完全保證，但能過濾出 HTML / text / zip 等非影片檔。
    """
    try:
        with open(path, "rb") as f:
            head = f.read(64)
    except Exception:
        return False

    if not head:
        return False

    # mp4/mov/m4v: 內含 'ftyp'（通常在 offset 4）
    if b"ftyp" in head:
        return True
    # mkv / webm: 0x1A 0x45 0xDF 0xA3
    if head.startswith(b"\x1A\x45\xDF\xA3"):
        return True
    # avi: 'RIFF' ... 'AVI '
    if head.startswith(b"RIFF") and b"AVI " in head[:16]:
        return True
    # flv:
    if head.startswith(b"FLV"):
        return True
    # mpeg program stream (very rough): 0x00 00 01 BA
    if head.startswith(b"\x00\x00\x01\xBA"):
        return True
    # fallback: check for webm 'webm' text in header (rare)
    if b"webm" in head.lower():
        return True

    return False

def _extract_file_id_from_drive_url(url: str) -> Optional[str]:
    if not url:
        return None
    url = url.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{10,}", url):
        return url
    m = re.search(r"/d/([A-Za-z0-9_-]+)", url)
    if m:
        return m.group(1)
    m = re.search(r"[?&]id=([A-Za-z0-9_-]+)", url)
    if m:
        return m.group(1)
    return None

def _size_mb(path: Path) -> float:
    try:
        return path.stat().st_size / (1024 * 1024)
    except Exception:
        return 0

def google_video_update(cache: bool = True) -> Optional[Path]:
    """
    Streamlit 工具：只使用 gdown 下載 Google Drive 分享連結（或 file_id）。
    回傳成功時為本機檔案路徑 (str)，失敗或未下載則回傳 None。
    """
    video_dir = TEMP_DIR / "uploaded_videos"
    video_dir.mkdir(parents=True, exist_ok=True)
    clean_folder(video_dir, max_items=10, max_age_days=5)

    st.subheader("🎞️ 從 Google Drive 分享連結下載影片（使用 gdown）")
    hint = "貼上 Google Drive 分享連結 或 直接貼 FILE_ID（例：https://drive.google.com/file/d/FILE_ID/view）"
    url_input = st.text_area(
        "Drive 分享連結 或 file id",
        placeholder=hint,
        key="drive_url_input",
        height=100,
    )

    download_btn = st.button("⬇️ Download", key="download_btn")
    st.info("請輸入 Google Drive 分享連結或 file id，然後按 Download")

    file_id = _extract_file_id_from_drive_url(url_input)
    file_path = video_dir / f"{file_id}.mp4"

    if cache and file_path.exists():
        size_mb = _size_mb(file_path)
        st.success(f"已使用快取：{file_path.name} ({size_mb:.2f} MB)")
        return file_path

    # 若沒有按下 Download 按鈕，直接回傳 None
    if not download_btn:
        return None

    # gdown 會嘗試自動命名並回傳實際檔案路徑
    try:
        with st.spinner("獲取資料中..."):
            out = gdown.download(
                url_input,
                output=str(file_path),
                quiet=True,
                fuzzy=True,
            )
    except Exception as e:
        st.error(f"gdown 下載時發生例外：{e}")
        return None

    # gdown 失敗會回傳 None 或空字串
    if not out:
        st.error("gdown 未回傳下載路徑（下載失敗）。請確認該檔案為公開分享或分享設定為 anyone with link。")
        return None

    # 檔案存在與大小檢查
    if _size_mb(file_path) == 0:
        file_path.unlink(missing_ok=True)
        st.error("下載後檔案大小為 0，下載失敗。")
        return None

    # 檢查副檔名
    is_video_magic = _is_video_magic(file_path)
    
    if not is_video_magic:
        file_path.unlink(missing_ok=True)
        st.error(
            "下載完成，但檔案看起來不是影片檔（副檔名與檔頭檢查皆非影片）。\n"
            "請確認該檔案是否為影片，或是否已設定為 anyone with link。"
        )
        return None

    # 存入快取並回傳
    size_mb = _size_mb(file_path)
    st.success(f"下載完成：{file_path.name} ({size_mb:.2f} MB)")
    return file_path