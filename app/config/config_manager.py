import streamlit as st
import json
from streamlit_local_storage import LocalStorage
from config import DEFAULT_CONFIGS

# 初始化瀏覽器本地存儲
localS = LocalStorage()

def initialize_session_state():
    """初始化 session state 配置值"""
    if 'config_initialized' not in st.session_state:
        default_config = DEFAULT_CONFIGS['系統預設']
        for key, value in default_config.items():
            if key not in st.session_state:
                st.session_state[key] = value
        st.session_state.config_initialized = True

def load_saved_configs():
    """從瀏覽器載入保存的設定"""
    try:
        saved_configs = localS.getItem("vessel_saved_configs")
        if saved_configs:
            configs = json.loads(saved_configs) if isinstance(saved_configs, str) else saved_configs
            all_configs = DEFAULT_CONFIGS.copy()
            all_configs.update(configs)
            return all_configs
        else:
            return DEFAULT_CONFIGS.copy()
    except (json.JSONDecodeError, TypeError, AttributeError) as e:
        st.error(f"載入設定失敗: {str(e)}")
        # 清除損壞的數據
        try:
            localS.deleteItem("vessel_saved_configs")
        except:
            pass
        return DEFAULT_CONFIGS.copy()
    except Exception as e:
        st.error(f"載入設定失敗: {str(e)}")
        return DEFAULT_CONFIGS.copy()

def save_config_to_browser(config_name, config):
    """儲存設定到瀏覽器"""
    try:
        # 載入現有設定
        current_configs = load_saved_configs()
        
        # 只保存非預設的設定
        user_configs = {k: v for k, v in current_configs.items() if k not in DEFAULT_CONFIGS}
        user_configs[config_name] = config
        
        # 儲存到瀏覽器
        localS.setItem("vessel_saved_configs", json.dumps(user_configs, ensure_ascii=False))
        return True
    except Exception as e:
        st.error(f"儲存設定失敗: {str(e)}")
        return False

def delete_config_from_browser(config_name):
    """從瀏覽器刪除設定"""
    try:
        if config_name in DEFAULT_CONFIGS:
            return False  # 不能刪除預設設定
            
        current_configs = load_saved_configs()
        user_configs = {k: v for k, v in current_configs.items() if k not in DEFAULT_CONFIGS}
        
        if config_name in user_configs:
            del user_configs[config_name]
            localS.setItem("vessel_saved_configs", json.dumps(user_configs, ensure_ascii=False))
            return True
        return False
    except Exception as e:
        st.error(f"刪除設定失敗: {str(e)}")
        return False

def apply_config(config):
    """套用配置到控件"""
    for key, value in config.items():
        st.session_state[key] = value

def get_current_config():
    """獲取當前的配置參數"""
    default_config = DEFAULT_CONFIGS["系統預設"]
    return {
        "pixel_size_mm": st.session_state.get('pixel_size_mm', default_config['pixel_size_mm']),
        "confidence_threshold": st.session_state.get('confidence_threshold', default_config['confidence_threshold']),
        "sample_interval": st.session_state.get('sample_interval', default_config['sample_interval']),
        "gradient_search_top": st.session_state.get('gradient_search_top', default_config['gradient_search_top']),
        "gradient_search_bottom": st.session_state.get('gradient_search_bottom', default_config['gradient_search_bottom']),
        "keep_ratio": st.session_state.get('keep_ratio', default_config['keep_ratio']),
        "line_thickness": st.session_state.get('line_thickness', default_config['line_thickness']),
        "line_alpha": st.session_state.get('line_alpha', default_config['line_alpha']),
        "display_labels": st.session_state.get('display_labels', default_config['display_labels']),
        "line_color_option": st.session_state.get('line_color_option', default_config['line_color_option'])
    }
