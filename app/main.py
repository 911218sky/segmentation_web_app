import math
import streamlit as st
import sys
import zipfile
from io import BytesIO
import numpy as np
from PIL import Image
# from streamlit_chunked_upload import uploader as chunked_uploader
from utils.canvas import render_canvas_section

sys.path.append("../yolov12")

from config import (
    BATCH_SIZE,
    DEFAULT_CONFIGS,
    AVAILABLE_MODELS,
    DEFAULT_MODEL,
    
    # config
    FileStorageManager,
    
    # model
    get_model_path,
    switch_model,
    
    # language
    get_text
)

from utils.excel import generate_csv_from_results, generate_excel_from_results
from utils.process import process_batch_images

file_storage_manager = FileStorageManager()

def initialize_language():
    """初始化語言設定"""
    if 'language' not in st.session_state:
        st.session_state.language = 'zh' 

# 頁面配置
def setup_page_config():
    st.set_page_config(
        page_title=get_text('page_title'),
        page_icon=get_text('page_icon'),
        layout="wide",
    )

# 初始化 session state
def initialize_app_state():
    if 'predictor' not in st.session_state:
        st.session_state.predictor = None
    if 'processed_results' not in st.session_state:
        st.session_state.processed_results = []
    if 'file_manager_initialized' not in st.session_state:
        file_storage_manager.initialize_session_state()
        st.session_state.file_manager_initialized = True

def render_language_selector():
    """渲染語言選擇器"""
    st.header(get_text('language_selector'))
    language_options = {
        '中文': 'zh',
        'English': 'en'
    }
    
    current_lang_key = [k for k, v in language_options.items() 
                       if v == st.session_state.language][0]
    
    selected_language = st.selectbox(
        get_text('language_selector'),
        options=list(language_options.keys()),
        index=list(language_options.keys()).index(current_lang_key),
        key='language_selector_widget'
    )
    
    # 如果語言改變，更新 session state 並重新運行
    if language_options[selected_language] != st.session_state.language:
        st.session_state.language = language_options[selected_language]
        st.rerun()

def render_model_section():
    """渲染模型選擇區域"""
    st.subheader(get_text('model_selection'))
    
    current_config = file_storage_manager.get_current_config()
    current_model = current_config['selected_model']
    
    selected_model = st.selectbox(
        get_text('select_model'),
        options=list(AVAILABLE_MODELS.keys()),
        index=list(AVAILABLE_MODELS.keys()).index(st.session_state.get('selected_model', DEFAULT_MODEL)),
        key='model_selector',
        help=get_text('select_model_help')
    )
    
    # 顯示當前模型資訊
    if current_config:
        st.info(f"{get_text('current_model')}: {current_model}")
    
    # 模型切換按鈕
    if st.button(get_text('switch_model'), type="secondary"):
        switch_model(selected_model)

    # 自動載入預設模型（如果還沒載入）
    if st.session_state.predictor is None:
        current_model = current_config['selected_model']
        switch_model(current_model)

    # 模型狀態顯示
    st.subheader(get_text('model_status'))
    if st.session_state.predictor is not None:
        st.success(f"{get_text('model_loaded')}: {current_model}")
        
        model_path = get_model_path(current_model)
        st.caption(f"📁 {get_text('model_file')}: {model_path.name}")
    else:
        st.error(get_text('model_failed'))
        available_models_info = []
        for name, filename in AVAILABLE_MODELS.items():
            model_path = get_model_path(name)
            status = "✅" if model_path.exists() else "❌"
            available_models_info.append(f"{status} {name}: {filename}")
        
        st.info(f"{get_text('available_models')}:\n" + "\n".join(available_models_info))

