import streamlit as st

from config import (
    AVAILABLE_MODELS,
    DEFAULT_MODEL,
    # config manager
    file_storage_manager,
    # language
    get_text,
    # model
    switch_model,
    get_model_path,
)

def model_section():
    """渲染模型選擇區域（側欄）"""
    st.subheader(get_text('model_selection'))

    current_config = file_storage_manager.get_current_config()
    current_model = current_config.get('selected_model', DEFAULT_MODEL)

    # 模型選擇器
    selected_model = st.selectbox(
        get_text('select_model'),
        options=list(AVAILABLE_MODELS.keys()),
        index=list(AVAILABLE_MODELS.keys()).index(current_model),
        key='model_selector',
        help=get_text('select_model_help')
    )
    
    # 模型切換按鈕
    if st.button(get_text('switch_model'), type="secondary"):
        switch_model(selected_model)
 
    # 如果選擇了模型，則更新當前模型
    if selected_model is not None:
        current_model = selected_model
        
    # 顯示當前模型資訊
    if current_config:
        st.info(f"{get_text('current_model')}: {current_model}")

    # 自動載入預設模型（如果還沒載入）
    if st.session_state.predictor is None:
        current_model = current_config.get('selected_model', current_model)
        switch_model(current_model)

    # 模型狀態顯示
    st.subheader(get_text('model_status'))
    if st.session_state.predictor is not None:
        st.success(f"{get_text('model_loaded')}: {current_model}")
        try:
            model_path = get_model_path(current_model)
            st.caption(f"📁 {get_text('model_file')}: {model_path.name}")
        except Exception:
            pass
    else:
        st.error(get_text('model_failed'))
        available_models_info = []
        for name, filename in AVAILABLE_MODELS.items():
            try:
                model_path = get_model_path(name)
                status = "✅" if model_path.exists() else "❌"
            except Exception:
                status = "❌"
            available_models_info.append(f"{status} {name}: {filename}")

        st.info(f"{get_text('available_models')}:\n" + "\n".join(available_models_info))