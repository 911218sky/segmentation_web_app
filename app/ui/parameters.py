import streamlit as st

from config import (
    BATCH_SIZE,
    get_text,
)

def parameters_section():
    """渲染參數配置區域（側欄），並回傳參數字典"""
    st.subheader(get_text('basic_params'))

    if 'pixel_size_mm' not in st.session_state:
        st.session_state['pixel_size_mm'] = 0.05
    pixel_size_mm = st.number_input(
        get_text('pixel_size'),
        min_value=0.01,
        max_value=1.0,
        step=0.01,
        key='pixel_size_mm',
        help=get_text('pixel_size_help')
    )

    if 'confidence_threshold' not in st.session_state:
        st.session_state['confidence_threshold'] = 0.4
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
    if 'sample_interval' not in st.session_state:
        st.session_state['sample_interval'] = 5
    sample_interval = st.number_input(
        get_text('sample_interval'),
        min_value=1,
        max_value=100,
        step=1,
        key='sample_interval',
        help=get_text('sample_interval_help')
    )

    if 'gradient_search_top' not in st.session_state:
        st.session_state['gradient_search_top'] = 5
    gradient_search_top = st.number_input(
        get_text('gradient_search_top'),
        min_value=1,
        max_value=50,
        step=1,
        key='gradient_search_top',
        help=get_text('gradient_search_top_help')
    )

    if 'gradient_search_bottom' not in st.session_state:
        st.session_state['gradient_search_bottom'] = 5
    gradient_search_bottom = st.number_input(
        get_text('gradient_search_bottom'),
        min_value=1,
        max_value=50,
        step=1,
        key='gradient_search_bottom',
        help=get_text('gradient_search_bottom_help')
    )

    if 'keep_ratio' not in st.session_state:
        st.session_state['keep_ratio'] = 0.3
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
    if 'line_thickness' not in st.session_state:
        st.session_state['line_thickness'] = 1
    line_thickness = st.number_input(
        get_text('line_thickness'),
        min_value=1,
        max_value=10,
        step=1,
        key='line_thickness',
        help=get_text('line_thickness_help')
    )

    if 'line_alpha' not in st.session_state:
        st.session_state['line_alpha'] = 0.7
    line_alpha = st.slider(
        get_text('line_alpha'),
        min_value=0.1,
        max_value=1.0,
        step=0.1,
        key='line_alpha',
        help=get_text('line_alpha_help')
    )

    if 'display_labels' not in st.session_state:
        st.session_state['display_labels'] = True
    display_labels = st.checkbox(
        get_text('display_labels'),
        key='display_labels',
        help=get_text('display_labels_help')
    )

    # 是否開啟區域限制
    if 'region_limit' not in st.session_state:
        st.session_state['region_limit'] = True
    region_limit = st.checkbox(
        get_text('region_limit'),
        key='region_limit',
        help=get_text('region_limit_help')
    )

    # 線條顏色選擇 (使用語言無關的 key)
    color_keys = ['color_green', 'color_red', 'color_blue', 'color_white', 'color_yellow']
    color_values = {
        'color_green': (0, 255, 0),
        'color_red': (0, 0, 255),
        'color_blue': (255, 0, 0),
        'color_white': (255, 255, 255),
        'color_yellow': (0, 255, 255)
    }

    # 取得當前選中的顏色 index
    if 'line_color_option' not in st.session_state:
        st.session_state['line_color_option'] = 'color_green'
    current_color = st.session_state['line_color_option']
    color_index = color_keys.index(current_color) if current_color in color_keys else 0

    line_color_option = st.selectbox(
        get_text('line_color'),
        options=color_keys,
        index=color_index,
        format_func=lambda x: get_text(x),
        key='line_color_option',
        help=get_text('line_color_help'),
    )

    line_color = color_values.get(line_color_option, (0, 255, 0))

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
