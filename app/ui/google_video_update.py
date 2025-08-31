from typing import Optional
from pathlib import Path
import streamlit as st
import re

from utils.file import clean_folder
from config import TEMP_DIR, SA_FILE, VIDEO_COMPRESSOR
from utils.video_compressor import VideoCompressor
from utils.drive_fetcher import DriveFetcher, DriveFetchResult

# Google Drive URL matcher
_DRIVE_FILE_RE = re.compile(r'https?://(drive|docs)\.google\.com/.+')

# 150 MB
MAX_COMPRESS_SIZE = 1024 * 1024 * 150

# 下載緩存資料夾
UPDATE_DIR = Path(TEMP_DIR) / "uploaded_videos"
UPDATE_DIR.mkdir(parents=True, exist_ok=True)

# 初始化 DriveFetcher
fetcher = DriveFetcher(
    service_account_file=SA_FILE,
    allowed_extensions=['.mp4', '.mov', '.mkv', '.webm', '.avi', '.flv'],
    max_workers=1,
)
compressor = VideoCompressor()

def _is_drive_link(url: str) -> bool:
    """
    檢查是否為 Google Drive 分享連結
    """
    return bool(url and _DRIVE_FILE_RE.match(url.strip()))

def _set_cache(link: str, result: DriveFetchResult):
    """
    設定快取
    """
    if 'drive_video_link_cache' not in st.session_state:
        st.session_state['drive_video_link_cache'] = {}
    st.session_state['drive_video_link_cache'][link] = result

def _get_cache(link: str) -> Optional[DriveFetchResult]:
    """
    取得快取
    """
    if 'drive_video_link_cache' not in st.session_state:
        return None
    return st.session_state['drive_video_link_cache'].get(link)

def _get_compressed_path(path: Path) -> Path:
    """
    取得壓縮後的影片路徑
    """
    return path.with_name(f"{path.stem}_c{path.suffix or '.mp4'}")

def google_video_update() -> Optional[Path]:
    clean_folder(UPDATE_DIR, max_items=10, max_age_days=5)

    st.subheader("🎞️ 從 Google Drive 分享連結下載影片")
    hint = "貼上 Google Drive 分享連結 範例 https://drive.google.com/file/d/1jmK_i5AvezX6fCAZLhTrxm0dUnI3KLQT/view?usp=drive_link"
    url_input = st.text_area(
        "Drive 分享連結 或 file id",
        placeholder=hint,
        key="drive_video_url_input",
        height=100,
    )

    download_btn = st.button("獲取影片", key="download_video_btn")
    st.info("請輸入 Google Drive 分享連結然後按獲取影片 範例 https://drive.google.com/file/d/1jmK_i5AvezX6fCAZLhTrxm0dUnI3KLQT/view?usp=drive_link")

    link = url_input.strip()
    if link and not _is_drive_link(link):
        st.error("請輸入有效的 Google Drive 分享連結或 file id。")
        return None

    # 檢查連結緩存
    if _get_cache(link):
        result = _get_cache(link)
        if result.path.exists():
            st.success(f"已使用連結緩存：{result.path.name}")
            return result.path


    if not download_btn:
        return None

    # 下載新影片
    try:
        with st.spinner("獲取資料中..."):
            results = fetcher.fetch(link, download_dir=UPDATE_DIR, recurse=False, only_list=True)
            # 假如有獲取結果檢查是否有快取
            if results and VIDEO_COMPRESSOR:
                com_path = _get_compressed_path(results[0].path)
                # 檢查壓縮後的影片是否存在
                if com_path.exists():
                    results[0].path = com_path
                    _set_cache(link, results[0])
                    return com_path
                # 壓縮後的影片不存在，檢查原始影片是否存在
                if results[0].path.exists():
                    _set_cache(link, results[0])
                    return results[0].path
            results = fetcher.fetch(link, download_dir=UPDATE_DIR, recurse=False)
    except Exception as e:
        st.error(f"下載過程發生錯誤：{e}")
        return None

    if not results:
        st.error("未找到任何關於影片的檔案或下載失敗，請確認連結或權限設定。")
        return None

    # 選擇第一個影片
    first = results[0]
    if first.error:
        st.error(f"下載失敗：{first.error}")
        return None

    path = Path(first.path)
    if not path.exists():
        st.error(f"下載失敗：{path.name} 不存在")
        return None

    st.success(f"下載完成：{path.name}")

    # 假如超過壓縮影片門檻，壓縮影片
    if first.size > MAX_COMPRESS_SIZE and VIDEO_COMPRESSOR:
        try:
            com_path = _get_compressed_path(path)
            with st.spinner("壓縮影片中..."):
                compressor.compress(str(path), str(com_path), overwrite=True, quiet=True)
            st.success(f"壓縮完成：{com_path.name}")
            # 刪除原檔
            path.unlink()
            # 修改結果路徑
            first.path = com_path
        except Exception as _:
            # 若失敗，清理暫存檔
            if com_path.exists():
                com_path.unlink()
            raise

    # 儲存至連結緩存
    _set_cache(link, first)
    return first.path