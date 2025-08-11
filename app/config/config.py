from pathlib import Path

# 路徑配置
BASE_DIR = Path(__file__).resolve().parents[2]
TEMP_DIR = BASE_DIR / "temp"
OUTPUT_DIR = BASE_DIR / "output"
MODELS_DIR = BASE_DIR / "models"

# 配置檔案路徑
STORAGE_DIR = BASE_DIR / "user_configs"
CONFIG_FILE = STORAGE_DIR / "saved_configs.json"

# 可用模型配置
AVAILABLE_MODELS = {
    "v1.0": "best.pt",
    "v3.0 (alpha)": "best_v3_alpha.pt",
    "v3.0 (beta) new": "best_v3_beta.pt",
}

# 預設模型
DEFAULT_MODEL = "v3.0 (beta) new"

# 批次處理大小
BATCH_SIZE = 64

# 圖片大小配置
TARGET_SIZE = (1024, 1024)

# 儲存設定到瀏覽器的 key
STORAGE_KEY = "vessel_saved_configs"

# 模型配置
YOLO_CONFIG = {
    "imgsz": 640,
    "conf": 0.4,
    "iou": 0.1,
    "batch": BATCH_SIZE,
    "device": 0,
    "verbose": False,
    "save": False,
    "stream": False,
    "retina_masks": True,
}

# 處理配置
PROCESSING_CONFIG = {
    "pixel_size_mm": 0.05,  # 圖片像素大小 (mm)
}

# 視覺化配置
VISUALIZATION_CONFIG = {
    "line_color": (255, 255, 255),  # 線條顏色
    "line_thickness": 1,            # 線條粗細
    "line_alpha": 0.7,              # 線條透明度
    "point_radius": 3,              # 點的半徑
    "min_point_color": (255, 0, 0), # 藍色
    "max_point_color": (0, 0, 255), # 紅色
    "show_points": False,           # 顯示點
    "display_labels": True,         # 顯示標籤
    "region_limit": True,          # 是否開啟區域限制
}

# 線條提取配置
LINE_EXTRACTION_CONFIG = {
    "sample_interval": 5,         # x 軸採樣步距
    "gradient_search_top": 5,     # 往上搜尋的最大像素距離
    "gradient_search_bottom": 5,  # 往下搜尋的最大像素距離
    "keep_ratio": 0.3,           # 保留的寬度比例
    "window_size": 5,             # 平滑過濾視窗大小
    "threshold": 0.1,             # 平滑過濾閾值
}

# 線條顏色選擇
COLOR_MAPPINGS = {
    '綠色': (0, 255, 0),
    '紅色': (0, 0, 255),
    '藍色': (255, 0, 0),
    '白色': (255, 255, 255),
    '黃色': (0, 255, 255),
}

# 預設設定組合
DEFAULT_CONFIGS = {
    "系統預設": {
        "selected_model": DEFAULT_MODEL,
        "pixel_size_mm": PROCESSING_CONFIG["pixel_size_mm"],
        "confidence_threshold": YOLO_CONFIG["conf"],
        "sample_interval": LINE_EXTRACTION_CONFIG["sample_interval"],
        "gradient_search_top": LINE_EXTRACTION_CONFIG["gradient_search_top"],
        "gradient_search_bottom": LINE_EXTRACTION_CONFIG["gradient_search_bottom"],
        "keep_ratio": LINE_EXTRACTION_CONFIG["keep_ratio"],
        "line_thickness": VISUALIZATION_CONFIG["line_thickness"],
        "line_alpha": VISUALIZATION_CONFIG["line_alpha"],
        "display_labels": VISUALIZATION_CONFIG["display_labels"],
        "region_limit": VISUALIZATION_CONFIG["region_limit"],
        "line_color_option": "綠色",
    }
}