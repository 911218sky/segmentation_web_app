from typing import Optional, List
from pathlib import Path
import streamlit as st
import re
from PIL import Image

from utils.file import clean_folder
from config import TEMP_DIR, SA_FILE, IMAGE_COMPRESSOR, get_text
from utils.drive_fetcher import DriveFetcher, DriveFetchResult

# Google Drive URL matcher
_DRIVE_FILE_RE = re.compile(r'https?://(drive|docs)\.google\.com/.+')

# 壓縮門檻 2 MB
MAX_COMPRESS_SIZE = 1024 * 1024 * 2

# 下載緩存資料夾
UPDATE_DIR = Path(TEMP_DIR) / "uploaded_images"
UPDATE_DIR.mkdir(parents=True, exist_ok=True)

# 初始化 DriveFetcher
fetcher = DriveFetcher(
    service_account_file=SA_FILE,
    allowed_extensions=['.jpg', '.jpeg', '.png'],
    max_workers=8,
)

def _is_drive_link(url: str) -> bool:
    """
    檢查是否為 Google Drive 分享連結
    """
    return bool(url and _DRIVE_FILE_RE.match(url.strip()))

def _set_cache(link: str, result: List[DriveFetchResult]):
    """
    設定快取
    """
    if 'drive_img_link_cache' not in st.session_state:
        st.session_state['drive_img_link_cache'] = {}
    st.session_state['drive_img_link_cache'][link] = result

def _get_cache(link: str) -> Optional[List[DriveFetchResult]]:
    """
    取得快取
    """
    if 'drive_img_link_cache' not in st.session_state:
        return None
    return st.session_state['drive_img_link_cache'].get(link)

def _get_compressed_path(path: Path, ext: str) -> Path:
    """
    取得壓縮後的圖片路徑
    """
    return path.with_name(f"{path.stem}_c{ext}")

def _compress_with_pillow(
    in_path: Path,
    out_path: Path,
    quality: int = 85,
    to_webp: bool = False,
):
    im = Image.open(in_path)
    if to_webp:
        im.save(out_path, "WEBP", quality=quality, method=6) 
    else:
        im = im.convert("RGB")
        im.save(out_path, "JPEG", quality=quality, optimize=True, progressive=True)

def google_img_update() -> Optional[List[Path]]:
    clean_folder(UPDATE_DIR, max_items=500, max_age_days=5)

    st.subheader(get_text('google_img_download_subtitle'))
    hint = get_text('google_drive_link_hint_images')
    
    url_input = st.text_area(
        get_text('google_drive_link_label'),
        placeholder=hint,
        key="drive_img_url_input",
        height=100,
    )

    download_btn = st.button(get_text('google_img_download_button'), key="download_img_btn")
    st.info(get_text('google_img_info'))

    link = url_input.strip()
    if link and not _is_drive_link(link):
        st.error(get_text('google_drive_invalid_link'))
        return None

    # 檢查連結緩存
    if _get_cache(link):
        result = _get_cache(link)
        if result:
            st.success(get_text('google_img_cache_used').format(count=len(result)))
            return [Path(r.path) for r in result]

    if not download_btn:
        return None

    # 下載圖片
    try:
        with st.spinner(get_text('google_fetching_data')):
            all_exists = True
            results = fetcher.fetch(link, download_dir=UPDATE_DIR, recurse=False, only_list=True, preserve_structure=False)
            # 假如有獲取結果檢查是否有快取
            if results and IMAGE_COMPRESSOR:
                # 壓縮圖片
                for r in results:
                    com_path = _get_compressed_path(r.path, r.path.suffix)
                    # 壓縮後的圖片存在，則更新結果路徑
                    if com_path.exists():
                        r.path = com_path
                    # 壓縮後的圖片不存在，檢查原始圖片是否存在
                    elif r.path.exists():
                        pass
                    else:
                        all_exists = False
                        break
            # 如果所有圖片都存在，則儲存至連結緩存
            if all_exists:
                _set_cache(link, results)
                return [Path(r.path) for r in results]
            
            results = fetcher.fetch(link, download_dir=UPDATE_DIR, recurse=False, preserve_structure=False)
    except Exception as e:
        st.error(get_text('google_img_download_error').format(error=e))
        return None
    
    st.success(get_text('google_img_download_complete').format(count=len(results)))
    
    # 壓縮圖片
    if IMAGE_COMPRESSOR:
        with st.spinner(get_text('google_img_compressing')):
            for r in results:
                if r.size > MAX_COMPRESS_SIZE:
                    com_path = _get_compressed_path(r.path, r.path.suffix)
                    _compress_with_pillow(r.path, com_path, quality=85, to_webp=False)
                    # 刪除原始圖片
                    r.path.unlink()
                    # 更新結果路徑
                    r.path = com_path
            st.success(get_text('google_img_compress_complete').format(count=len(results)))

    # 儲存至連結緩存
    _set_cache(link, results)
    return [Path(r.path) for r in results]