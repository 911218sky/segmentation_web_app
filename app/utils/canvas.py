import streamlit as st
from typing import Tuple
from PIL import Image
from streamlit_drawable_canvas import st_canvas
from config.language import get_text

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

def render_canvas_section(uploaded_file):
    """渲染可繪製畫布區域 - 單張圖片，只能畫一個矩形區域 (x, y, w, h)"""
    if not uploaded_file:
        return None
    
    # 初始化 canvas key counter
    if 'canvas_key_counter' not in st.session_state:
        st.session_state.canvas_key_counter = 0
    
    # 需要在 language config 中添加這個 key
    st.subheader(get_text('interactive_selection'))
    
    # 直接使用上傳的單張圖片
    selected_image = Image.open(uploaded_file)
    
    # 調整圖片大小以適應畫布
    canvas_width = 800
    canvas_height = int(canvas_width * selected_image.height / selected_image.width)
    
    if canvas_height > 600:
        canvas_height = 600
        canvas_width = int(canvas_height * selected_image.width / selected_image.height)
    
    resized_image = selected_image.resize((canvas_width, canvas_height))
    
    # 簡化控制選項
    st.info(get_text('interactive_selection_help'))
    
    # 創建可繪製畫布 - 使用動態 key 來支援清除功能
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",
        stroke_width=2,
        stroke_color="#00f900",
        background_color="#eee",
        background_image=resized_image,
        update_streamlit=True,
        width=canvas_width,
        height=canvas_height,
        drawing_mode="rect",
        key=f"canvas_{st.session_state.canvas_key_counter}",
        display_toolbar=False,
    )
    
    # 處理繪製結果 - 只處理矩形，且只取第一個
    region = None
    if canvas_result.json_data is not None:
        objects = canvas_result.json_data.get("objects", [])
        
        # 只取第一個矩形物件
        rect_objects = [obj for obj in objects if obj["type"] == "rect"]
        
        if rect_objects:
            # 計算縮放比例
            scale_x = selected_image.width / canvas_width
            scale_y = selected_image.height / canvas_height
            
            # 只處理第一個矩形
            obj = rect_objects[0]
            x = int(obj["left"] * scale_x)
            y = int(obj["top"] * scale_y)
            w = int(obj["width"] * scale_x)
            h = int(obj["height"] * scale_y)
            
            region = (x, y, w, h)
            
            # 如果有多個矩形，提醒用戶只會使用第一個
            if len(rect_objects) > 1:
                st.warning(get_text('multiple_regions_warning'))
    
    # 顯示已選擇的區域資訊
    if region:
        # 清除區域按鈕
        if st.button(get_text('clear_region'), key="clear_region"):
            st.session_state.canvas_key_counter += 1
            st.rerun()
        # 顯示成功訊息
        st.success(get_text('region_selected'))
    else:
        st.info(get_text('no_region_selected'))
    
    return region
