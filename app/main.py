import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CONFIG

from typing import List, Tuple, Dict, Any
import torch
import streamlit as st
import torchvision.transforms as T
import logging
import numpy as np
import torch.nn as nn
import time

from utils import group_lengths
from file_processor import (
    process_images,
    create_zip_archive,
    create_excel_report,
    collect_measurement_data
)
from state_manager import AppState
from i18n.language_manager import lang_manager

# 設置日誌配置
logging.basicConfig(level=logging.INFO)
current_file = os.path.abspath(__file__)
file_name = os.path.basename(current_file)
logger = logging.getLogger(file_name)

# 檢查是否有可用的 GPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 設置 Streamlit 頁面配置 - 必須是第一個 Streamlit 命令
st.set_page_config(
    page_title=lang_manager.get_text("page_title"),
    layout="wide",
    initial_sidebar_state="expanded",
)

@st.cache_data
def get_model_path() -> str:
    MODEL_DIR = CONFIG.model.model_dir
    MODEL_FILENAME = CONFIG.model.filename
    model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), MODEL_DIR, MODEL_FILENAME)
    logger.info(f"模型路徑: {model_path}")
    return model_path

@st.cache_data
def get_infer_transform() -> T.Compose:
    return T.Compose([
        T.Resize(CONFIG.image.size),
        T.Grayscale(num_output_channels=CONFIG.image.channels), 
        T.ToTensor(),
    ])

@st.cache_resource(show_spinner=False)
def load_model(model_path: str) -> nn.Module:
    try:
        logger.info(f"正在從 {model_path} 加載模型")
        if model_path.endswith(".ts"):
            logger.info("TorchScript model detected use torch_tensorrt.")
            import torch_tensorrt
            assert device.type == "cuda", "TorchScript models require a CUDA device."
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
            if mean_lengths and 0 <= value < len(mean_lengths):
                state.selected_measurements[measurement_key] = mean_lengths[value]
            else:
                logger.warning(f"Invalid index {value} for mean_lengths with key {measurement_key}")
                st.warning("選擇的測量值無效，請重新選擇。")
    
    state.results_confirmed = False
    state.excel_buffer = None
    state.zip_buffer = None

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
    start_time = time.time()
    state.zip_buffer = create_zip_archive(state.results, state.uploaded_files)
    end_time = time.time()
    logger.info(f"生成 ZIP 文件時間: {end_time - start_time:.2f} 秒")

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
            "label": lang_manager.get_text("download_excel"),
            "data": state.excel_buffer,
            "file_name": "measurement_results.xlsx",
            "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "help": lang_manager.get_text("download_excel_help"),
            "use_container_width": True
        }))
    else:
        buttons.append(("disabled_excel", {
            "label": lang_manager.get_text("download_excel"),
            "disabled": True,
            "help": lang_manager.get_text("download_disabled_help"),
            "use_container_width": True
        }))
    
    return buttons

