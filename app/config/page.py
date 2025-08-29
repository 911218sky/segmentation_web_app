import streamlit as st

PAGES = {
    "images": "📷 圖片處理",
    "videos": "🎞️ 影片處理",
    "results": "✅ 結果與下載"
}

def switch_page(page: str):
    if page not in PAGES:
        raise ValueError(f"Invalid page: {page}")
    st.session_state.active_page = page
    st.rerun()