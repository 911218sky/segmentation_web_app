import streamlit as st

from config import (
    file_storage_manager,
    # page config
    PAGES,
)
from ui import (
    model_section, 
    settings_section, 
    parameters_section, 
    language_selector,
    
    # image
    upload_images,
    handle_image_processing,
    image_results,
    image_downloads,
    
    # video
    upload_video,
    handle_video_processing,
    video_results,
    video_downloads,
)

def init_session():
    # YOLO 預測器初始化
    if 'predictor' not in st.session_state:
        st.session_state.predictor = None
    # 初始化 img_results
    if 'img_results' not in st.session_state:
        st.session_state.img_results = []
    # 初始化 video_results
    if 'video_results' not in st.session_state:
        st.session_state.video_results = {}
    # 默認語言
    if 'language' not in st.session_state:
        st.session_state.language = 'zh'
    # 初始化 file_storage_manager
    if 'file_manager_initialized' not in st.session_state:
        file_storage_manager.initialize_session_state()
        st.session_state.file_manager_initialized = True
    # 用於切換 tab
    if 'active_page' not in st.session_state:
        st.session_state.active_page = list(PAGES.keys())[0]

def set_page_config():
    st.set_page_config(
        page_title="Vessel Analyzer",
        page_icon="🚢",
        layout="wide",
        initial_sidebar_state="expanded",
    )

def main():
    init_session()
    set_page_config()
    
    # 側邊欄（語言 / 模型 / 設定 / 參數）
    with st.sidebar:
        language_selector()
        st.markdown("---")
        model_section()
        settings_section()
        params = parameters_section()
    
    page = st.segmented_control(
        label="🔖 功能",
        options=PAGES.keys(),
        format_func=lambda x: PAGES[x],
        default=st.session_state.active_page,
        key="active_page_control",
        on_change=None 
    )
    
    if page == "images":
        uploads = upload_images()
        if uploads:
            handle_image_processing(uploads, params)
    elif page == "videos":
        upload = upload_video()
        if upload:
            handle_video_processing(upload, params)
    elif page == "results":
        sub = st.tabs(["📷 圖片結果", "🎞️ 影片結果"])
        with sub[0]:
            image_downloads()
            image_results()
        with sub[1]:
            video_downloads()
            video_results()


if __name__ == "__main__":
    main()