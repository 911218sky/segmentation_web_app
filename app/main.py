import os
import io
import zipfile
import tempfile
from typing import List, Tuple, Dict, Any
import torch
from PIL import Image
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
import torchvision.transforms as T
import logging
import numpy as np
import torch.nn as nn
import pandas as pd

from utils import group_lengths
from file_processor import (
    process_images,
    create_zip_archive,
    create_excel_report,
    collect_measurement_data
)

# 設置日誌配置，方便調試和監控
logging.basicConfig(level=logging.INFO)
current_file = os.path.abspath(__file__)
file_name = os.path.basename(current_file)
logger = logging.getLogger(file_name)

# 設置 Streamlit 頁面配置
st.set_page_config(
    page_title="🩺 血管測量工具 v0.1",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 檢查是否有可用的 GPU，若沒有則使用 CPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

@st.cache_data
def get_model_path():
    # 定義模型存放的目錄和文件名
    MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
    MODEL_FILENAME = 'model_traced.pt'
    model_path = os.path.join(MODEL_DIR, MODEL_FILENAME)
    print(f"模型路徑: {model_path}")
    return model_path

@st.cache_data
def get_infer_transform():
    # 定義推理時的圖片轉換流程
    infer_transform: T.Compose = T.Compose([
        T.Resize((256, 256)),
        T.Grayscale(num_output_channels=1), 
        T.ToTensor(),
    ])
    return infer_transform


@st.cache_resource(show_spinner=False)
def load_model(model_path: str) -> nn.Module:
    """
    加載預訓練的 UNet3Plus 模型並緩存，以避免重複加載。

    參數:
        model_path (str): 模型文件的路徑。

    返回:
        UNet3Plus: 加載好的模型實例。
    """
    try:
        logger.info(f"正在從 {model_path} 加載模型")
        model = torch.jit.load(model_path).to(device)
        model.eval()  # 設置模型為評估模式
        logger.info("模型加載成功")
        return model
    except FileNotFoundError:
        logger.error(f"模型文件未找到: {model_path}")
        st.error("❌ 模型文件未找到，請確保模型文件放在 models/ 目錄下。")
        st.stop()  # 停止應用的執行
    except Exception as e:
        logger.exception("加載模型時發生錯誤")
        st.error(f"加載模型時發生錯誤: {e}")
        st.stop()


def initialize_session_state():
    """初始化或更新 session state"""
    # 如果是第一次初始化
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []
    if 'results' not in st.session_state:
        st.session_state.results = []
    if 'zip_buffer' not in st.session_state:
        st.session_state.zip_buffer = None
    if 'params' not in st.session_state:
        st.session_state.params = {
            'num_lines': 50,
            'line_width': 3,
            'min_length_mm': 1.0,
            'max_length_mm': 7.0,
            'depth_cm': 3.2,
            'line_length_weight': 1.0,
            'line_color': (0, 255, 0),
            'deviation_threshold': 0.0,
            'deviation_percent': 0.1
        }
    if 'form_submitted' not in st.session_state:
        st.session_state.form_submitted = False
    if 'compression_in_progress' not in st.session_state:
        st.session_state.compression_in_progress = False
    if 'selected_measurements' not in st.session_state:
        st.session_state.selected_measurements = {}

def main():
    """
    主函數，負責設置頁面內容和用戶交互。
    """
    initialize_session_state()

    # 設置頁面的標題和描述
    st.title("🩺 血管測量工具")
    st.write("🔍 此工具可以自動識別並測量圖片中的血管長度。")

    # 加載模型，如果模型文件不存在，已在 load_model 中處理錯誤
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

    # 如果有新的文件上傳，更新 session_state 並清除之前的結果
    if uploaded_files and uploaded_files != st.session_state.uploaded_files:
        st.session_state.uploaded_files = uploaded_files
        st.session_state.results = []
        st.session_state.zip_buffer = None

    # 步驟 2：調整參數
    st.markdown("## 步驟 2: 設定測量參數")
    with st.form("params_form"):
        # 使用雙欄佈局提升界面整潔度
        col1, col2 = st.columns(2)
        with col1:
            num_lines = st.slider(
                "垂直線的數量",
                min_value=1,
                max_value=250,
                value=st.session_state.params['num_lines'],
                step=1,
                key="num_lines_slider",
                help="設定圖片中垂直線的數量，用於血管的測量。"
            )
            line_width = st.slider(
                "線條寬度",
                min_value=1,
                max_value=10,
                value=st.session_state.params['line_width'],
                step=1,
                key="line_width_slider",
                help="設定血管線條的寬度。"
            )
            min_length_mm = st.slider(
                "最小線條長度 (mm)",
                min_value=0.1,
                max_value=10.0,
                value=st.session_state.params['min_length_mm'],
                step=0.1,
                key="min_length_mm_slider",
                help="設定血管線條的最小長度（毫米）。"
            )
            max_length_mm = st.slider(
                "最大線條長度 (mm)",
                min_value=4.0,
                max_value=20.0,
                value=st.session_state.params['max_length_mm'],
                step=0.1,
                key="max_length_mm_slider",
                help="設定血管線條的最大長度（毫米）。"
            )
        with col2:
            depth_cm = st.slider(
                "深度 (cm)",
                min_value=1.0,
                max_value=20.0,
                value=st.session_state.params['depth_cm'],
                step=0.1,
                key="depth_cm_slider",
                help="設定血管深度（厘米）。"
            )
            line_length_weight = st.slider(
                "調整線條長度權重",
                min_value=0.1,
                max_value=5.0,
                value=st.session_state.params['line_length_weight'],
                step=0.05,
                key="line_length_weight_slider",
                help="調整線條長度在測量中的權重。"
            )
            deviation_threshold = st.slider(
                "誤差閾值 (%)",
                min_value=0.0,
                max_value=1.0,
                value=st.session_state.params['deviation_threshold'],
                step=0.01,
                key="deviation_threshold_slider",
                help="設定可接受的誤差範圍百分比，超出此範圍的測量值將被過濾。(0 代表關閉過濾)"
            )
            deviation_percent = st.slider(
                "分組差距百分比 (%)",
                min_value=0.0,
                max_value=1.0,
                value=st.session_state.params['deviation_percent'],
                step=0.01,
                key="deviation_percent_slider",
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
                key="line_color_radio",
                help="選擇標記血管的線條顏色。"
            )[1]

        # 提交按鈕
        submitted = st.form_submit_button("開始測量")
        if submitted:
            st.session_state.form_submitted = True
            if not st.session_state.uploaded_files:
                st.warning("⚠️ 請上傳至少一張圖片。")
            else:
                # 更新所有參數
                st.session_state.params.update({
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
                
                # 重新處理圖片並獲取結果
                st.session_state.results = process_images(
                    model=model,
                    uploaded_files=st.session_state.uploaded_files,
                    params=st.session_state.params,
                    device=device,
                    transform=infer_transform
                )

    # 顯示處理結果
    if st.session_state.results:
        display_results(st.session_state.results,
                        st.session_state.uploaded_files)


def display_results(results: List[Tuple[Image.Image, Image.Image, List[float]]], uploaded_files: List[UploadedFile]):
    """
    顯示處理後的圖片結果並提供下載功能。

    參數:
        results (List[Tuple[Image.Image, Image.Image, List[float]]]): 每張圖片的處理結果。
        uploaded_files (List[UploadedFile]): 用戶上傳的圖片文件列表。
    """
    st.markdown("## 處理結果")

    if not results:
        st.warning("沒有可顯示的處理結果。")
        return

    # 創建下載按鈕區域
    zip_col, excel_col = st.columns(2)
    
    # ZIP下載按鈕
    zip_buffer = create_zip_archive(results, uploaded_files)
    if zip_buffer:
        with zip_col:
            st.download_button(
                "📥 下載所有處理後的圖片",
                data=zip_buffer,
                file_name="processed_images.zip",
                mime="application/zip",
                help="點擊此按鈕下載所有處理後的圖片壓縮包。"
            )

    # 使用網格布局顯示結果
    cols = st.columns(2)
    for idx, (processed_img, _, measurements) in enumerate(results):
        with cols[idx % 2]:
            filename = os.path.basename(uploaded_files[idx].name)
            st.markdown(f"### {filename}")
            if processed_img:
                st.image(processed_img, caption="處理後的圖像",
                         use_container_width=True)
                
                if len(measurements) > 0:
                    measurement_key = f"measurement_{filename}_{idx}"
                    
                    # 獲取分組後的測量值
                    if st.session_state.params['deviation_percent'] > 0:
                        mean_lengths = group_lengths(measurements, st.session_state.params['deviation_percent'])
                    else:
                        mean_lengths = [np.mean(measurements)]
                    
                    # 顯示選擇按鈕
                    selected_index = st.radio(
                        "選擇測量值",
                        options=range(len(mean_lengths)),
                        format_func=lambda x: f"{mean_lengths[x]:.2f} mm",
                        key=f"radio_{measurement_key}",
                        horizontal=True
                    )
                    
                    # 保存選中的測量值
                    selected_measurement = mean_lengths[selected_index]
                    st.session_state.selected_measurements[measurement_key] = selected_measurement
                    st.write(f"**選擇的測量值: {selected_measurement:.2f} mm**")
                else:
                    st.write("未測量到血管")
            else:
                st.error(f"處理失敗: {filename}")

    # Excel下載按鈕 - 移到最後，這樣會在每次選擇改變時更新
    measurement_data = collect_measurement_data(
        results,
        uploaded_files,
        st.session_state.selected_measurements
    )
    if measurement_data:
        excel_buffer = create_excel_report(measurement_data)
        if excel_buffer:
            with excel_col:
                st.download_button(
                    label="📊 下載測量結果 Excel",
                    data=excel_buffer,
                    file_name="measurement_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="下載所有圖片的測量結果為Excel檔案"
                )

if __name__ == '__main__':
    main()
