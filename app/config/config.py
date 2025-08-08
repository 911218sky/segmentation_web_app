from pathlib import Path

# 路徑配置
BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEMP_DIR = BASE_DIR / "temp"
OUTPUT_DIR = BASE_DIR / "output"
MODELS_DIR = BASE_DIR / "models"

# 可用模型配置
AVAILABLE_MODELS = {
    "血管分割模型 v1.0": "best.pt",
    "血管分割模型 v3.0": "best_v3.pt",
}

# 預設模型
DEFAULT_MODEL = "血管分割模型 v1.0"
BATCH_SIZE = 32  # 批次處理大小

# 圖片大小配置 (將輸入圖片統一大小)
TARGET_SIZE = (1024, 1024)

# 模型配置
YOLO_CONFIG = {
    "imgsz": 640,
    "conf": 0.4,
    "iou": 0.1,
    "batch": 32,
    "device": 0,
    "verbose": False,
    "save": False,
    "stream": False,
    "retina_masks": True
}

# 處理配置
PROCESSING_CONFIG = {
    'pixel_size_mm': 0.01 # 圖片像素大小 (mm)
}

# 視覺化配置
VISUALIZATION_CONFIG = {
    "line_color": (255, 255, 255),  # 線條顏色
    "line_thickness": 1, # 線條粗細
    "line_alpha": 0.7, # 線條透明度
    "point_radius": 3, # 點的半徑
    "min_point_color": (255, 0, 0),  # 藍色
    "max_point_color": (0, 0, 255),  # 紅色
    "show_points": False, # 顯示點
    "display_labels": True # 顯示標籤
}

# 線條提取配置
LINE_EXTRACTION_CONFIG = {
    'sample_interval': 5,           # x 軸採樣步距
    'gradient_search_top': 20,       # 往上搜尋的最大像素距離
    'gradient_search_bottom': 20,    # 往下搜尋的最大像素距離
    'keep_ratio': 0.25,               # 保留的寬度比例
    'window_size': 5,                 # 平滑過濾視窗大小
    'threshold': 0.1                  # 平滑過濾閾值
}

# 預設設定組合 - 修正為嵌套結構
DEFAULT_CONFIGS = {
    "系統預設": {
        'selected_model': DEFAULT_MODEL,
        'pixel_size_mm': PROCESSING_CONFIG['pixel_size_mm'],
        'confidence_threshold': YOLO_CONFIG['conf'], 
        'sample_interval': LINE_EXTRACTION_CONFIG['sample_interval'],
        'gradient_search_top': LINE_EXTRACTION_CONFIG['gradient_search_top'],
        'gradient_search_bottom': LINE_EXTRACTION_CONFIG['gradient_search_bottom'],
        'keep_ratio': LINE_EXTRACTION_CONFIG['keep_ratio'],
        'line_thickness': VISUALIZATION_CONFIG['line_thickness'],
        'line_alpha': VISUALIZATION_CONFIG['line_alpha'],
        'display_labels': VISUALIZATION_CONFIG['display_labels'],
        'line_color_option': '綠色'
    },
}