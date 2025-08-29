from typing import Optional

import numpy as np
import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image as PILImage

from config import CANVAS_CONFIG
from config.language import get_text
from utils.canvas import process_image_for_canvas, XYWH, FileLike

def canvas(
    uploaded_file: FileLike,
    rect_width: int = CANVAS_CONFIG["rect_width"],
    rect_height: int = CANVAS_CONFIG["rect_height"],
) -> Optional[XYWH]:
    """
    渲染可繪製畫布區域 - 單張圖片，固定矩形尺寸，只能移動位置。
    Args:
        uploaded_file: file-like / path / PIL.Image
        rect_width, rect_height: rectangle size in ORIGINAL image pixels
    Returns:
        region in ORIGINAL image coordinates (x, y, w, h) or None if no selection.
    """
    st.subheader(get_text("interactive_selection"))
    
    # 如果上傳的是 numpy 陣列，則轉換為 PIL 圖片
    if isinstance(uploaded_file, np.ndarray):
        uploaded_file = PILImage.fromarray(uploaded_file)

    # 處理圖片（resized 輸出用於 canvas 背景）
    resized_img, orig_size, canvas_size = process_image_for_canvas(uploaded_file)

    st.markdown("**調整選取區域尺寸**")
    col1, col2 = st.columns(2)
    with col1:
        fixed_width: int = st.number_input(
            "寬度 (px)",
            min_value=10,
            max_value=orig_size[0],
            step=10,
            value=rect_width,
            key="rect_width",
        )

    with col2:
        fixed_height: int = st.number_input(
            "高度 (px)",
            min_value=10,
            max_value=orig_size[1],
            step=10,
            value=rect_height,
            key="rect_height",
        )

    # 計算縮放比例和畫布中的矩形尺寸（canvas 座標系）
    scale_x: float = float(canvas_size[0]) / float(orig_size[0])
    scale_y: float = float(canvas_size[1]) / float(orig_size[1])
    canvas_rect_width: int = int(round(fixed_width * scale_x))
    canvas_rect_height: int = int(round(fixed_height * scale_y))

    # 設定初始位置（置中）
    default_x: int = (canvas_size[0] - canvas_rect_width) // 2
    default_y: int = (canvas_size[1] - canvas_rect_height) // 2

    # 準備初始繪圖物件（fabric-like object description）
    initial_drawing = {
        "objects": [
            {
                "type": "rect",
                "originX": "left",
                "originY": "top",
                "left": default_x,
                "top": default_y,
                "width": canvas_rect_width,
                "height": canvas_rect_height,
                "fill": "rgba(255, 165, 0, 0.3)",
                "stroke": "#00f900",
                "strokeWidth": 2,
                "selectable": True,
                "evented": True,
                "lockScalingX": True,
                "lockScalingY": True,
                "lockRotation": True,
                "hasControls": False,
                "hasBorders": True,
            }
        ]
    }

    # 畫布元件
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",
        stroke_width=2,
        stroke_color="#00f900",
        background_color="#f0f0f0",
        background_image=resized_img,
        update_streamlit=True,
        width=canvas_size[0],
        height=canvas_size[1],
        drawing_mode="transform",  # 設定為變換模式，只能移動、選取現有物件
        initial_drawing=initial_drawing,
        display_toolbar=False,
        key=f"canvas_{canvas_size[0]}_{canvas_size[1]}_{fixed_width}_{fixed_height}",
    )

    region: Optional[XYWH] = None

    # 處理畫布結果
    json_data = getattr(canvas_result, "json_data", None)
    if json_data:
        objects = json_data.get("objects", [])
        if objects:
            obj = objects[0]
            # left/top may be float; convert safely
            new_x = int(round(float(obj.get("left", 0.0))))
            new_y = int(round(float(obj.get("top", 0.0))))

            # 轉換為原始圖片座標
            orig_scale_x = float(orig_size[0]) / float(canvas_size[0])
            orig_scale_y = float(orig_size[1]) / float(canvas_size[1])

            x = int(round(new_x * orig_scale_x))
            y = int(round(new_y * orig_scale_y))
            w = int(round(fixed_width))
            h = int(round(fixed_height))

            # 保證不超出原始邊界
            x = max(0, min(x, orig_size[0]))
            y = max(0, min(y, orig_size[1]))
            if x + w > orig_size[0]:
                w = max(0, orig_size[0] - x)
            if y + h > orig_size[1]:
                h = max(0, orig_size[1] - y)

            region = (x, y, w, h)

    st.info(get_text("interactive_selection_help") + f" (目前選擇區域: {region})")

    return region