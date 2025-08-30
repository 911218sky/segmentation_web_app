from typing import Optional, Dict, Any, List, Tuple
import os
import math
import cv2
import time
import numpy as np

import streamlit as st
from streamlit_chunked_upload import uploader as chunk_uploader
from streamlit.runtime.uploaded_file_manager import UploadedFile

from config import (
    TEMP_DIR,
    switch_page,
)
from utils.file import (
    save_uploaded_to_dir,
    clean_folder,
)
from utils.excel import generate_excel_video_results
from processing import (
    process_video,
    IntervalStat,
)
from ui import (
    canvas,
    video_intervals,
)

def upload_video(cache: bool = True) -> Optional[UploadedFile]:
    st.subheader("🎞️ 上傳影片")
    
    # st.session_state.video_uploader = st.file_uploader(
    #     "選擇影片 (mp4/mov/avi/mkv)", type=['mp4','mov','avi','mkv'],
    #     accept_multiple_files=False,
    # )
    
    if not cache or not st.session_state.get("video_uploader"):
        st.session_state.video_uploader = chunk_uploader(
            label="選擇影片 (mp4/mov/avi/mkv)",
            chunk_size=2,
            type=['mp4','mov','avi','mkv'],
            uploader_msg="選擇影片 (mp4/mov/avi/mkv) 建議不超過 1GB",
        )
    
    show_clear_button = st.button("🗑️ 清空影片")
    if show_clear_button:
        st.session_state.video_uploader = None
        st.rerun()
    
    return st.session_state.video_uploader

@st.cache_data(show_spinner=False)
def get_first_frame(video_path: str) -> Optional[np.ndarray]:
    cap = cv2.VideoCapture(video_path)
    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        return None
    return frame
  
def handle_video_processing(
    upload: UploadedFile,
    params: Dict[str, Any],
):
    if upload is None:
        return
    
    # 保存上傳的影片
    video_dir = TEMP_DIR / "uploaded_videos"
    output_dir = TEMP_DIR / "output_videos"
    video_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 清理過期檔案
    clean_folder(video_dir, max_items=2, max_age_days=1)
    clean_folder(output_dir, max_items=20, max_age_days=5)
    
    # 保存上傳的影片快取
    if st.session_state.get("last_video_data") is None:
        video_path = save_uploaded_to_dir(upload, video_dir)
        st.session_state["last_video_data"] = {
            "video_path": video_path,
            "video_id": id(upload),
        }
    # 如果上傳的影片有變更，則重新保存
    elif id(upload) != st.session_state["last_video_data"]["video_id"]:
        video_path = save_uploaded_to_dir(upload, video_dir)
        st.session_state["last_video_data"] = {
            "video_path": video_path,
            "video_id": id(upload),
        }
    else:
        video_path = st.session_state["last_video_data"]["video_path"]
    
    video_slot = st.empty()
    if video_path.exists():
        video_slot.video(str(video_path))
    
    intervals = video_intervals()
    
    # 選區（第一幀）
    region = None
    if params.get('region_limit') and video_path.exists():
        frame = get_first_frame(str(video_path))
        if frame is not None:
            region = canvas(frame)
                
    col1, col2 = st.columns(2)
    if col1.button("📤 開始處理影片"):
        if not intervals:
            st.error("請先設定時間區間")
            return
        st.success("🔍 開始處理影片 ... 請稍候")
        stats = process_video(
            predictor=st.session_state.predictor,
            video_path=video_path,
            pixel_size_mm=params['pixel_size_mm'],
            conf_threshold=params['confidence_threshold'],
            region=region,
            intervals=intervals,
            line_config={
                "sample_interval": params['sample_interval'],
                "gradient_search_top": params['gradient_search_top'],
                "gradient_search_bottom": params['gradient_search_bottom'],
                "keep_ratio": params['keep_ratio'],
            },
            vis_config={
                'line_color': params['line_color'],
                'line_thickness': params['line_thickness'],
                'line_alpha': params['line_alpha'],
                'display_labels': params['display_labels']
            },
            output_dir=output_dir,
        )
        st.session_state.video_results = stats
        st.success("✅ 影片處理完成")
        
        switch_page("results")

    if col2.button("🗑️ 清空影片結果"):
        st.session_state.video_results = {}
        st.rerun()
        
# 結果區
def video_results():
    """
    將 st.session_state.video_results (dict of IntervalStat) 
    以卡片式呈現，每段影片都附上视频预览和相关统计指标。
    """
    stats_dict: Dict[str, IntervalStat] = st.session_state.get("video_results", {})
    if not stats_dict:
        st.info("尚無影片處理結果")
        return

    st.subheader("🎞️ 影片結果檢視")
    
    items: List[Tuple[str, IntervalStat]] = list(stats_dict.items())
    cards_per_row = 2
    num_rows = math.ceil(len(items) / cards_per_row)

    for row in range(num_rows):
        cols = st.columns(cards_per_row, gap="large")
        for i in range(cards_per_row):
            idx = row * cards_per_row + i
            if idx >= len(items):
                break
            key, iv = items[idx]
            with cols[i]:
                # 標題與影片預覽
                st.markdown(f"### ▶️ 片段：{key.replace('_', ' ')}  ({iv.start_s:.1f}s - {iv.end_s:.1f}s)")
                st.video(str(iv.file_path))
                
                with open(iv.file_path, 'rb') as f:
                    video_bytes = f.read()
                    st.download_button(
                        label="⬇️ 下載影片",
                        data=video_bytes,
                        file_name=os.path.basename(iv.file_path),
                        mime="video/mp4"
                    )
                
                with st.expander("🔍 查看統計數據", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("幀數", f"{iv.frame_count}")
                        st.metric("開始時間", f"{iv.start_s:.1f} s")
                        st.metric("結束時間", f"{iv.end_s:.1f} s")
                    with col2:
                        st.metric("最大出現秒數", f"{iv.max_at_s:.1f} s")
                        st.metric("平均長度", f"{iv.mean_of_means_mm:.3f} mm")
                        st.metric("最大長度", f"{iv.max_of_means_mm:.3f} mm")
    
    
# 下載區
def video_downloads():
    if not st.session_state.video_results:
        return
    st.subheader("💾 下載處理結果")
    buf_xl = generate_excel_video_results(st.session_state.video_results)
    st.download_button("下載 Excel", buf_xl.getvalue(),
                         "video_results.xlsx",
                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")