import streamlit as st
from typing import Tuple
from PIL import Image
from streamlit_drawable_canvas import st_canvas
from config.language import get_text
from config import CANVAS_CONFIG

def convert_original_xywh_to_resized(
    original_xywh: Tuple[int, int, int, int],
    scale: float,
    padding: Tuple[int, int]
) -> Tuple[int, int, int, int]:
    """
    根據縮放比例和填充邊距，將原圖xywh座標轉換到調整大小後圖片的座標系

    Args:
        original_xywh: 原始圖片上的 (x, y, w, h)
        scale: 縮放比例 (來自resize_image_uniform函數的回傳值)
        padding: (pad_left, pad_top) 填充邊距 (來自resize_image_uniform函數的回傳值)

    Returns:
        resized_xywh: 調整大小圖片上對應的 (x, y, w, h)
    """
    x, y, w, h = original_xywh
    pad_left, pad_top = padding

    # 先縮放座標和寬高
    resized_x = int(x * scale) + pad_left
    resized_y = int(y * scale) + pad_top
    resized_w = int(w * scale)
    resized_h = int(h * scale)

    return (resized_x, resized_y, resized_w, resized_h)

@st.cache_data(ttl=3600, max_entries=5)
def process_image_for_canvas(image_file):
    """
    讀取並依畫布寬高上限對圖片進行高品質重採樣。
    回傳: resized_img, original_size(tuple), canvas_size(tuple)
    """
    img = Image.open(image_file)

    max_canvas_w = CANVAS_CONFIG['max_canvas_w']
    max_canvas_h = CANVAS_CONFIG['max_canvas_h']

    canvas_w = max_canvas_w
    canvas_h = int(canvas_w * img.height / img.width)

    # 若高度超過上限則改依高度縮放
    if canvas_h > max_canvas_h:
        canvas_h = max_canvas_h
        canvas_w = int(canvas_h * img.width / img.height)

    resized_img = img.resize((canvas_w, canvas_h), Image.Resampling.LANCZOS)

    return resized_img, (img.width, img.height), (canvas_w, canvas_h)
    
def render_canvas_section(uploaded_file, rect_width = CANVAS_CONFIG['rect_width'], rect_height = CANVAS_CONFIG['rect_height']):
    """渲染可繪製畫布區域 - 單張圖片，固定矩形尺寸，只能移動位置"""
    if not uploaded_file:
        return None
    
    st.subheader(get_text('interactive_selection'))

    # 處理圖片
    resized_img, orig_size, canvas_size = process_image_for_canvas(uploaded_file)
    
    st.markdown("**調整選取區域尺寸**")
    col1, col2 = st.columns(2)
    with col1:
        fixed_width = st.number_input(
            "寬度 (px)", 
            min_value=10, 
            max_value=orig_size[0], 
            step=10,
            value=rect_width,
            key="rect_width"
        )
    
    with col2:
        fixed_height = st.number_input(
            "高度 (px)", 
            min_value=10, 
            max_value=orig_size[1], 
            step=10,
            value=rect_height,
            key="rect_height"
        )
        
    # 計算縮放比例和畫布尺寸
    scale_x = canvas_size[0] / orig_size[0]
    scale_y = canvas_size[1] / orig_size[1]
    canvas_rect_width = int(fixed_width * scale_x)
    canvas_rect_height = int(fixed_height * scale_y)
    
    # 設定初始位置（只在首次或重置時）
    default_x = (canvas_size[0] - canvas_rect_width) // 2
    default_y = (canvas_size[1] - canvas_rect_height) // 2
    
    # 準備初始繪圖物件
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
                "selectable": True, # 可以被選取/點擊
                "evented": True, # 可以觸發事件（如滑鼠事件）
                "lockScalingX": True, # 鎖定水平縮放 - 防止水平縮放矩形
                "lockScalingY": True, # 鎖定垂直縮放 - 防止垂直縮放矩形 
                "lockRotation": True, # 鎖定旋轉 - 防止旋轉矩形
                "hasControls": False, # 隱藏控制點 - 不顯示四角的縮放控制點
                "hasBorders": True,  # 顯示選取邊框 - 選取時會顯示邊框
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
        drawing_mode="transform", # 設定為變換模式，只能移動、選取現有物件，不能繪製新物件
        initial_drawing=initial_drawing, # 預載初始繪圖內容
        display_toolbar=False, # 隱藏工具列
        key=f"canvas_{fixed_width}_{fixed_height}",
    )
    
    # 處理畫布結果
    region = None
    
    if canvas_result.json_data is not None:
        objects = canvas_result.json_data.get("objects", [])
        if objects:
            obj = objects[0]
            new_x = int(obj["left"])
            new_y = int(obj["top"])
            
            # 轉換為原始圖片座標
            orig_scale_x = orig_size[0] / canvas_size[0]
            orig_scale_y = orig_size[1] / canvas_size[1]
            
            x = int(new_x * orig_scale_x)
            y = int(new_y * orig_scale_y)
            w = fixed_width
            h = fixed_height
            
            region = (x, y, w, h)
    
    st.info(get_text('interactive_selection_help') + f" (目前選擇區域: {region})")
    
    return region