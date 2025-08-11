import json
import streamlit as st
from .config import DEFAULT_CONFIGS, STORAGE_KEY, STORAGE_DIR, CONFIG_FILE

class FileStorageManager:
    """檔案存儲管理器，負責處理配置的持久化存儲"""
    
    def __init__(self):
        """初始化檔案存儲管理器"""
        self.storage_dir = STORAGE_DIR
        self.config_file = CONFIG_FILE
        self.storage_key = STORAGE_KEY
        self.default_configs = DEFAULT_CONFIGS
    
    def _ensure_storage_dir(self):
        """確保存儲目錄存在"""
        try:
            self.storage_dir.mkdir(exist_ok=True)
            return True
        except Exception as e:
            st.error(f"無法建立存儲目錄: {str(e)}")
            return False
    
    def _read_config_file(self):
        """讀取配置檔案"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            st.error(f"讀取配置檔案失敗: {str(e)}")
            return {}
    
    def _write_config_file(self, data):
        """寫入配置檔案"""
        try:
            if not self._ensure_storage_dir():
                return False
                
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            st.error(f"寫入配置檔案失敗: {str(e)}")
            return False
    
    def initialize_session_state(self):
        """初始化 session state 配置值"""
        if 'config_initialized' not in st.session_state:
            default_config = self.default_configs['系統預設']
            for key, value in default_config.items():
                if key not in st.session_state:
                    st.session_state[key] = value
            st.session_state.config_initialized = True
    
    def load_saved_configs(self):
        """從檔案載入保存的設定"""
        try:
            # 讀取檔案中的用戶配置
            saved_data = self._read_config_file()
            saved_configs = saved_data.get(self.storage_key, {})
            
            if saved_configs:
                # 處理可能的 JSON 字串或已解析的對象
                if isinstance(saved_configs, str):
                    try:
                        configs = json.loads(saved_configs)
                    except json.JSONDecodeError:
                        st.warning("配置數據格式錯誤，使用預設配置")
                        return self.default_configs.copy()
                else:
                    configs = saved_configs
                
                # 合併預設配置和用戶配置
                all_configs = self.default_configs.copy()
                if isinstance(configs, dict):
                    all_configs.update(configs)
                return all_configs
            else:
                return self.default_configs.copy()
                
        except Exception as e:
            st.error(f"載入設定失敗: {str(e)}")
            # 清除可能損壞的數據
            try:
                if self.config_file.exists():
                    self.config_file.unlink()
            except:
                pass
            return self.default_configs.copy()
    
    def save_config_to_browser(self, config_name, config):
        """儲存設定到檔案"""
        try:
            # 載入現有配置
            current_configs = self.load_saved_configs()
            user_configs = {k: v for k, v in current_configs.items() 
                          if k not in self.default_configs}
            user_configs[config_name] = config
            
            # 準備要寫入的數據
            data_to_save = self._read_config_file()
            data_to_save[self.storage_key] = user_configs
            
            # 寫入檔案
            return self._write_config_file(data_to_save)
            
        except Exception as e:
            st.error(f"儲存設定失敗: {str(e)}")
            return False
    
    def delete_config_from_browser(self, config_name):
        """從檔案刪除設定"""
        try:
            if config_name in self.default_configs:
                return False  # 不能刪除預設設定
                
            current_configs = self.load_saved_configs()
            user_configs = {k: v for k, v in current_configs.items() 
                          if k not in self.default_configs}
            
            if config_name in user_configs:
                del user_configs[config_name]
                
                # 準備要寫入的數據
                data_to_save = self._read_config_file()
                data_to_save[self.storage_key] = user_configs
                
                return self._write_config_file(data_to_save)
            return False
            
        except Exception as e:
            st.error(f"刪除設定失敗: {str(e)}")
            return False
    
    @staticmethod
    def apply_config(config):
        """套用配置到控件"""
        for key, value in config.items():
            st.session_state[key] = value
    
    @staticmethod
    def get_current_config():
        """獲取當前的配置參數"""
        default_config = DEFAULT_CONFIGS["系統預設"]
        return {
            "selected_model": st.session_state.get('selected_model', default_config['selected_model']),
            "pixel_size_mm": st.session_state.get('pixel_size_mm', default_config['pixel_size_mm']),
            "confidence_threshold": st.session_state.get('confidence_threshold', default_config['confidence_threshold']),
            "sample_interval": st.session_state.get('sample_interval', default_config['sample_interval']),
            "gradient_search_top": st.session_state.get('gradient_search_top', default_config['gradient_search_top']),
            "gradient_search_bottom": st.session_state.get('gradient_search_bottom', default_config['gradient_search_bottom']),
            "keep_ratio": st.session_state.get('keep_ratio', default_config['keep_ratio']),
            "line_thickness": st.session_state.get('line_thickness', default_config['line_thickness']),
            "line_alpha": st.session_state.get('line_alpha', default_config['line_alpha']),
            "display_labels": st.session_state.get('display_labels', default_config['display_labels']),
            "region_limit": st.session_state.get('region_limit', default_config['region_limit']),
            "line_color_option": st.session_state.get('line_color_option', default_config['line_color_option']),
        }