import streamlit as st

from config import get_text

# 側邊欄函式（語言 / 模型 / 設定 / 參數）
def language_selector():
    """渲染語言選擇器（側欄）"""
    st.header(get_text('language_selector'))
    language_options = {
        '中文': 'zh',
        'English': 'en'
    }

    # 取得目前語言
    current_lang_key = [k for k, v in language_options.items()
                        if v == st.session_state.language][0]

    # 語言選擇器
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