from dataclasses import dataclass, asdict
from typing import Dict, Tuple, Any
from streamlit_local_storage import LocalStorage

@dataclass
class ProcessingParams:
    """處理參數的數據類"""
    num_lines: int = 50
    line_width: int = 3
    min_length_mm: float = 1.0
    max_length_mm: float = 7.0
    depth_cm: float = 3.2
    line_length_weight: float = 1.0
    line_color: Tuple[int, int, int] = (0, 255, 0)
    deviation_threshold: float = 0.0
    deviation_percent: float = 0.1

class AppState:
    def __init__(self, st):
        self.st = st
        self.local_storage = LocalStorage(key="app_state")
        if 'uploaded_files' not in self.st.session_state:
            self.st.session_state.uploaded_files = []
            self.st.session_state.results = []
            self.st.session_state.processing = False
            self.st.session_state.form_submitted = False
            self.st.session_state.results_confirmed = False
            self.st.session_state.selected_measurements = {}
            self.st.session_state.mean_lengths_cache = {}
            self.st.session_state.measurement_data = None
            self.st.session_state.excel_buffer = None
            self.st.session_state.zip_buffer = None
            self.st.session_state.params = ProcessingParams()

    def save_params(self, preset_name: str) -> None:
        """保存當前參數設置"""
        saved_presets = self.local_storage.getItem("params_presets") or {}
        saved_presets[preset_name] = asdict(self.params)
        self.local_storage.setItem("params_presets", saved_presets)
        self.st.success(f"✅ 已保存參數設置: {preset_name}")

    def load_params(self, preset_name: str) -> None:
        """加載保存的參數設置"""
        saved_presets = self.local_storage.getItem("params_presets") or {}
        params_dict = saved_presets.get(preset_name)
        if params_dict:
            self.update_params(params_dict)
            self.st.success(f"✅ 已加載參數設置: {preset_name}")
        else:
            self.st.error(f"❌ 找不到參數設置: {preset_name}")

    def delete_preset(self, preset_name: str) -> None:
        """刪除保存的參數設置"""
        try:
            saved_presets = self.local_storage.getItem("params_presets") or {}
            if preset_name in saved_presets:
                updated_presets = saved_presets.copy()
                del updated_presets[preset_name]
                self.local_storage.setItem("params_presets", updated_presets)
                self.st.success(f"✅ 已刪除參數設置: {preset_name}")
            else:
                self.st.error(f"❌ 找不到參數設置: {preset_name}")
        except Exception as e:
            self.st.error(f"❌ 刪除參數設置時發生錯誤: {str(e)}")

    def get_saved_presets(self) -> Dict[str, Any]:
        presets = self.local_storage.getItem("params_presets") or {}
        return presets
    
    def update_params(self, new_params: Dict[str, Any]) -> None:
        try:
            params = ProcessingParams(**new_params)
            self.st.session_state.params = params
        except Exception as e:
            self.st.error(f"❌ 更新参数时发生错误: {str(e)}")
            self.st.session_state.params = ProcessingParams()

    def reset_file_state(self) -> None:
        """重置文件相關的狀態，但保留測量選擇"""
        self.results = []
        self.processing = False
        self.form_submitted = False
        self.results_confirmed = False
        self.mean_lengths_cache = {}
        self.measurement_data = None
        self.excel_buffer = None
        self.zip_buffer = None

    def reset_all(self) -> None:
        """完全重置所有狀態"""
        self.__init__(self.st)

    @property
    def uploaded_files(self):
        return self.st.session_state.uploaded_files

    @uploaded_files.setter
    def uploaded_files(self, value):
        self.st.session_state.uploaded_files = value

    @property
    def results(self):
        return self.st.session_state.results

    @results.setter
    def results(self, value):
        self.st.session_state.results = value

    @property
    def processing(self):
        return self.st.session_state.processing

    @processing.setter
    def processing(self, value):
        self.st.session_state.processing = value

    @property
    def form_submitted(self):
        return self.st.session_state.form_submitted

    @form_submitted.setter
    def form_submitted(self, value):
        self.st.session_state.form_submitted = value

    @property
    def results_confirmed(self):
        return self.st.session_state.results_confirmed

    @results_confirmed.setter
    def results_confirmed(self, value):
        self.st.session_state.results_confirmed = value

    @property
    def selected_measurements(self):
        return self.st.session_state.selected_measurements

    @selected_measurements.setter
    def selected_measurements(self, value):
        self.st.session_state.selected_measurements = value

    @property
    def mean_lengths_cache(self):
        return self.st.session_state.mean_lengths_cache

    @mean_lengths_cache.setter
    def mean_lengths_cache(self, value):
        self.st.session_state.mean_lengths_cache = value

    @property
    def measurement_data(self):
        return self.st.session_state.measurement_data

    @measurement_data.setter
    def measurement_data(self, value):
        self.st.session_state.measurement_data = value

    @property
    def excel_buffer(self):
        return self.st.session_state.excel_buffer

    @excel_buffer.setter
    def excel_buffer(self, value):
        self.st.session_state.excel_buffer = value

    @property
    def zip_buffer(self):
        return self.st.session_state.zip_buffer

    @zip_buffer.setter
    def zip_buffer(self, value):
        self.st.session_state.zip_buffer = value

    @property
    def params(self) -> ProcessingParams:
        return self.st.session_state.params

    @params.setter
    def params(self, value: ProcessingParams):
        self.st.session_state.params = value