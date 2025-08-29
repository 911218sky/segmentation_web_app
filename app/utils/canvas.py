import streamlit as st
from typing import Tuple, Union
from pathlib import Path
from PIL import Image
from streamlit.runtime.uploaded_file_manager import UploadedFile

from config import CANVAS_CONFIG

XYWH = Tuple[int, int, int, int]
FileLike = Union[str, Path, Image.Image, UploadedFile]

def convert_original_xywh_to_resized(
    region: Tuple[float, float, float, float],
    src_size: Tuple[int, int],
    target_size: Tuple[int, int],
    *,
    clip: bool = True,
) -> Tuple[int, int, int, int]:
    """
    把原始圖片座標 (x, y, w, h) 轉換到 letterbox -> resized 座標系。
    
    Args:
        region: (x, y, w, h) in original pixel coordinates (top-left origin),
                或 dict with keys {'x','y','w','h'}.
        src_size: (src_w, src_h) 原始圖片寬高（pixels）
        target_size: (target_w, target_h) letterbox 之後的目標寬高（pixels）
        clip: 是否在回傳前把結果裁切到 [0, target_w/target_h] 範圍內（預設 True）
    
    Returns:
        (x_resized, y_resized, w_resized, h_resized) in the resized coordinate system,
        或若 region is None 則回傳 None。
    """
    x, y, w, h = map(float, region)
    
    src_w, src_h = src_size
    target_w, target_h = target_size
    
    # scale 與新的（縮放後）寬高（跟你原始片段一致）
    scale = min(target_w / src_w, target_h / src_h)
    new_w = src_w * scale
    new_h = src_h * scale

    # letterbox padding（在目標畫布上的偏移量）
    pad_left = (target_w - new_w) / 2.0
    pad_top = (target_h - new_h) / 2.0

    # 轉換座標：先乘 scale，然後加上 padding
    x_r = x * scale + pad_left
    y_r = y * scale + pad_top
    w_r = w * scale
    h_r = h * scale
    
    if clip:
        # clip x,y,w,h 使盒子保持在 [0, target_w/target_h]
        # 先確保 w/h 非負
        w_r = max(0.0, w_r)
        h_r = max(0.0, h_r)
        # clip x,y so that x in [0, target_w] and y in [0, target_h]
        x_r = min(max(x_r, 0.0), float(target_w))
        y_r = min(max(y_r, 0.0), float(target_h))
        # optionally ensure box doesn't overflow right/bottom
        if x_r + w_r > target_w:
            w_r = max(0.0, float(target_w) - x_r)
        if y_r + h_r > target_h:
            h_r = max(0.0, float(target_h) - y_r)
    
    return int(x_r), int(y_r), int(w_r), int(h_r)

def process_image_for_canvas(
    image_file: FileLike,
) -> Tuple[Image.Image, Tuple[int, int], Tuple[int, int]]:
    """
    讀取並依畫布寬高上限對圖片進行高品質重採樣。
    回傳: resized_img, original_size(tuple), canvas_size(tuple)
    """
    key = f"canvas_cache_{getattr(image_file, 'file_id', id(image_file))}"
    if key in st.session_state:
        return st.session_state[key]
 
    if isinstance(image_file, Image.Image):
        img = image_file
    else:
        img = Image.open(image_file)

    max_canvas_w = CANVAS_CONFIG['max_canvas_w']
    max_canvas_h = CANVAS_CONFIG['max_canvas_h']

    # 先依寬度試算高度
    canvas_w = max_canvas_w
    canvas_h = int(canvas_w * img.height / img.width)

    # 若高度超過上限，改依高度試算寬度
    if canvas_h > max_canvas_h:
        canvas_h = max_canvas_h
        canvas_w = int(canvas_h * img.width / img.height)

    resized_img = img.resize(
        (canvas_w, canvas_h),
        resample=Image.Resampling.LANCZOS
    )

    st.session_state[key] = (resized_img, (img.width, img.height), (canvas_w, canvas_h))
    return st.session_state[key]