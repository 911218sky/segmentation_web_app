import streamlit as st

from config import (
    DEFAULT_CONFIGS,
    DEFAULT_CONFIG_KEY,
    DEFAULT_MODEL,
    # config manager
    file_storage_manager,
    # language
    get_text,
    # model
    switch_model,
    # config
    CURRENT_CONFIG_NAME,
)

def _get_config_display_name(config_key: str) -> str:
    """取得設定的顯示名稱（預設設定使用翻譯，用戶設定使用原名）"""
    if config_key == DEFAULT_CONFIG_KEY:
        return get_text('default_config_name')
    return config_key

def settings_section():
    """渲染設定管理區域（側欄）"""
    st.subheader(get_text('settings_management'))

    # 載入所有可用設定
    available_configs = file_storage_manager.load_saved_configs()
    config_names = list(available_configs.keys())
    current_config_name = file_storage_manager.get_current_config_name()
    current_config = file_storage_manager.get_current_config()
    current_model = current_config.get('selected_model', DEFAULT_MODEL)

    selected_config_name = st.selectbox(
        get_text('select_config'),
        options=config_names,
        format_func=_get_config_display_name,
        index=config_names.index(current_config_name) if current_config_name in config_names else 0,
        help=get_text('select_config_help')
    )

    col1, col2 = st.columns(2)
    # 套用設定按鈕
    with col1:
        if st.button(get_text('apply_config'), type="primary"):
            if selected_config_name in available_configs:
                new_config = available_configs[selected_config_name]
                # 檢查是否需要切換模型
                config_model = new_config.get('selected_model')
                model_changed = config_model and config_model != current_model
                # 套用設定
                file_storage_manager.apply_config(new_config)
                # 保存目前設定
                file_storage_manager.save_config_to_file(selected_config_name, new_config)
                # 保存目前設定名稱
                file_storage_manager.save_data(CURRENT_CONFIG_NAME, selected_config_name)
                # 只有在模型改變時才切換模型並 rerun
                if model_changed:
                    switch_model(config_model)
                    st.success(get_text('config_applied_message').format(name=selected_config_name))
                    st.rerun()
                else:
                    st.success(get_text('config_applied_message').format(name=selected_config_name))

    # 刪除設定按鈕
    with col2:
        can_delete = selected_config_name not in DEFAULT_CONFIGS
        if st.button(get_text('delete_config'), disabled=not can_delete):
            if can_delete:
                if file_storage_manager.delete_config_from_file(selected_config_name):
                    st.success(get_text('config_deleted_message').format(name=selected_config_name))
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

    # 儲存設定按鈕
    if st.button(get_text('save_config')):
        if new_config_name:
            current_config = file_storage_manager.get_current_config()
            if file_storage_manager.save_config_to_file(new_config_name, current_config):
                st.success(get_text('config_saved_message').format(name=new_config_name))
                st.rerun()
            else:
                st.error(get_text('save_failed'))
        else:
            st.error(get_text('enter_config_name'))