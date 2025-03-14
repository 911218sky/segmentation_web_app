from typing import TypedDict, Literal, Dict

class TranslationStrings(TypedDict):
    # Page and general
    page_title: str
    app_title: str
    app_description: str
    
    # Steps
    step1_title: str
    step2_title: str
    
    # File operations
    clear_results: str
    clear_results_help: str
    upload_images: str
    upload_warning: str
    
    # Parameters
    basic_params: str
    display_settings: str
    num_lines: str
    num_lines_help: str
    line_width: str
    line_width_help: str
    min_length: str
    min_length_help: str
    max_length: str
    max_length_help: str
    depth: str
    depth_help: str
    line_length_weight: str
    line_length_weight_help: str
    deviation_threshold: str
    deviation_threshold_help: str
    deviation_percent: str
    deviation_percent_help: str
    
    # Colors
    line_color: str
    line_color_help: str
    color_green: str
    color_red: str
    color_blue: str
    color_yellow: str
    color_white: str
    
    # Preset management
    preset_management: str
    preset_name: str
    preset_name_placeholder: str
    preset_name_warning: str
    save_params: str
    saved_presets: str
    load_preset: str
    delete_preset: str
    
    # Processing
    start_processing: str
    processing: str
    processing_spinner: str
    
    # Results
    results_title: str
    confirm_results: str
    results_confirmed: str
    download_images: str
    download_images_help: str
    download_excel: str
    download_excel_help: str
    download_disabled_help: str
    select_measurement: str
    selected_measurement: str
    no_vessel_detected: str
    processing_failed: str
    no_results: str
    generating_report: str
    processed_image: str

LanguageCode = Literal["zh_TW", "en"]
Translations = Dict[LanguageCode, TranslationStrings]

