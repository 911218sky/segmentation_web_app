from typing import Optional, Dict, Any, List, Tuple
import os
import math
import cv2
import numpy as np
from pathlib import Path
import streamlit as st

from config import (
    TEMP_DIR,
    switch_page,
    get_text,
)
from utils.file import (
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

@st.cache_data(show_spinner=False)
def get_first_frame(video_path: str) -> Optional[np.ndarray]:
    cap = cv2.VideoCapture(video_path)
    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        return None
    return frame
  
def handle_video_processing(
    video_path: Path,
    params: Dict[str, Any],
):
    if video_path is None:
        return
    
    # 保存上傳的影片
    output_dir = TEMP_DIR / "output_videos"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 清理過期檔案
    clean_folder(output_dir, max_items=20, max_age_days=5)
    
    with st.form("video_preview"):
        if video_path.exists():
            st.video(str(video_path))
        st.form_submit_button(get_text('video_refetch'))
    
    intervals = video_intervals()
    
    # 選區（第一幀）
    region = None
    if params.get('region_limit') and video_path.exists():
        frame = get_first_frame(str(video_path))
        if frame is not None:
            region = canvas(frame)
                
    col1, col2 = st.columns(2)
    if col1.button(get_text('start_video_processing')):
        if not intervals:
            st.error(get_text('video_interval_required'))
            return
        st.success(get_text('video_processing_start'))
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
        st.success(get_text('video_processing_complete'))
        
        switch_page("results")

    if col2.button(get_text('clear_video_results')):
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
        st.info(get_text('no_video_results'))
        return

    st.subheader(get_text('video_results_title'))
    
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
                st.markdown(f"### {get_text('video_segment_label')}: {key.replace('_', ' ')} ({iv.start_s:.1f}s - {iv.end_s:.1f}s)")
                st.video(str(iv.file_path))
                
                with open(iv.file_path, 'rb') as f:
                    video_bytes = f.read()
                    st.download_button(
                        label=get_text('download_video'),
                        data=video_bytes,
                        file_name=os.path.basename(iv.file_path),
                        mime="video/mp4"
                    )
                
                with st.expander(get_text('view_stats'), expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(get_text('frame_count'), f"{iv.frame_count}")
                        st.metric(get_text('start_time'), f"{iv.start_s:.1f} s")
                        st.metric(get_text('end_time'), f"{iv.end_s:.1f} s")
                    with col2:
                        st.metric(get_text('max_occurrence_time'), f"{iv.max_at_s:.1f} s")
                        st.metric(get_text('mean_length'), f"{iv.mean_of_means_mm:.3f} mm")
                        st.metric(get_text('max_length'), f"{iv.max_of_means_mm:.3f} mm")
    
    
# 下載區
def video_downloads():
    if not st.session_state.video_results:
        return
    st.subheader(get_text('download_results'))
    buf_xl = generate_excel_video_results(st.session_state.video_results)
    st.download_button(get_text('download_excel'), buf_xl.getvalue(),
                         "video_results.xlsx",
                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")