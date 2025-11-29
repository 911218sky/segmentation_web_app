import streamlit as st

PAGES = {
    "images": "page_images",
    "videos": "page_videos",
    "results": "page_results"
}

def switch_page(page: str):
    if page not in PAGES:
        raise ValueError(f"Invalid page: {page}")
    st.session_state.active_page = page
    st.rerun()