TRANSLATIONS: Translations = {
    "zh_TW": {
        # Page and general
        "page_title": "🩺 血管測量工具 v0.2",
        "app_title": "🩺 血管測量工具",
        "app_description": "🔍 此工具可以自動識別並測量圖片中的血管長度。",
        
        # Steps
        "step1_title": "## 步驟 1: 上傳圖片",
        "step2_title": "## 步驟 2: 設定測量參數",
        
        # File operations
        "clear_results": "🗑️ 清空結果",
        "clear_results_help": "清空所有處理結果",
        "upload_images": "上傳多張圖片進行測量（支援格式：JPG, PNG）",
        "upload_warning": "⚠️ 請上傳至少一張圖片。",
        
        # Parameters
        "basic_params": "### 基本參數",
        "display_settings": "### 顯示設定",
        "num_lines": "垂直線的數量",
        "num_lines_help": "設定圖片中垂直線的數量，用於血管的測量。",
        "line_width": "線條寬度",
        "line_width_help": "設定血管線條的寬度。",
        "min_length": "最小線條長度 (mm)",
        "min_length_help": "設定血管線條的最小長度（毫米）。",
        "max_length": "最大線條長度 (mm)",
        "max_length_help": "設定血管線條的最大長度（毫米）。",
        "depth": "深度 (cm)",
        "depth_help": "設定血管深度（厘米）。",
        "line_length_weight": "調整線條長度權重",
        "line_length_weight_help": "調整線條長度在測量中的權重。",
        "deviation_threshold": "誤差閾值 (%)",
        "deviation_threshold_help": "設定可接受的誤差範圍百分比，超出此範圍的測量值將被過濾。(0 代表關閉過濾)",
        "deviation_percent": "分組差距百分比 (%)",
        "deviation_percent_help": "設定分組差距百分比，用於將相似長度的線條分組。(0 代表關閉分組)",
        
        # Colors
        "line_color": "線條顏色",
        "line_color_help": "選擇標記血管的線條顏色。",
        "color_green": "綠色",
        "color_red": "紅色",
        "color_blue": "藍色",
        "color_yellow": "黃色",
        "color_white": "白色",
        
        # Preset management
        "preset_management": "⚙️ 參數預設值管理",
        "preset_name": "預設值名稱",
        "preset_name_placeholder": "輸入預設值名稱...",
        "preset_name_warning": "請輸入預設值名稱",
        "save_params": "💾 保存當前參數",
        "saved_presets": "### 已保存的預設值",
        "load_preset": "📥 載入",
        "delete_preset": "🗑️ 刪除",
        
        # Processing
        "start_processing": "開始測量",
        "processing": "處理中...",
        "processing_spinner": "正在處理圖片...",
        
        # Results
        "results_title": "## 處理結果",
        "confirm_results": "確認測量結果",
        "results_confirmed": "✓ 已確認測量結果",
        "download_images": "📥 下載所有處理後的圖片",
        "download_images_help": "點擊此按鈕下載所有處理後的圖片壓縮包。",
        "download_excel": "📊 下載測量結果 Excel",
        "download_excel_help": "下載所有圖片的測量結果為Excel檔案",
        "download_disabled_help": "請先確認測量結果才能下載",
        "select_measurement": "選擇測量值",
        "selected_measurement": "選擇的測量值: {:.2f} mm",
        "no_vessel_detected": "未測量到血管",
        "processing_failed": "處理失敗: {}",
        "no_results": "沒有可顯示的處理結果。",
        "generating_report": "正在生成報告...",
        "processed_image": "處理後的圖像"
    },
    "en": {
        # Page and general
        "page_title": "🩺 Vessel Measurement Tool v0.2",
        "app_title": "🩺 Vessel Measurement Tool",
        "app_description": "🔍 This tool automatically identifies and measures vessel lengths in images.",
        
        # Steps
        "step1_title": "## Step 1: Upload Images",
        "step2_title": "## Step 2: Set Measurement Parameters",
        
        # File operations
        "clear_results": "🗑️ Clear Results",
        "clear_results_help": "Clear all processing results",
        "upload_images": "Upload multiple images for measurement (Supported formats: JPG, PNG)",
        "upload_warning": "⚠️ Please upload at least one image.",
        
        # Parameters
        "basic_params": "### Basic Parameters",
        "display_settings": "### Display Settings",
        "num_lines": "Number of Vertical Lines",
        "num_lines_help": "Set the number of vertical lines for vessel measurement.",
        "line_width": "Line Width",
        "line_width_help": "Set the width of vessel lines.",
        "min_length": "Minimum Line Length (mm)",
        "min_length_help": "Set the minimum length of vessel lines (millimeters).",
        "max_length": "Maximum Line Length (mm)",
        "max_length_help": "Set the maximum length of vessel lines (millimeters).",
        "depth": "Depth (cm)",
        "depth_help": "Set the vessel depth (centimeters).",
        "line_length_weight": "Line Length Weight",
        "line_length_weight_help": "Adjust the weight of line length in measurements.",
        "deviation_threshold": "Deviation Threshold (%)",
        "deviation_threshold_help": "Set acceptable deviation range percentage. Measurements outside this range will be filtered. (0 to disable filtering)",
        "deviation_percent": "Grouping Deviation Percentage (%)",
        "deviation_percent_help": "Set grouping deviation percentage for similar length lines. (0 to disable grouping)",
        
        # Colors
        "line_color": "Line Color",
        "line_color_help": "Choose the color for marking vessels.",
        "color_green": "Green",
        "color_red": "Red",
        "color_blue": "Blue",
        "color_yellow": "Yellow",
        "color_white": "White",
        
        # Preset management
        "preset_management": "⚙️ Parameter Preset Management",
        "preset_name": "Preset Name",
        "preset_name_placeholder": "Enter preset name...",
        "preset_name_warning": "Please enter a preset name",
        "save_params": "💾 Save Current Parameters",
        "saved_presets": "### Saved Presets",
        "load_preset": "📥 Load",
        "delete_preset": "🗑️ Delete",
        
        # Processing
        "start_processing": "Start Measurement",
        "processing": "Processing...",
        "processing_spinner": "Processing images...",
        
        # Results
        "results_title": "## Results",
        "confirm_results": "Confirm Measurements",
        "results_confirmed": "✓ Measurements Confirmed",
        "download_images": "📥 Download All Processed Images",
        "download_images_help": "Click to download all processed images as a ZIP file.",
        "download_excel": "📊 Download Results Excel",
        "download_excel_help": "Download measurement results as Excel file",
        "download_disabled_help": "Please confirm measurements first",
        "select_measurement": "Select Measurement",
        "selected_measurement": "Selected measurement: {:.2f} mm",
        "no_vessel_detected": "No vessel detected",
        "processing_failed": "Processing failed: {}",
        "no_results": "No results to display.",
        "generating_report": "Generating report...",
        "processed_image": "Processed image"
    }
}

# 自動檢查翻譯是否完整
def check_translations() -> None:
    missing_translations = []
    for lang, translations in TRANSLATIONS.items():
        for key in TranslationStrings.__annotations__:
            if key not in translations:
                missing_translations.append(f"Missing translation for key: {key} in language: {lang}")
    if missing_translations:
        raise ValueError("\n".join(missing_translations))
            
check_translations()