from typing import List, Tuple, Dict, Any
import torch
import streamlit as st
import torchvision.transforms as T
import logging
import numpy as np
import torch.nn as nn
import os
from dataclasses import asdict

from utils import group_lengths
from file_processor import (
    process_images,
    create_zip_archive,
    create_excel_report,
    collect_measurement_data
)
from state_manager import initialize_state, update_streamlit_state, AppState

# 設置日誌配置
logging.basicConfig(level=logging.INFO)
current_file = os.path.abspath(__file__)
file_name = os.path.basename(current_file)
logger = logging.getLogger(file_name)

# 設置 Streamlit 頁面配置
st.set_page_config(
    page_title="🩺 血管測量工具 v0.2",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 檢查是否有可用的 GPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

@st.cache_data
def get_model_path() -> str:
    MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
    MODEL_FILENAME = 'model_traced.pt'
    model_path = os.path.join(MODEL_DIR, MODEL_FILENAME)
    print(f"模型路徑: {model_path}")
    return model_path

@st.cache_data
def get_infer_transform() -> T.Compose:
    return T.Compose([
        T.Resize((256, 256)),
        T.Grayscale(num_output_channels=1), 
        T.ToTensor(),
    ])

@st.cache_resource(show_spinner=False)
def load_model(model_path: str) -> nn.Module:
    try:
        logger.info(f"正在從 {model_path} 加載模型")
        model = torch.jit.load(model_path).to(device)
        model.eval()
        logger.info("模型加載成功")
        return model
    except FileNotFoundError:
        logger.error(f"模型文件未找到: {model_path}")
        st.error("❌ 模型文件未找到，請確保模型文件放在 models/ 目錄下。")
        st.stop()
    except Exception as e:
        logger.exception("加載模型時發生錯誤")
        st.error(f"加載模型時發生錯誤: {e}")
        st.stop()

def on_radio_change(state: AppState, key: str) -> None:
    """當選擇改變時的回調函數"""
    # 只更新改變的測量值，避免重置所有狀態
    if key.startswith("radio_measurement_"):
        measurement_key = key[6:]  # Remove "radio_" prefix
        mean_lengths = state.mean_lengths_cache.get(measurement_key, [])
        if key in st.session_state:
            value = st.session_state[key]
            if mean_lengths and value < len(mean_lengths):
                state.selected_measurements[measurement_key] = mean_lengths[value]
                # 只在測量值改變時更新狀態，但不重置確認狀態
                update_streamlit_state(st, state)

def confirm_results(state: AppState) -> None:
    """確認結果並生成報告"""
    state.results_confirmed = True
    
    # 生成報告
    state.measurement_data = collect_measurement_data(
        state.results,
        state.uploaded_files,
        state.selected_measurements
    )
    if state.measurement_data:
        state.excel_buffer = create_excel_report(state.measurement_data)
    
    # 生成 ZIP 文件
    state.zip_buffer = create_zip_archive(state.results, state.uploaded_files)
    
    update_streamlit_state(st, state)

@st.cache_data
def create_download_buttons(state: AppState) -> List[Tuple[str, Dict[str, Any]]]:
    """創建下載按鈕"""
    buttons = []
    
    # ZIP下載按鈕
    if state.results_confirmed and state.zip_buffer:
        buttons.append(("zip", {
            "label": "📥 下載所有處理後的圖片",
            "data": state.zip_buffer,
            "file_name": "processed_images.zip",
            "mime": "application/zip",
            "help": "點擊此按鈕下載所有處理後的圖片壓縮包。",
            "use_container_width": True
        }))
    else:
        buttons.append(("disabled_zip", {
            "label": "📥 下載所有處理後的圖片",
            "disabled": True,
            "help": "請先確認測量結果才能下載",
            "use_container_width": True
        }))
    
    # Excel下載按鈕
    if state.excel_buffer and state.results_confirmed:
        buttons.append(("excel", {
            "label": "📊 下載測量結果 Excel",
            "data": state.excel_buffer,
            "file_name": "measurement_results.xlsx",
            "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "help": "下載所有圖片的測量結果為Excel檔案",
            "use_container_width": True
        }))
    else:
        buttons.append(("disabled_excel", {
            "label": "📊 下載測量結果 Excel",
            "disabled": True,
            "help": "請先確認測量結果才能下載",
            "use_container_width": True
        }))
    
    return buttons

def display_results(state: AppState) -> None:
    """顯示處理後的圖片結果並提供下載功能"""
    st.markdown("## 處理結果")

    if not state.results:
        st.warning("沒有可顯示的處理結果。")
        return

    # 確認按鈕和下載區域
    col1, col2, col3 = st.columns([1, 1, 1])
    
    # 確認按鈕
    with col1:
        if not state.results_confirmed:
            if st.button(
                "確認測量結果",
                type="primary",
                key="confirm_button",
                use_container_width=True
            ):
                with st.spinner("正在生成報告..."):
                    confirm_results(state)
                st.rerun()
        else:
            st.button(
                "✓ 已確認測量結果",
                type="secondary",
                disabled=True,
                key="confirm_button",
                use_container_width=True
            )
    
    # 創建下載按鈕
    buttons = create_download_buttons(state)
    
    # 顯示下載按鈕
    for (button_type, button_args) in buttons:
        if button_type == "zip":
            with col2:
                st.download_button(**button_args)
        elif button_type == "disabled_zip":
            with col2:
                st.button(**button_args)
        elif button_type == "excel":
            with col3:
                st.download_button(**button_args)
        elif button_type == "disabled_excel":
            with col3:
                st.button(**button_args)

    st.markdown("---")

    # 使用網格布局顯示結果
    cols = st.columns(2)
    for idx, (processed_img, _, measurements) in enumerate(state.results):
        with cols[idx % 2]:
            filename = os.path.basename(state.uploaded_files[idx].name)
            st.markdown(f"### {filename}")
            if processed_img:
                # 使用 st.container 來減少重新渲染
                with st.container():
                    st.image(processed_img, caption="處理後的圖像",
                            use_container_width=True)
                    
                    if len(measurements) > 0:
                        measurement_key = f"measurement_{filename}_{idx}"
                        radio_key = f"radio_{measurement_key}"
                        
                        # 獲取分組後的測量值並緩存
                        mean_lengths = state.mean_lengths_cache.get(measurement_key)
                        if mean_lengths is None:
                            if state.params.deviation_percent > 0:
                                mean_lengths = group_lengths(measurements, state.params.deviation_percent)
                            else:
                                mean_lengths = [np.mean(measurements)]
                            state.mean_lengths_cache[measurement_key] = mean_lengths
                        
                        # 初始化選中的測量值
                        if measurement_key not in state.selected_measurements:
                            state.selected_measurements[measurement_key] = mean_lengths[0]
                        
                        # 找到當前選中值的索引
                        current_value = state.selected_measurements[measurement_key]
                        current_index = 0
                        for i, value in enumerate(mean_lengths):
                            if abs(value - current_value) < 0.001:
                                current_index = i
                                break
                        
                        # 使用 session state 來管理 radio button 的狀態
                        if radio_key not in st.session_state:
                            st.session_state[radio_key] = current_index
                        
                        # 顯示選擇按鈕，不設置 index 參數
                        selected_index = st.radio(
                            "選擇測量值",
                            options=range(len(mean_lengths)),
                            format_func=lambda x: f"{mean_lengths[x]:.2f} mm",
                            key=radio_key,
                            horizontal=True,
                            on_change=lambda: on_radio_change(state, radio_key),
                            label_visibility="collapsed"  # 隱藏標籤以減少空間
                        )
                        
                        # 更新選中的測量值
                        selected_measurement = mean_lengths[selected_index]
                        state.selected_measurements[measurement_key] = selected_measurement
                        st.write(f"**選擇的測量值: {selected_measurement:.2f} mm**")
                    else:
                        st.write("未測量到血管")
            else:
                st.error(f"處理失敗: {filename}")

def main():
    """主函數，負責設置頁面內容和用戶交互"""
    state = initialize_state(st)

    # 設置頁面的標題和描述
    st.title("🩺 血管測量工具")
    st.write("🔍 此工具可以自動識別並測量圖片中的血管長度。")

    # 加載模型
    model = load_model(get_model_path())
    infer_transform = get_infer_transform()

    # 步驟 1：上傳圖片
    st.markdown("## 步驟 1: 上傳圖片")
    uploaded_files = st.file_uploader(
        "上傳多張圖片進行測量（支援格式：JPG, PNG）",
        accept_multiple_files=True,
        type=["jpg", "jpeg", "png"],
        key="file_uploader"
    )

    # 如果有新的文件上傳，更新狀態
    if uploaded_files and uploaded_files != state.uploaded_files:
        state.uploaded_files = uploaded_files
        state.reset_file_state()
        update_streamlit_state(st, state)

    # 步驟 2：調整參數
    st.markdown("## 步驟 2: 設定測量參數")
    with st.form("params_form"):
        col1, col2 = st.columns(2)
        with col1:
            num_lines = st.slider(
                "垂直線的數量",
                min_value=1,
                max_value=250,
                value=state.params.num_lines,
                step=1,
                help="設定圖片中垂直線的數量，用於血管的測量。"
            )
            line_width = st.slider(
                "線條寬度",
                min_value=1,
                max_value=10,
                value=state.params.line_width,
                step=1,
                help="設定血管線條的寬度。"
            )
            min_length_mm = st.slider(
                "最小線條長度 (mm)",
                min_value=0.1,
                max_value=10.0,
                value=state.params.min_length_mm,
                step=0.1,
                help="設定血管線條的最小長度（毫米）。"
            )
            max_length_mm = st.slider(
                "最大線條長度 (mm)",
                min_value=4.0,
                max_value=20.0,
                value=state.params.max_length_mm,
                step=0.1,
                help="設定血管線條的最大長度（毫米）。"
            )
        with col2:
            depth_cm = st.slider(
                "深度 (cm)",
                min_value=1.0,
                max_value=20.0,
                value=state.params.depth_cm,
                step=0.1,
                help="設定血管深度（厘米）。"
            )
            line_length_weight = st.slider(
                "調整線條長度權重",
                min_value=0.1,
                max_value=5.0,
                value=state.params.line_length_weight,
                step=0.05,
                help="調整線條長度在測量中的權重。"
            )
            deviation_threshold = st.slider(
                "誤差閾值 (%)",
                min_value=0.0,
                max_value=1.0,
                value=state.params.deviation_threshold,
                step=0.01,
                help="設定可接受的誤差範圍百分比，超出此範圍的測量值將被過濾。(0 代表關閉過濾)"
            )
            deviation_percent = st.slider(
                "分組差距百分比 (%)",
                min_value=0.0,
                max_value=1.0,
                value=state.params.deviation_percent,
                step=0.01,
                help="設定分組差距百分比，用於將相似長度的線條分組。(0 代表關閉分組)"
            )
            line_color = st.radio(
                "線條顏色",
                options=[
                    ('綠色', (0, 255, 0)),
                    ('紅色', (255, 0, 0)),
                    ('藍色', (0, 0, 255)),
                    ('黃色', (255, 255, 0)),
                    ('白色', (255, 255, 255)),
                ],
                index=0,
                format_func=lambda x: x[0],
                help="選擇標記血管的線條顏色。"
            )[1]

        # 提交按鈕
        submitted = st.form_submit_button(
            "開始測量" if not state.processing else "處理中...",
            disabled=state.processing
        )
        
        if submitted:
            state.form_submitted = True
            if not state.uploaded_files:
                st.warning("⚠️ 請上傳至少一張圖片。")
            else:
                # 更新參數
                state.update_params({
                    'num_lines': num_lines,
                    'line_width': line_width,
                    'min_length_mm': min_length_mm,
                    'max_length_mm': max_length_mm,
                    'depth_cm': depth_cm,
                    'line_length_weight': line_length_weight,
                    'deviation_threshold': deviation_threshold,
                    'deviation_percent': deviation_percent,
                    'line_color': line_color
                })
                
                # 設置處理狀態
                state.processing = True
                update_streamlit_state(st, state)
                
                # 顯示進度條
                with st.spinner('正在處理圖片...'):
                    try:
                        state.results = process_images(
                            model=model,
                            uploaded_files=state.uploaded_files,
                            params=asdict(state.params),
                            device=device,
                            transform=infer_transform
                        )
                    finally:
                        state.processing = False
                        update_streamlit_state(st, state)

    # 顯示處理結果
    if state.results:
        display_results(state)

if __name__ == '__main__':
    main()