def render_settings_section():
    """渲染設定管理區域"""
    st.subheader(get_text('settings_management'))
    
    # 載入所有可用設定
    available_configs = file_storage_manager.load_saved_configs()
    config_names = list(available_configs.keys())
    current_config = file_storage_manager.get_current_config()
    current_model = current_config['selected_model']
    
    selected_config = st.selectbox(
        get_text('select_config'),
        options=config_names,
        help=get_text('select_config_help')
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button(get_text('apply_config'), type="primary"):
            if selected_config in available_configs:
                file_storage_manager.apply_config(available_configs[selected_config])
                # 如果設定包含不同的模型，也要切換模型
                config_model = available_configs[selected_config].get('selected_model')
                if config_model and config_model != current_model:
                    switch_model(config_model)
                st.success(f"✅ {get_text('config_applied')}「{selected_config}」設定")
                st.rerun()
    
    with col2:
        can_delete = selected_config not in DEFAULT_CONFIGS
        if st.button(get_text('delete_config'), disabled=not can_delete):
            if can_delete:
                if file_storage_manager.delete_config_from_browser(selected_config):
                    st.success(f"✅ {get_text('config_deleted')}「{selected_config}」設定")
                    st.rerun()
                else:
                    st.error(get_text('delete_failed'))
            else:
                st.warning(get_text('cannot_delete_default'))

    # 儲存當前設定
    st.markdown("---")
    st.markdown(f"**{get_text('save_current_config')}**")
    
    new_config_name = st.text_input(
        get_text('config_name'),
        placeholder=get_text('config_name_placeholder'),
        help=get_text('config_name_help')
    )
    
    if st.button(get_text('save_config')):
        if new_config_name:
            current_config = file_storage_manager.get_current_config()
            if file_storage_manager.save_config_to_browser(new_config_name, current_config):
                st.success(f"✅ 設定「{new_config_name}」{get_text('config_saved')}")
                st.rerun()
            else:
                st.error(get_text('save_failed'))
        else:
            st.error(get_text('enter_config_name'))

def render_parameters_section():
    """渲染參數配置區域"""
    # 基本處理參數
    st.subheader(get_text('basic_params'))
    
    pixel_size_mm = st.number_input(
        get_text('pixel_size'),
        min_value=0.01,
        max_value=1.0,
        step=0.01,
        key='pixel_size_mm',
        help=get_text('pixel_size_help')
    )

    confidence_threshold = st.slider(
        get_text('confidence_threshold'),
        min_value=0.1,
        max_value=1.0,
        step=0.05,
        key='confidence_threshold',
        help=get_text('confidence_threshold_help')
    )

    # 線條提取參數
    st.subheader(get_text('line_extraction'))
    sample_interval = st.number_input(
        get_text('sample_interval'),
        min_value=1,
        max_value=100,
        step=1,
        key='sample_interval',
        help=get_text('sample_interval_help')
    )

    gradient_search_top = st.number_input(
        get_text('gradient_search_top'),
        min_value=1,
        max_value=50,
        step=1,
        key='gradient_search_top',
        help=get_text('gradient_search_top_help')
    )

    gradient_search_bottom = st.number_input(
        get_text('gradient_search_bottom'),
        min_value=1,
        max_value=50,
        step=1,
        key='gradient_search_bottom',
        help=get_text('gradient_search_bottom_help')
    )

    keep_ratio = st.slider(
        get_text('keep_ratio'),
        min_value=0.1,
        max_value=1.0,
        step=0.1,
        key='keep_ratio',
        help=get_text('keep_ratio_help')
    )

    # 視覺化參數
    st.subheader(get_text('visualization'))
    line_thickness = st.number_input(
        get_text('line_thickness'),
        min_value=1,
        max_value=10,
        step=1,
        key='line_thickness',
        help=get_text('line_thickness_help')
    )

    line_alpha = st.slider(
        get_text('line_alpha'),
        min_value=0.1,
        max_value=1.0,
        step=0.1,
        key='line_alpha',
        help=get_text('line_alpha_help')
    )

    display_labels = st.checkbox(
        get_text('display_labels'),
        key='display_labels',
        help=get_text('display_labels_help')
    )
    
    # 是否開啟區域限制
    region_limit = st.checkbox(
        get_text('region_limit'),
        key='region_limit',
        help=get_text('region_limit_help')
    )

    # 線條顏色選擇
    color_options = {
        get_text('color_green'): (0, 255, 0),
        get_text('color_red'): (0, 0, 255),
        get_text('color_blue'): (255, 0, 0),
        get_text('color_white'): (255, 255, 255),
        get_text('color_yellow'): (0, 255, 255)
    }
    
    line_color_option = st.selectbox(
        get_text('line_color'),
        options=list(color_options.keys()),
        key='line_color_option',
        help=get_text('line_color_help'),
    )
    
    line_color = color_options.get(line_color_option, (0, 255, 0))

    # 批次處理資訊
    st.subheader(get_text('batch_processing'))
    st.info(f"{get_text('batch_size_info')}: {BATCH_SIZE} {get_text('images_text')}")
    st.info(get_text('batch_efficiency'))
    
    return {
        'pixel_size_mm': pixel_size_mm,
        'confidence_threshold': confidence_threshold,
        'sample_interval': sample_interval,
        'gradient_search_top': gradient_search_top,
        'gradient_search_bottom': gradient_search_bottom,
        'keep_ratio': keep_ratio,
        'line_thickness': line_thickness,
        'line_alpha': line_alpha,
        'display_labels': display_labels,
        'line_color': line_color,
        'region_limit': region_limit,
    }

def render_upload_section():
    """渲染上傳區域"""
    # # 分段上傳（大影片檔案）
    # st.subheader(get_text('video_upload'))
    # chunked_video = chunked_uploader(
    #     get_text('select_video'),
    #     key="video_uploader",
    #     chunk_size=8,  # 8MB 分段
    #     help=get_text('video_upload_help'),
    # )
    
    # if chunked_video is not None:
    #     st.success(f"{get_text('video_uploaded')}: {chunked_video.name}")
    #     st.info(f"{get_text('file_size')}: {chunked_video.size / (1024*1024):.1f} MB")

    # 圖片上傳區域
    st.subheader(get_text('image_upload'))
    uploaded_files = st.file_uploader(
        get_text('select_images'),
        type=['png', 'jpg', 'jpeg', 'bmp', 'tiff'],
        accept_multiple_files=True,
        help=get_text('select_images_help')
    )
    
    return uploaded_files

def render_results_section(results):
    """渲染結果顯示區域"""
    if not results:
        return
        
    st.subheader(get_text('analysis_results'))

    # 統計摘要
    successful_results = [r for r in results if r['success']]
    failed_results = [r for r in results if not r['success']]

    if successful_results:
        col1, col2, col3, col4 = st.columns(4)

        all_mean_lengths = [r['stats']['mean_length'] for r in successful_results]

        with col1:
            st.metric(
                get_text('successful_processing'),
                f"{len(successful_results)}/{len(results)}"
            )
        with col2:
            st.metric(f"{get_text('average_length')}", f"{np.mean(all_mean_lengths):.2f}")
        with col3:
            st.metric(get_text('max_average_length'), f"{np.max(all_mean_lengths):.2f}")
        with col4:
            st.metric(get_text('min_average_length'), f"{np.min(all_mean_lengths):.2f}")

    if failed_results:
        st.warning(f"⚠️ {len(failed_results)} {get_text('processing_failed')}")

    # 顯示成功的結果
    successful_with_images = [r for r in successful_results if r['result'] is not None]

    if successful_with_images:
        # 每行顯示2張圖片
        cols_per_row = 2
        num_rows = math.ceil(len(successful_with_images) / cols_per_row)

        for row in range(num_rows):
            cols = st.columns(cols_per_row)

            for col_idx in range(cols_per_row):
                result_idx = row * cols_per_row + col_idx

                if result_idx < len(successful_with_images):
                    result = successful_with_images[result_idx]

                    with cols[col_idx]:
                        st.subheader(f"📷 {result['filename']}")

                        # 只顯示處理後的圖片
                        st.image(result['result'], use_container_width=True)

                        # 顯示統計資料
                        stats = result['stats']

                        # 使用更緊凑的佈局顯示統計數據
                        st.markdown(f"**{get_text('measurement_data')}**")

                        metrics_col1, metrics_col2 = st.columns(2)
                        with metrics_col1:
                            st.metric(get_text('confidence'), f"{stats['confidence']:.3f}")
                            st.metric(get_text('num_lines'), stats['num_lines'])
                        with metrics_col2:
                            st.metric(f"{get_text('mean_length')}", f"{stats['mean_length']:.2f} mm")
                            st.metric(get_text('std_length'), f"{stats['std_length']:.2f} mm")

                        # 顯示範圍
                        st.markdown(f"**{get_text('range')}:** {stats['min_length']:.2f} - {stats['max_length']:.2f} mm")
                        st.markdown("---")

    # 失敗結果單獨顯示
    if failed_results:
        st.subheader(get_text('failed_images'))
        for result in failed_results:
            st.error(f"**{result['filename']}**: {result['stats'].get('error', get_text('unknown_error'))}")

def render_download_section(results):
    """渲染下載區域"""
    successful_results = [r for r in results if r['success']]
    
    if not successful_results:
        return
        
    st.subheader(get_text('download_results'))
    
    # 生成 Excel 和 CSV 檔案
    excel_buffer = None
    csv_content = None

    try:
        excel_buffer = generate_excel_from_results(results)
        csv_content = generate_csv_from_results(results)
    except ImportError:
        st.error(get_text('excel_load_failed'))
    except Exception as e:
        st.error(f"{get_text('excel_csv_failed')}: {str(e)}")

    # 創建 ZIP 檔案
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        # 儲存圖片結果
        for result in successful_results:
            if result['result']:
                img_buffer = BytesIO()
                result['result'].save(img_buffer, format='JPEG')
                zip_file.writestr(
                    f"results/result_{result['filename']}",
                    img_buffer.getvalue()
                )
                
        # 將 Excel 檔案也加入 ZIP
        if excel_buffer:
            zip_file.writestr(
                "measurement_results.xlsx", excel_buffer.getvalue())

        # 將 CSV 檔案也加入 ZIP
        if csv_content:
            zip_file.writestr(
                "measurement_results.csv", csv_content.encode('utf-8-sig'))

    # 下載按鈕佈局
    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            label=get_text('download_complete'),
            data=zip_buffer.getvalue(),
            file_name="vessel_complete_analysis_results.zip",
            mime="application/zip",
            help=get_text('download_complete_help')
        )

    with col2:
        if excel_buffer:
            st.download_button(
                label=get_text('download_excel'),
                data=excel_buffer.getvalue(),
                file_name="vessel_measurement_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help=get_text('download_excel_help')
            )
        else:
            st.error(get_text('excel_generation_failed'))

    with col3:
        if csv_content:
            st.download_button(
                label=get_text('download_csv'),
                data=csv_content,
                file_name="vessel_measurement_results.csv",
                mime="text/csv",
                help=get_text('download_csv_help')
            )
        else:
            st.error(get_text('csv_generation_failed'))

    # 處理效率顯示
    st.metric(get_text('processing_efficiency'), f"{len(successful_results)} {get_text('success_count')}")

