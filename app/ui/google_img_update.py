from typing import Optional, List
from pathlib import Path
import streamlit as st
import re
from PIL import Image

from utils.file import clean_folder
from config import TEMP_DIR, SA_FILE, IMAGE_COMPRESSOR
from utils.drive_fetcher import DriveFetcher, DriveFetchResult

# Google Drive URL matcher
_DRIVE_FILE_RE = re.compile(r'https?://(drive|docs)\.google\.com/.+')

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

    st.subheader("🎞️ 從 Google Drive 分享連結下載圖片")
    hint = "貼上 Google Drive 分享連結 或 直接貼 FILE_ID 範例 https://drive.google.com/drive/folders/1ppSMdn1YYdc8rN56uKgWJhqezzneajAY?usp=drive_link"
    
    url_input = st.text_area(
        "Drive 分享連結 或 file id",
        placeholder=hint,
        key="drive_img_url_input",
        height=100,
    )

    download_btn = st.button("獲取圖片", key="download_img_btn")
    st.info("請輸入 Google Drive 分享連結或 file id，然後按 獲取圖片")

    link = url_input.strip()
    if link and not _is_drive_link(link):
        st.error("請輸入有效的 Google Drive 分享連結或 file id。")
        return None

    # 檢查連結緩存
    if _get_cache(link):
        result = _get_cache(link)
        if result:
            st.success(f"已使用連結緩存 共 {len(result)} 張圖片")
            return [Path(r.path) for r in result]

    if not download_btn:
        return None

    # 下載圖片
    try:
        with st.spinner("獲取資料中..."):
            all_exists = True
            results = fetcher.fetch(link, download_dir=UPDATE_DIR, recurse=False, only_list=True, preserve_structure=False)
            # 假如有獲取結果檢查是否有快取
            if results and IMAGE_COMPRESSOR:
                # 壓縮圖片
                for r in results:
                    com_path = _get_compressed_path(r.path, r.path.suffix)
                    if com_path.exists():
                        r.path = com_path
                    else:
                        all_exists = False
                        break
            # 如果所有圖片都存在，則儲存至連結緩存
            if all_exists:
                _set_cache(link, results)
                return [Path(r.path) for r in results]
            
            results = fetcher.fetch(link, download_dir=UPDATE_DIR, recurse=False, preserve_structure=False)
    except Exception as e:
        st.error(f"下載過程發生錯誤：{e}")
        return None
    
    st.success(f"下載完成 共 {len(results)} 張圖片")
    
    # 壓縮圖片
    if IMAGE_COMPRESSOR:
        with st.spinner("壓縮圖片中..."):
            for r in results:
                com_path = _get_compressed_path(r.path, r.path.suffix)
                _compress_with_pillow(r.path, com_path, quality=85, to_webp=False)
                # 刪除原始圖片
                r.path.unlink()
                # 更新結果路徑
                r.path = com_path
            st.success(f"壓縮完成 共 {len(results)} 張圖片")

    # 儲存至連結緩存
    _set_cache(link, results)
    return [Path(r.path) for r in results]