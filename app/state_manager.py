from dataclasses import dataclass
from typing import Dict, Tuple, Any

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
    def params(self):
        return self.st.session_state.params

    @params.setter
    def params(self, value):
        self.st.session_state.params = value

    def update_params(self, new_params: Dict[str, Any]) -> None:
        """更新處理參數"""
        for key, value in new_params.items():
            if hasattr(self.params, key):
                setattr(self.params, key, value)

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