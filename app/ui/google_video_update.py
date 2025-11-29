from typing import Optional
from pathlib import Path
import streamlit as st
import re

from utils.file import clean_folder
from config import TEMP_DIR, SA_FILE, VIDEO_COMPRESSOR, get_text
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

    st.subheader(get_text('google_video_download_subtitle'))
    hint = get_text('google_drive_link_hint_videos')
    url_input = st.text_area(
        get_text('google_drive_link_label'),
        placeholder=hint,
        key="drive_video_url_input",
        height=100,
    )

    download_btn = st.button(get_text('google_video_download_button'), key="download_video_btn")
    st.info(get_text('google_video_info'))

    link = url_input.strip()
    if link and not _is_drive_link(link):
        st.error(get_text('google_drive_invalid_link'))
        return None

    # 檢查連結緩存
    if _get_cache(link):
        result = _get_cache(link)
        if result.path.exists():
            st.success(get_text('google_video_cached').format(name=result.path.name))
            return result.path


    if not download_btn:
        return None

    # 下載新影片
    try:
        with st.spinner(get_text('google_fetching_data')):
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
        st.error(get_text('google_video_download_error').format(error=e))
        return None

    if not results:
        st.error(get_text('google_video_no_results'))
        return None

    # 選擇第一個影片
    first = results[0]
    if first.error:
        st.error(get_text('google_video_fetch_failed').format(error=first.error))
        return None

    path = Path(first.path)
    if not path.exists():
        st.error(get_text('google_video_path_missing').format(name=path.name))
        return None

    st.success(get_text('google_video_download_complete').format(name=path.name))

    # 假如超過壓縮影片門檻，壓縮影片
    if first.size > MAX_COMPRESS_SIZE and VIDEO_COMPRESSOR:
        try:
            com_path = _get_compressed_path(path)
            with st.spinner(get_text('google_video_compressing')):
                compressor.compress(str(path), str(com_path), overwrite=True, quiet=True)
            st.success(get_text('google_video_compress_complete').format(name=com_path.name))
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