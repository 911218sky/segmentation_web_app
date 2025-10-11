import math
import zipfile
from io import BytesIO
from typing import List, Dict, Any

import streamlit as st
from PIL import Image
from streamlit.runtime.uploaded_file_manager import UploadedFile
from config import (
    BATCH_SIZE,
    # page config
    switch_page,
    # ui config
    IMAGE_UPLOAD_SESSION_KEY,
)
from ui import canvas
from utils.excel import generate_excel_img_results
from processing import process_batch_images
from utils.canvas import FileLike

def _serialize_uploaded_files(files: List[UploadedFile]) -> List[Dict[str, Any]]:
    """將 Streamlit 的 UploadedFile 物件轉換成可放入 session 的一般資料結構。"""
    serialized: List[Dict[str, Any]] = []
    for upload in files:
        if upload is None:
            continue
        try:
            data = upload.getvalue()
        except Exception:
            # 如果檔案臨時存放位置已失效則略過
            continue
        serialized.append({
            "name": upload.name,
            "type": upload.type,
            "data": data,
        })
    return serialized

def _deserialize_uploaded_files(serialized: List[Dict[str, Any]]) -> List[FileLike]:
    """從序列化的資料還原成可供讀取的 file-like 物件。"""
    buffers: List[FileLike] = []
    for item in serialized:
        data = item.get("data")
        if data is None:
            continue
        buffer = BytesIO(data)
        buffer.name = item.get("name", "uploaded_image")
        buffer.seek(0)
        buffers.append(buffer)
    return buffers

# 上傳區
def upload_images(cache: bool = True) -> List[FileLike]:
    # 移除舊版存放於 session_state 的 UploadedFile
    if "image_uploader" in st.session_state:
        st.session_state.pop("image_uploader", None)

    uploads = st.file_uploader(
        "選擇多張圖片",
        type=['png', 'jpg', 'jpeg', 'bmp', 'tiff'],
        accept_multiple_files=True,
    )

    # 若本次有新的上傳檔案，立即序列化並存入 session_state
    new_serialized = None
    if uploads:
        new_serialized = _serialize_uploaded_files(uploads)
        st.session_state[IMAGE_UPLOAD_SESSION_KEY] = new_serialized

    # 根據 cache 參數決定要使用本次上傳或既有快取，並還原成可讀取的 file-like 物件
    files_to_use: List[FileLike] = []
    if cache:
        serialized = new_serialized if new_serialized is not None else st.session_state.get(IMAGE_UPLOAD_SESSION_KEY, [])
        files_to_use = _deserialize_uploaded_files(serialized)
    elif new_serialized is not None:
        files_to_use = _deserialize_uploaded_files(new_serialized)

    # 使用者可點擊清除按鈕來移除快取並重新整理頁面
    show_clear_button = st.button("🗑️ 清空圖片")
    if show_clear_button:
        st.session_state.pop(IMAGE_UPLOAD_SESSION_KEY, None)
        files_to_use = []
        st.rerun()

    # 回傳實際可供後續處理的檔案串列
    return files_to_use

# 處理按鈕
def handle_image_processing(
    uploads: List[FileLike],
    params: Dict[str, Any],
):
    if uploads is None:
        return
    
    region = None
    # 如果選擇了區域限制，則使用 canvas 選取區域
    if params.get('region_limit') and uploads:
        region = canvas(uploads[0])
    
    col1, col2 = st.columns(2)
    if col1.button("📤 開始批量處理圖片"):
        imgs = [(f.name, Image.open(f)) for f in uploads]
        progress = st.progress(0)
        total_batches = math.ceil(len(imgs)/BATCH_SIZE)
        st.info(f"共 {len(imgs)} 張，分 {total_batches} 批處理")
        results = process_batch_images(
            predictor=st.session_state.predictor,
            images=imgs,
            pixel_size_mm=params['pixel_size_mm'],
            conf_threshold=params['confidence_threshold'],
            region=region,
            line_config={
                'sample_interval': params['sample_interval'],
                'gradient_search_top': params['gradient_search_top'],
                'gradient_search_bottom': params['gradient_search_bottom'],
                'keep_ratio': params['keep_ratio']
            },
            vis_config={
                'line_color': params['line_color'],
                'line_thickness': params['line_thickness'],
                'line_alpha': params['line_alpha'],
                'display_labels': params['display_labels']
            }
        )
        st.session_state.img_results = results
        progress.progress(1.0)
        st.success("✅ 圖片處理完成")
        switch_page("results")

    if col2.button("🗑️ 清空圖片結果"):
        st.session_state.img_results = []
        st.session_state.pop(IMAGE_UPLOAD_SESSION_KEY, None)
        st.rerun()

def image_results():
    res = st.session_state.img_results
    if not res:
        st.info("尚無圖片處理結果")
        return

    st.subheader("📷 圖片處理結果")
    succ = [r for r in res if r['success']]
    fail = [r for r in res if not r['success']]

    st.markdown(f"**成功：{len(succ)}/{len(res)} 張**")

    if succ:
        cols_per_row = 2
        rows = math.ceil(len(succ) / cols_per_row)
        for row in range(rows):
            cols = st.columns(cols_per_row, gap="large")
            for col_idx in range(cols_per_row):
                i = row * cols_per_row + col_idx
                if i >= len(succ):
                    break
                r = succ[i]
                with cols[col_idx]:
                    # 圖片 + 標題
                    st.image(r['result'], caption=r['filename'], use_container_width=True)
                    # 統計數據放在 expander，預設收合
                    with st.expander("🔍 查看統計數據", expanded=True):
                        stats = r['stats']
                        c1, c2 = st.columns(2)
                        with c1:
                            st.metric("信心度", f"{stats['confidence']:.3f}")
                            st.metric("線條數", f"{stats['num_lines']}")
                            st.metric("平均長度", f"{stats['mean_length']:.2f} mm")
                        with c2:
                            st.metric("長度標準差", f"{stats['std_length']:.2f} mm")
                            st.metric("最大長度", f"{stats['max_length']:.2f} mm")
                            st.metric("最小長度", f"{stats['min_length']:.2f} mm")

    # 處理失敗結果
    if fail:
        st.warning(f"⚠️ {len(fail)} 張處理失敗")

# 下載區
def image_downloads():
    imgs = [r for r in st.session_state.img_results if r['success']]
    if not imgs:
        return

    st.subheader("💾 下載處理結果")
    buf_xl = generate_excel_img_results(st.session_state.img_results)
    buf_zip = BytesIO()
    with zipfile.ZipFile(buf_zip, 'w') as zf:
        for r in imgs:
            b = BytesIO()
            r['result'].save(b, format='JPEG')
            zf.writestr(f"images/{r['filename']}.jpg", b.getvalue())
        zf.writestr("image_results.xlsx", buf_xl.getvalue())

    col1, col2 = st.columns(2)
    col1.download_button("下載 ZIP", buf_zip.getvalue(), "image_results.zip", "application/zip")
    col2.download_button("下載 Excel", buf_xl.getvalue(),
                         "image_results.xlsx",
                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