def main():
    # 獲取當前設定
    current_config = file_storage_manager.get_current_config()

    # 初始化語言
    initialize_language()
    
    # 頁面配置
    setup_page_config()
    
    # 初始化應用狀態
    initialize_app_state()

    # 主標題
    st.title(get_text('main_title'))
    st.markdown("---")

    # 側邊欄配置
    with st.sidebar:
        # 語言選擇器
        render_language_selector()
        st.markdown("---")
        
        # 系統配置標題
        st.header(get_text('system_config'))

        # 模型選擇區域
        render_model_section()

        # 設定管理區域
        render_settings_section()

        # 參數配置區域
        params = render_parameters_section()
    
    # 主要內容區域
    if st.session_state.predictor is None:
        st.error(get_text('model_not_loaded'))
        st.info(get_text('check_model_path'))
        return

    # 上傳區域
    uploaded_files = render_upload_section()
    
    if uploaded_files:
        
        # 是否開啟區域限制
        if params['region_limit']:
            selected_regions = render_canvas_section(uploaded_files[0], current_config['rect_width'], current_config['rect_height'])
        else:
            selected_regions = None
        
        st.success(f"{get_text('uploaded_count')} {len(uploaded_files)} {get_text('images_text')}")

        # 處理選項
        col1, col2 = st.columns(2)
        with col1:
            process_all = st.button(get_text('process_all'), type="primary")
        with col2:
            clear_results = st.button(get_text('clear_results'))

        if clear_results:
            st.session_state.processed_results = []
            st.rerun()

        # 批次處理圖片
        if process_all:
            progress_bar = st.progress(0)
            status_text = st.empty()

            # 準備配置參數
            line_config = {
                'sample_interval': params['sample_interval'],
                'gradient_search_top': params['gradient_search_top'],
                'gradient_search_bottom': params['gradient_search_bottom'],
                'keep_ratio': params['keep_ratio']
            }

            vis_config = {
                'line_color': params['line_color'],
                'line_thickness': params['line_thickness'],
                'line_alpha': params['line_alpha'],
                'display_labels': params['display_labels']
            }

            # 準備圖片資料
            images_data = [(f.name, Image.open(f)) for f in uploaded_files]
            total_batches = math.ceil(len(images_data) / BATCH_SIZE)

            status_text.text(
                f"{get_text('start_batch_processing')} {len(images_data)} {get_text('images_text')} ({total_batches} {get_text('batches_text')})")

            # 批次處理
            st.session_state.processed_results = process_batch_images(
                predictor=st.session_state.predictor,
                images=images_data,
                pixel_size_mm=params['pixel_size_mm'],
                conf_threshold=params['confidence_threshold'],
                region=selected_regions,
                line_config=line_config,
                vis_config=vis_config
            )

            progress_bar.progress(1.0)
            status_text.text(get_text('processing_complete'))

        # 顯示結果
        if st.session_state.processed_results:
            render_results_section(st.session_state.processed_results)
            render_download_section(st.session_state.processed_results)

if __name__ == "__main__":
    main()