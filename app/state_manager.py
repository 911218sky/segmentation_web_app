from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from PIL import Image
from streamlit.runtime.uploaded_file_manager import UploadedFile
import io

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

@dataclass
class AppState:
    """應用程序狀態的數據類"""
    # 文件和結果
    uploaded_files: List[UploadedFile] = field(default_factory=list)
    results: List[Tuple[Optional[Image.Image], Optional[Image.Image], List[float]]] = field(default_factory=list)
    
    # 緩存和緩衝區
    zip_buffer: Optional[io.BytesIO] = None
    mean_lengths_cache: Dict[str, List[float]] = field(default_factory=dict)
    excel_buffer: Optional[io.BytesIO] = None
    
    # 測量相關
    selected_measurements: Dict[str, float] = field(default_factory=dict)
    measurement_data: Optional[List[Dict[str, str]]] = None
    
    # 狀態標誌
    form_submitted: bool = False
    processing: bool = False
    results_confirmed: bool = False
    compression_in_progress: bool = False
    
    # 其他
    last_changed_radio: Optional[str] = None
    params: ProcessingParams = field(default_factory=ProcessingParams)

    def reset_processing_state(self) -> None:
        """重置處理相關的狀態"""
        self.processing = False
        self.results_confirmed = False
        self.compression_in_progress = False
        self.measurement_data = None
        self.excel_buffer = None
        self.zip_buffer = None

    def reset_file_state(self) -> None:
        """重置文件相關的狀態"""
        self.results = []
        self.zip_buffer = None
        self.mean_lengths_cache = {}
        self.selected_measurements = {}
        self.results_confirmed = False
        self.excel_buffer = None

    def update_params(self, new_params: Dict[str, Any]) -> None:
        """更新處理參數"""
        for key, value in new_params.items():
            if hasattr(self.params, key):
                setattr(self.params, key, value)

    def to_streamlit_state(self) -> Dict[str, Any]:
        """將狀態轉換為 Streamlit session_state 格式"""
        state_dict = asdict(self)
        # 移除不需要存儲在 session_state 中的字段
        state_dict['params'] = asdict(self.params)
        return state_dict

def initialize_state(st) -> AppState:
    """初始化應用程序狀態"""
    state = AppState()
    
    # 如果 session_state 中已有數據，則更新狀態
    for key in state.to_streamlit_state().keys():
        if key not in st.session_state:
            st.session_state[key] = state.to_streamlit_state()[key]
        else:
            # 更新 AppState 實例中的值
            if key == 'params':
                state.params = ProcessingParams(**st.session_state[key])
            else:
                setattr(state, key, st.session_state[key])
    
    return state

def update_streamlit_state(st, state: AppState) -> None:
    """更新 Streamlit session_state"""
    state_dict = state.to_streamlit_state()
    for key, value in state_dict.items():
        st.session_state[key] = value 