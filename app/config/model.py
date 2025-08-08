import streamlit as st
import time
from yolo_predictor import YOLOPredictor

from .config import AVAILABLE_MODELS, DEFAULT_MODEL, MODELS_DIR

def get_model_path(model_name):
    """根據模型名稱獲取完整路徑"""
    if model_name in AVAILABLE_MODELS:
        return MODELS_DIR / AVAILABLE_MODELS[model_name]
    return MODELS_DIR / AVAILABLE_MODELS[DEFAULT_MODEL]

@st.cache_resource
def load_model(model_name):
    """載入並快取 YOLO 模型"""
    try:
        weights_path = get_model_path(model_name)
        
        if not weights_path.exists():
            st.error(f"模型檔案不存在: {weights_path}")
            return None, None
        predictor = YOLOPredictor(weights_path)
        return predictor, model_name
    except Exception as e:
        st.error(f"模型載入失敗: {str(e)}")
        return None, None

def switch_model(new_model_name):
    """切換模型"""
    if new_model_name != st.session_state.get('current_model_name'):
        # 清除快取並重新載入模型
        load_model.clear()
        with st.spinner(f"正在載入模型: {new_model_name}..."):
            predictor, loaded_model_name = load_model(new_model_name)
            if predictor is not None:
                st.session_state.predictor = predictor
                st.session_state.current_model_name = loaded_model_name
                st.session_state.selected_model = new_model_name
                # 清除之前的處理結果
                st.session_state.processed_results = []
                st.success(f"✅ 已切換至模型: {new_model_name}")
                st.rerun()
            else:
                st.error(f"❌ 模型載入失敗: {new_model_name}")