def display_results(state: AppState) -> None:
    """顯示處理後的圖片結果並提供下載功能"""
    st.markdown(lang_manager.get_text("results_title"))

    if not state.results:
        st.warning(lang_manager.get_text("no_results"))
        return
    
    # 確認按鈕和下載區域
    col1, col2, col3 = st.columns([1, 1, 1])
    # 確認按鈕
    with col1:
        if not state.results_confirmed:
            if st.button(
                lang_manager.get_text("confirm_results"),
                type="primary",
                key="confirm_button",
                use_container_width=True,
            ):
                with st.spinner(lang_manager.get_text("generating_report")):
                    confirm_results(state)
                    st.rerun()
        else:
            st.button(
                lang_manager.get_text("results_confirmed"),
                type="secondary",
                disabled=True,
                key="confirm_button",
                use_container_width=True
            )
    
    # 下載按鈕
    with col2:
        if state.results_confirmed and state.zip_buffer:
            st.download_button(
                label=lang_manager.get_text("download_images"),
                data=state.zip_buffer,
                file_name="processed_images.zip",
                mime="application/zip",
                help=lang_manager.get_text("download_images_help"),
                use_container_width=True
            )
        else:
            st.button(
                label=lang_manager.get_text("download_images"),
                disabled=True,
                help=lang_manager.get_text("download_disabled_help"),
                use_container_width=True
            )
    
    with col3:
        if state.excel_buffer and state.results_confirmed:
            st.download_button(
                label=lang_manager.get_text("download_excel"),
                data=state.excel_buffer,
                file_name="measurement_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help=lang_manager.get_text("download_excel_help"),
                use_container_width=True
            )
        else:
            st.button(
                label=lang_manager.get_text("download_excel"),
                disabled=True,
                help=lang_manager.get_text("download_disabled_help"),
                use_container_width=True
            )

    st.markdown("---")

    # 使用網格布局顯示結果
    cols = st.columns(2)
    for idx, (processed_img, _, measurements) in enumerate(state.results):
        with cols[idx % 2]:
            filename = os.path.basename(state.uploaded_files[idx].name)
            st.markdown(f"### {filename}")
            if processed_img:
                with st.container():
                    st.image(processed_img, caption=lang_manager.get_text("processed_image"),
                            use_container_width=True)
                    
                    if len(measurements) > 0:
                        measurement_key = f"measurement_{filename}_{idx}"
                        radio_key = f"radio_{measurement_key}"
                        
                        mean_lengths = state.mean_lengths_cache.get(measurement_key)
                        if mean_lengths is None:
                            if state.params.deviation_percent > 0:
                                mean_lengths = group_lengths(measurements, state.params.deviation_percent)
                            else:
                                mean_lengths = [float(np.mean(measurements))]
                            
                            if not mean_lengths:  # 如果分組後沒有有效的長度
                                mean_lengths = [0.0]
                            state.mean_lengths_cache[measurement_key] = mean_lengths
                        
                        if mean_lengths:  # 確保有有效的長度值
                            selected_index = st.radio(
                                lang_manager.get_text("select_measurement"),
                                options=range(len(mean_lengths)),
                                format_func=lambda x: f"{mean_lengths[x]:.2f} mm",
                                key=radio_key,
                                horizontal=True,
                                on_change=lambda: on_radio_change(state, radio_key),
                                label_visibility="collapsed",
                            )
                            
                            selected_measurement = mean_lengths[selected_index]
                            state.selected_measurements[measurement_key] = selected_measurement
                            st.write(lang_manager.get_text("selected_measurement").format(selected_measurement))
                        else:
                            st.write(lang_manager.get_text("no_valid_measurements"))
                    else:
                        st.write(lang_manager.get_text("no_vessel_detected"))
            else:
                st.error(lang_manager.get_text("processing_failed").format(filename))

def main():
    """主函數，負責設置頁面內容和用戶交互"""
    state = AppState(st)

    # 添加語言選擇器到側邊欄
    with st.sidebar:
        lang_manager.get_language_selector()

    # 設置頁面的標題和描述
    st.title(lang_manager.get_text("app_title"))
    st.write(lang_manager.get_text("app_description"))

    # 加載模型
    model = load_model(get_model_path())
    infer_transform = get_infer_transform()

    # 步驟 1：上傳圖片
    st.markdown(lang_manager.get_text("step1_title"))
    st.session_state["file_uploader_key"] = 0 if "file_uploader_key" not in st.session_state else st.session_state["file_uploader_key"]
    
    if st.button(
        lang_manager.get_text("clear_results"), 
        type="primary",
        key="clear_button",
        help=lang_manager.get_text("clear_results_help"),
        use_container_width=True
    ):
        st.session_state["file_uploader_key"] += 1
        state.reset_file_state()
        
    uploaded_files = st.file_uploader(
        lang_manager.get_text("upload_images"),
        accept_multiple_files=True,
        type=["jpg", "jpeg", "png"],
        key=f"file_uploader_{st.session_state['file_uploader_key']}",
    )

    # 如果有新的文件上傳，更新狀態
    if uploaded_files and uploaded_files != state.uploaded_files:
        state.uploaded_files = uploaded_files
        state.reset_file_state()

    # 步驟 2：調整參數
    st.markdown(lang_manager.get_text("step2_title"))

    # 參數設置表單
    with st.form("params_form"):
        st.markdown(lang_manager.get_text("basic_params"))
        col1, col2 = st.columns(2)
        with col1:
            num_lines = st.slider(
                lang_manager.get_text("num_lines"),
                min_value=1,
                max_value=250,
                value=int(state.params.num_lines),
                step=1,
                help=lang_manager.get_text("num_lines_help"),
                key="num_lines"
            )
            line_width = st.slider(
                lang_manager.get_text("line_width"),
                min_value=1,
                max_value=10,
                value=int(state.params.line_width),
                step=1,
                help=lang_manager.get_text("line_width_help"),
                key="line_width"
            )
            min_length_mm = st.slider(
                lang_manager.get_text("min_length"),
                min_value=0.1,
                max_value=10.0,
                value=float(state.params.min_length_mm),
                step=0.1,
                help=lang_manager.get_text("min_length_help"),
                key="min_length_mm"
            )
            max_length_mm = st.slider(
                lang_manager.get_text("max_length"),
                min_value=4.0,
                max_value=20.0,
                value=float(state.params.max_length_mm),
                step=0.1,
                help=lang_manager.get_text("max_length_help"),
                key="max_length_mm"
            )
        with col2:
            depth_cm = st.slider(
                lang_manager.get_text("depth"),
                min_value=1.0,
                max_value=20.0,
                value=float(state.params.depth_cm),
                step=0.1,
                help=lang_manager.get_text("depth_help"),
                key="depth_cm"
            )
            line_length_weight = st.slider(
                lang_manager.get_text("line_length_weight"),
                min_value=0.1,
                max_value=5.0,
                value=float(state.params.line_length_weight),
                step=0.05,
                help=lang_manager.get_text("line_length_weight_help"),
                key="line_length_weight"
            )
            deviation_threshold = st.slider(
                lang_manager.get_text("deviation_threshold"),
                min_value=0.0,
                max_value=1.0,
                value=float(state.params.deviation_threshold),
                step=0.01,
                help=lang_manager.get_text("deviation_threshold_help"),
                key="deviation_threshold"
            )
            deviation_percent = st.slider(
                lang_manager.get_text("deviation_percent"),
                min_value=0.0,
                max_value=1.0,
                value=float(state.params.deviation_percent),
                step=0.01,
                help=lang_manager.get_text("deviation_percent_help"),
                key="deviation_percent"
            )

        st.markdown(lang_manager.get_text("display_settings"))
        line_color = st.radio(
            lang_manager.get_text("line_color"),
            options=[
                (lang_manager.get_text("color_green"), (0, 255, 0)),
                (lang_manager.get_text("color_red"), (255, 0, 0)),
                (lang_manager.get_text("color_blue"), (0, 0, 255)),
                (lang_manager.get_text("color_yellow"), (255, 255, 0)),
                (lang_manager.get_text("color_white"), (255, 255, 255)),
            ],
            index=0,
            format_func=lambda x: x[0],
            help=lang_manager.get_text("line_color_help"),
            key="line_color",
            horizontal=True
        )[1]

        # 參數預設值管理
        with st.expander("⚙️ 參數預設值管理", expanded=True):
            preset_name = st.text_input(
                lang_manager.get_text("preset_name"),
                key="preset_name",
                placeholder=lang_manager.get_text("preset_name_placeholder"),
                label_visibility="visible"
            )
            
            # 保存參數按鈕
            save_params = st.form_submit_button(
                lang_manager.get_text("save_params"),
                type="secondary",
                use_container_width=True
            )

            if save_params:
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
                if preset_name:
                    state.save_params(preset_name)
                else:
                    st.warning(lang_manager.get_text("preset_name_warning"))

            # 顯示已保存的預設值
            saved_presets = state.get_saved_presets()
            if saved_presets:
                st.markdown("### 已保存的預設值")
                for name in saved_presets.keys():
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.write(f"**{name}**")
                    with col2:
                        if st.form_submit_button(f"📥 載入 {name}"):
                            state.load_params(name)
                            st.rerun()
                    with col3:
                        if st.form_submit_button(f"🗑️ 刪除 {name}"):
                            state.delete_preset(name)

        # 提交按鈕
        st.markdown(lang_manager.get_text("start_processing"))
        submitted = st.form_submit_button(
            lang_manager.get_text("start_processing") if not state.processing else lang_manager.get_text("processing"),
            disabled=state.processing,
            type="primary",
            use_container_width=True
        )
        
        if submitted:
            state.form_submitted = True
            if not state.uploaded_files:
                st.warning(lang_manager.get_text("upload_warning"))
            else:
                # 設置處理狀態
                state.processing = True
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
                # 顯示進度條
                with st.spinner(lang_manager.get_text("processing_spinner")):
                    try:
                        state.results = process_images(
                            model=model,
                            uploaded_files=state.uploaded_files,
                            params=state.params,
                            device=device,
                            transform=infer_transform,
                        )
                    finally:
                        state.processing = False

    # 顯示處理結果
    if state.results:
        display_results(state)

if __name__ == '__main__':
    main()
