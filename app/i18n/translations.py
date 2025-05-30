from typing import TypedDict, Literal, Dict

class TranslationStrings(TypedDict):
    # Page and general
    page_title: str
    app_title: str
    app_description: str
    
    # Steps
    step1_title: str
    step2_title: str
    
    # Progress stages
    progress_loading: str
    progress_inference: str
    progress_drawing: str
    
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
    scale: str
    scale_help: str
    
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

LanguageCode = Literal["zh_TW", "en", "ru", "fr", "es", "ja", "ko", "de", "ar"]
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
        
        # Progress stages
        "progress_loading": "載入圖片中",
        "progress_inference": "AI分析中",
        "progress_drawing": "繪製測量線中",
        
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
        "scale": "縮放比例",
        "scale_help": "設定影像縮放倍數，以放大圖片並獲取更多細節。(線條會更細)",
        
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
        
        # Progress stages
        "progress_loading": "Loading Images in progress",
        "progress_inference": "AI Analysis in progress",
        "progress_drawing": "Drawing Measurement Lines in progress",
        
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
        "deviation_percent_help": "Set the percentage for grouping similar measurements. (0 to disable grouping)",
        "scale": "Scale",
        "scale_help": "Set the image scaling factor to enlarge the image and capture more detail.",
        
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
        
        # Messages
        "no_vessel_detected": "⚠️ No vessel detected in this image.",
        "no_valid_measurements": "⚠️ No valid measurements after filtering.",
        "processing_failed": "❌ Failed to process image: {}",
        
        # Other UI elements
        "processed_image": "Processed Image",
        "select_measurement": "Select Measurement",
        "selected_measurement": "Selected measurement: {:.2f} mm",
        
        # Results
        "results_title": "## Results",
        "confirm_results": "Confirm Measurements",
        "results_confirmed": "✓ Measurements Confirmed",
        "download_images": "📥 Download All Processed Images",
        "download_images_help": "Click to download all processed images as a ZIP file.",
        "download_excel": "📊 Download Results Excel",
        "download_excel_help": "Download measurement results as Excel file",
        "download_disabled_help": "Please confirm measurements first",
        "no_results": "No results to display.",
        "generating_report": "Generating report..."
    },
    "ru": {
        # Page and general
        "page_title": "🩺 Инструмент измерения сосудов v0.2",
        "app_title": "🩺 Инструмент измерения сосудов",
        "app_description": "🔍 Этот инструмент автоматически идентифицирует и измеряет длину сосудов на изображениях.",
        
        # Steps
        "step1_title": "## Шаг 1: Загрузка изображений",
        "step2_title": "## Шаг 2: Настройка параметров измерения",
        
        # Progress stages
        "progress_loading": "Загрузка изображений",
        "progress_inference": "Анализ ИИ",
        "progress_drawing": "Отрисовка линий измерения",
        
        # File operations
        "clear_results": "🗑️ Очистить результаты",
        "clear_results_help": "Очистить все результаты обработки",
        "upload_images": "Загрузите несколько изображений для измерения (Поддерживаемые форматы: JPG, PNG)",
        "upload_warning": "⚠️ Пожалуйста, загрузите хотя бы одно изображение.",
        
        # Parameters
        "basic_params": "### Основные параметры",
        "display_settings": "### Настройки отображения",
        "num_lines": "Количество вертикальных линий",
        "num_lines_help": "Установите количество вертикальных линий для измерения сосудов.",
        "line_width": "Ширина линии",
        "line_width_help": "Установите ширину линий сосудов.",
        "min_length": "Минимальная длина линии (мм)",
        "min_length_help": "Установите минимальную длину линий сосудов (миллиметры).",
        "max_length": "Максимальная длина линии (мм)",
        "max_length_help": "Установите максимальную длину линий сосудов (миллиметры).",
        "depth": "Глубина (см)",
        "depth_help": "Установите глубину сосудов (сантиметры).",
        "line_length_weight": "Вес длины линии",
        "line_length_weight_help": "Настройте вес длины линии в измерениях.",
        "deviation_threshold": "Порог отклонения (%)",
        "deviation_threshold_help": "Установите допустимый процент отклонения. Измерения вне этого диапазона будут отфильтрованы. (0 для отключения фильтрации)",
        "deviation_percent": "Процент группировки отклонений (%)",
        "deviation_percent_help": "Установите процент для группировки схожих измерений. (0 для отключения группировки)",
        "scale": "Масштаб",
        "scale_help": "Установите коэффициент масштабирования изображения, чтобы увеличить его и получить больше деталей.",
        
        # Colors
        "line_color": "Цвет линии",
        "line_color_help": "Выберите цвет для маркировки сосудов.",
        "color_green": "Зеленый",
        "color_red": "Красный",
        "color_blue": "Синий",
        "color_yellow": "Желтый",
        "color_white": "Белый",
        
        # Preset management
        "preset_management": "⚙️ Управление предустановками параметров",
        "preset_name": "Название предустановки",
        "preset_name_placeholder": "Введите название предустановки...",
        "preset_name_warning": "Пожалуйста, введите название предустановки",
        "save_params": "💾 Сохранить текущие параметры",
        "saved_presets": "### Сохраненные предустановки",
        "load_preset": "📥 Загрузить",
        "delete_preset": "🗑️ Удалить",
        
        # Processing
        "start_processing": "Начать измерение",
        "processing": "Обработка...",
        "processing_spinner": "Обработка изображений...",
        
        # Messages
        "no_vessel_detected": "⚠️ На этом изображении не обнаружено сосудов.",
        "no_valid_measurements": "⚠️ Нет действительных измерений после фильтрации.",
        "processing_failed": "❌ Не удалось обработать изображение: {}",
        
        # Other UI elements
        "processed_image": "Обработанное изображение",
        "select_measurement": "Выберите измерение",
        "selected_measurement": "Выбранное измерение: {:.2f} мм",
        
        # Results
        "results_title": "## Результаты",
        "confirm_results": "Подтвердить измерения",
        "results_confirmed": "✓ Измерения подтверждены",
        "download_images": "📥 Скачать все обработанные изображения",
        "download_images_help": "Нажмите, чтобы скачать все обработанные изображения в ZIP-архиве.",
        "download_excel": "📊 Скачать результаты в Excel",
        "download_excel_help": "Скачать результаты измерений в формате Excel",
        "download_disabled_help": "Сначала подтвердите измерения",
        "no_results": "Нет результатов для отображения.",
        "generating_report": "Создание отчета..."
    },
    "fr": {
        # Page and general
        "page_title": "🩺 Outil de mesure des vaisseaux v0.2",
        "app_title": "🩺 Outil de mesure des vaisseaux",
        "app_description": "🔍 Cet outil identifie et mesure automatiquement la longueur des vaisseaux dans les images.",
        
        # Steps
        "step1_title": "## Étape 1 : Télécharger des images",
        "step2_title": "## Étape 2 : Définir les paramètres de mesure",
        
        # Progress stages
        "progress_loading": "Chargement des images",
        "progress_inference": "Analyse IA",
        "progress_drawing": "Dessin des lignes de mesure",
        
        # File operations
        "clear_results": "🗑️ Effacer les résultats",
        "clear_results_help": "Effacer tous les résultats de traitement",
        "upload_images": "Télécharger plusieurs images pour la mesure (Formats supportés : JPG, PNG)",
        "upload_warning": "⚠️ Veuillez télécharger au moins une image.",
        
        # Parameters
        "basic_params": "### Paramètres de base",
        "display_settings": "### Paramètres d'affichage",
        "num_lines": "Nombre de lignes verticales",
        "num_lines_help": "Définir le nombre de lignes verticales pour la mesure des vaisseaux.",
        "line_width": "Largeur de ligne",
        "line_width_help": "Définir la largeur des lignes des vaisseaux.",
        "min_length": "Longueur minimale de ligne (mm)",
        "min_length_help": "Définir la longueur minimale des lignes des vaisseaux (millimètres).",
        "max_length": "Longueur maximale de ligne (mm)",
        "max_length_help": "Définir la longueur maximale des lignes des vaisseaux (millimètres).",
        "depth": "Profondeur (cm)",
        "depth_help": "Définir la profondeur des vaisseaux (centimètres).",
        "line_length_weight": "Poids de longitud de ligne",
        "line_length_weight_help": "Ajuster le poids de la longueur de ligne dans les mesures.",
        "deviation_threshold": "Seuil de déviation (%)",
        "deviation_threshold_help": "Définir le pourcentage de déviation acceptable. Les mesures hors de cette plage seront filtrées. (0 pour désactiver le filtrage)",
        "deviation_percent": "Pourcentage de regroupement des déviations (%)",
        "deviation_percent_help": "Définir le pourcentage pour grouper mesures similaires. (0 pour désactiver le regroupement)",
        "scale": "Échelle",
        "scale_help": "Définissez le facteur de mise à l’échelle de l’image pour l’agrandir et capturer davantage de détails.",

        # Colors
        "line_color": "Couleur de ligne",
        "line_color_help": "Choisir la couleur pour marquer les vaisseaux.",
        "color_green": "Vert",
        "color_red": "Rouge",
        "color_blue": "Bleu",
        "color_yellow": "Jaune",
        "color_white": "Blanc",
        
        # Preset management
        "preset_management": "⚙️ Gestion des préréglages",
        "preset_name": "Nom du préréglage",
        "preset_name_placeholder": "Entrer le nom du préréglage...",
        "preset_name_warning": "Veuillez entrer un nom de préréglage",
        "save_params": "💾 Sauvegarder les paramètres actuels",
        "saved_presets": "### Préréglages sauvegardés",
        "load_preset": "📥 Charger",
        "delete_preset": "🗑️ Supprimer",
        
        # Processing
        "start_processing": "Commencer la mesure",
        "processing": "Traitement...",
        "processing_spinner": "Traitement des images...",
        
        # Results
        "results_title": "## Résultats",
        "confirm_results": "Confirmer les mesures",
        "results_confirmed": "✓ Mesures confirmées",
        "download_images": "📥 Télécharger toutes les images traitées",
        "download_images_help": "Cliquer pour télécharger toutes les images traitées au format ZIP.",
        "download_excel": "📊 Télécharger les résultats Excel",
        "download_excel_help": "Télécharger les résultats des mesures au format Excel",
        "download_disabled_help": "Veuillez d'abord confirmer les mesures",
        "select_measurement": "Sélectionner la mesure",
        "selected_measurement": "Mesure sélectionnée : {:.2f} mm",
        "no_vessel_detected": "Aucun vaisseau détecté dans cette image",
        "processing_failed": "Échec du traitement : {}",
        "no_results": "Aucun résultat à afficher.",
        "generating_report": "Génération du rapport...",
        "processed_image": "Image traitée"
    },
    "es": {
        # Page and general
        "page_title": "🩺 Herramienta de medición de vasos v0.2",
        "app_title": "🩺 Herramienta de medición de vasos",
        "app_description": "🔍 Esta herramienta identifica y mide automáticamente la longitud de los vasos en las imágenes.",
        
        # Steps
        "step1_title": "## Paso 1: Subir imágenes",
        "step2_title": "## Paso 2: Establecer parámetros de medición",
        
        # Progress stages
        "progress_loading": "Cargando imágenes",
        "progress_inference": "Análisis de IA",
        "progress_drawing": "Dibujando líneas de medición",
        
        # File operations
        "clear_results": "🗑️ Borrar resultados",
        "clear_results_help": "Borrar todos los resultados del procesamiento",
        "upload_images": "Subir múltiples imágenes para medición (Formatos soportados: JPG, PNG)",
        "upload_warning": "⚠️ Por favor, suba al menos una imagen.",
        
        # Parameters
        "basic_params": "### Parámetros básicos",
        "display_settings": "### Ajustes de visualización",
        "num_lines": "Número de líneas verticales",
        "num_lines_help": "Establecer el número de líneas verticales para la medición de vasos.",
        "line_width": "Ancho de línea",
        "line_width_help": "Establecer el ancho de las líneas de los vasos.",
        "min_length": "Longitud mínima de línea (mm)",
        "min_length_help": "Establecer la longitud mínima de las líneas de los vasos (milímetros).",
        "max_length": "Longitud máxima de línea (mm)",
        "max_length_help": "Establecer la longitud máxima de las líneas de los vasos (milímetros).",
        "depth": "Profundidad (cm)",
        "depth_help": "Establecer la profundidad de los vasos (centímetros).",
        "line_length_weight": "Peso de longitud de línea",
        "line_length_weight_help": "Ajustar el peso de la longitud de línea en las mediciones.",
        "deviation_threshold": "Umbral de desviación (%)",
        "deviation_threshold_help": "Establecer el porcentaje de desviación aceptable. Las mediciones fuera de este rango serán filtradas. (0 para desactivar el filtrado)",
        "deviation_percent": "Porcentaje de agrupación de desviaciones (%)",
        "deviation_percent_help": "Establecer el porcentaje para agrupar mediciones similares. (0 para desactivar la agrupación)",
        "scale": "Escala",
        "scale_help": "Establezca el factor de escala de la imagen para ampliarla y capturar más detalles.",
        
        # Colors
        "line_color": "Color de línea",
        "line_color_help": "Elegir el color para marcar los vasos.",
        "color_green": "Verde",
        "color_red": "Rojo",
        "color_blue": "Azul",
        "color_yellow": "Amarillo",
        "color_white": "Blanco",
        
        # Preset management
        "preset_management": "⚙️ Gestión de preajustes",
        "preset_name": "Nombre del preajuste",
        "preset_name_placeholder": "Introducir nombre del preajuste...",
        "preset_name_warning": "Por favor, introduzca un nombre de preajuste",
        "save_params": "💾 Guardar parámetros actuales",
        "saved_presets": "### Preajustes guardados",
        "load_preset": "📥 Cargar",
        "delete_preset": "🗑️ Eliminar",
        
        # Processing
        "start_processing": "Comenzar medición",
        "processing": "Procesando...",
        "processing_spinner": "Procesando imágenes...",
        
        # Results
        "results_title": "## Resultados",
        "confirm_results": "Confirmar mediciones",
        "results_confirmed": "✓ Mediciones confirmadas",
        "download_images": "📥 Descargar todas las imágenes procesadas",
        "download_images_help": "Haga clic para descargar todas las imágenes procesadas en formato ZIP.",
        "download_excel": "📊 Descargar resultados Excel",
        "download_excel_help": "Descargar resultados de mediciones en formato Excel",
        "download_disabled_help": "Por favor, confirme primero las mediciones",
        "select_measurement": "Seleccionar medición",
        "selected_measurement": "Medición seleccionada: {:.2f} mm",
        "no_vessel_detected": "No se detectaron vasos en esta imagen",
        "processing_failed": "Error en el procesamiento: {}",
        "no_results": "No hay resultados para mostrar.",
        "generating_report": "Generando informe...",
        "processed_image": "Imagen procesada"
    },
    "ja": {
        # Page and general
        "page_title": "🩺 血管測定ツール v0.2",
        "app_title": "🩺 血管測定ツール",
        "app_description": "🔍 このツールは画像内の血管の長さを自動的に識別し測定します。",
        
        # Steps
        "step1_title": "## ステップ 1: 画像のアップロード",
        "step2_title": "## ステップ 2: 測定パラメータの設定",
        
        # Progress stages
        "progress_loading": "画像の読み込み中",
        "progress_inference": "AI分析中",
        "progress_drawing": "測定線の描画中",
        
        # File operations
        "clear_results": "🗑️ 結果をクリア",
        "clear_results_help": "すべての処理結果をクリアします",
        "upload_images": "測定する画像をアップロード（対応形式：JPG, PNG）",
        "upload_warning": "⚠️ 少なくとも1枚の画像をアップロードしてください。",
        
        # Parameters
        "basic_params": "### 基本パラメータ",
        "display_settings": "### 表示設定",
        "num_lines": "垂直線の数",
        "num_lines_help": "血管測定用の垂直線の数を設定します。",
        "line_width": "線の幅",
        "line_width_help": "血管線の幅を設定します。",
        "min_length": "最小線長 (mm)",
        "min_length_help": "血管線の最小長さを設定します（ミリメートル）。",
        "max_length": "最大線長 (mm)",
        "max_length_help": "血管線の最大長さを設定します（ミリメートル）。",
        "depth": "深さ (cm)",
        "depth_help": "血管の深さを設定します（センチメートル）。",
        "line_length_weight": "線長の重み",
        "line_length_weight_help": "測定における線長の重みを調整します。",
        "deviation_threshold": "偏差閾値 (%)",
        "deviation_threshold_help": "許容される偏差範囲の割合を設定します。この範囲外の測定値はフィルタリングされます。(0でフィルタリング無効)",
        "deviation_percent": "グループ化偏差割合 (%)",
        "deviation_percent_help": "類似の測定値をグループ化する割合を設定します。(0でグループ化無効)",
        "scale": "拡大率",
        "scale_help": "画像を拡大して詳細を取得するための倍率を設定します。",

        
        # Colors
        "line_color": "線の色",
        "line_color_help": "血管をマークする色を選択します。",
        "color_green": "緑",
        "color_red": "赤",
        "color_blue": "青",
        "color_yellow": "黄",
        "color_white": "白",
        
        # Preset management
        "preset_management": "⚙️ パラメータプリセット管理",
        "preset_name": "プリセット名",
        "preset_name_placeholder": "プリセット名を入力...",
        "preset_name_warning": "プリセット名を入力してください",
        "save_params": "💾 現在のパラメータを保存",
        "saved_presets": "### 保存済みプリセット",
        "load_preset": "📥 読み込み",
        "delete_preset": "🗑️ 削除",
        
        # Processing
        "start_processing": "測定開始",
        "processing": "処理中...",
        "processing_spinner": "画像を処理中...",
        
        # Results
        "results_title": "## 結果",
        "confirm_results": "測定結果を確認",
        "results_confirmed": "✓ 測定結果を確認済み",
        "download_images": "📥 処理済み画像をすべてダウンロード",
        "download_images_help": "クリックして処理済み画像をZIPファイルでダウンロードします。",
        "download_excel": "📊 Excel結果をダウンロード",
        "download_excel_help": "測定結果をExcel形式でダウンロード",
        "download_disabled_help": "先に測定結果を確認してください",
        "select_measurement": "測定値を選択",
        "selected_measurement": "選択された測定値: {:.2f} mm",
        "no_vessel_detected": "この画像では血管が検出されませんでした",
        "processing_failed": "処理に失敗しました: {}",
        "no_results": "表示する結果がありません。",
        "generating_report": "レポート生成中...",
        "processed_image": "処理済み画像"
    },
    "ko": {
        # Page and general
        "page_title": "🩺 혈관 측정 도구 v0.2",
        "app_title": "🩺 혈관 측정 도구",
        "app_description": "🔍 이 도구는 이미지에서 혈관의 길이를 자동으로 식별하고 측정합니다.",
        
        # Steps
        "step1_title": "## 단계 1: 이미지 업로드",
        "step2_title": "## 단계 2: 측정 매개변수 설정",
        
        # Progress stages
        "progress_loading": "이미지 로딩 중",
        "progress_inference": "AI 분석 중",
        "progress_drawing": "측정선 그리기 중",
        
        # File operations
        "clear_results": "🗑️ 결과 지우기",
        "clear_results_help": "모든 처리 결과를 지웁니다",
        "upload_images": "측정할 여러 이미지 업로드 (지원 형식: JPG, PNG)",
        "upload_warning": "⚠️ 최소 한 개의 이미지를 업로드해 주세요.",
        
        # Parameters
        "basic_params": "### 기본 매개변수",
        "display_settings": "### 표시 설정",
        "num_lines": "수직선 개수",
        "num_lines_help": "혈관 측정을 위한 수직선의 개수를 설정합니다.",
        "line_width": "선 너비",
        "line_width_help": "혈관 선의 너비를 설정합니다.",
        "min_length": "최소 선 길이 (mm)",
        "min_length_help": "혈관 선의 최소 길이를 설정합니다(밀리미터).",
        "max_length": "최대 선 길이 (mm)",
        "max_length_help": "혈관 선의 최대 길이를 설정합니다(밀리미터).",
        "depth": "깊이 (cm)",
        "depth_help": "혈관의 깊이를 설정합니다(센티미터).",
        "line_length_weight": "선 길이 가중치",
        "line_length_weight_help": "측정에서 선 길이의 가중치를 조정합니다.",
        "deviation_threshold": "편차 임계값 (%)",
        "deviation_threshold_help": "허용 가능한 편차 범위의 백분율을 설정합니다. 이 범위를 벗어난 측정값은 필터링됩니다. (0은 필터링 비활성화)",
        "deviation_percent": "그룹화 편차 백분율 (%)",
        "deviation_percent_help": "유사한 측정값을 그룹화하기 위한 백분율을 설정합니다. (0은 그룹화 비활성화)",
        "scale": "배율",
        "scale_help": "이미지를 확대하여 더 많은 세부 정보를 캡처하기 위한 배율을 설정합니다.",
        
        # Colors
        "line_color": "선 색상",
        "line_color_help": "혈관을 표시할 색상을 선택합니다.",
        "color_green": "녹색",
        "color_red": "빨간색",
        "color_blue": "파란색",
        "color_yellow": "노란색",
        "color_white": "흰색",
        
        # Preset management
        "preset_management": "⚙️ 매개변수 프리셋 관리",
        "preset_name": "프리셋 이름",
        "preset_name_placeholder": "프리셋 이름 입력...",
        "preset_name_warning": "프리셋 이름을 입력해 주세요",
        "save_params": "💾 현재 매개변수 저장",
        "saved_presets": "### 저장된 프리셋",
        "load_preset": "📥 불러오기",
        "delete_preset": "🗑️ 삭제",
        
        # Processing
        "start_processing": "측정 시작",
        "processing": "처리 중...",
        "processing_spinner": "이미지 처리 중...",
        
        # Results
        "results_title": "## 결과",
        "confirm_results": "측정 결과 확인",
        "results_confirmed": "✓ 측정 결과 확인됨",
        "download_images": "📥 모든 처리된 이미지 다운로드",
        "download_images_help": "클릭하여 모든 처리된 이미지를 ZIP 파일로 다운로드합니다.",
        "download_excel": "📊 Excel 결과 다운로드",
        "download_excel_help": "측정 결과를 Excel 형식으로 다운로드",
        "download_disabled_help": "먼저 측정 결과를 확인해 주세요",
        "select_measurement": "측정값 선택",
        "selected_measurement": "선택된 측정값: {:.2f} mm",
        "no_vessel_detected": "이 이미지에서 혈관이 감지되지 않았습니다",
        "processing_failed": "처리 실패: {}",
        "no_results": "표시할 결과가 없습니다.",
        "generating_report": "보고서 생성 중...",
        "processed_image": "처리된 이미지"
    },
    "de": {
        # Page and general
        "page_title": "🩺 Gefäßmesswerkzeug v0.2",
        "app_title": "🩺 Gefäßmesswerkzeug",
        "app_description": "🔍 Dieses Tool identifiziert und misst automatisch die Länge von Gefäßen in Bildern.",
        
        # Steps
        "step1_title": "## Schritt 1: Bilder hochladen",
        "step2_title": "## Schritt 2: Messparameter einstellen",
        
        # Progress stages
        "progress_loading": "Bilder werden geladen",
        "progress_inference": "KI-Analyse läuft",
        "progress_drawing": "Messlinien werden gezeichnet",
        
        # File operations
        "clear_results": "🗑️ Ergebnisse löschen",
        "clear_results_help": "Alle Verarbeitungsergebnisse löschen",
        "upload_images": "Mehrere Bilder zur Messung hochladen (Unterstützte Formate: JPG, PNG)",
        "upload_warning": "⚠️ Bitte laden Sie mindestens ein Bild hoch.",
        
        # Parameters
        "basic_params": "### Grundparameter",
        "display_settings": "### Anzeigeeinstellungen",
        "num_lines": "Anzahl vertikaler Linien",
        "num_lines_help": "Legen Sie die Anzahl der vertikalen Linien für die Gefäßmessung fest.",
        "line_width": "Linienbreite",
        "line_width_help": "Legen Sie die Breite der Gefäßlinien fest.",
        "min_length": "Minimale Linienlänge (mm)",
        "min_length_help": "Legen Sie die minimale Länge der Gefäßlinien fest (Millimeter).",
        "max_length": "Maximale Linienlänge (mm)",
        "max_length_help": "Legen Sie die maximale Länge der Gefäßlinien fest (Millimeter).",
        "depth": "Tiefe (cm)",
        "depth_help": "Legen Sie die Gefäßtiefe fest (Zentimeter).",
        "line_length_weight": "Linienlängengewichtung",
        "line_length_weight_help": "Passen Sie die Gewichtung der Linienlänge in den Messungen an.",
        "deviation_threshold": "Abweichungsschwelle (%)",
        "deviation_threshold_help": "Legen Sie den akzeptablen Abweichungsprozentsatz fest. Messungen außerhalb dieses Bereichs werden gefiltert. (0 zum Deaktivieren der Filterung)",
        "deviation_percent": "Gruppierungsabweichung (%)",
        "deviation_percent_help": "Legen Sie den Prozentsatz für die Gruppierung ähnlicher Messungen fest. (0 zum Deaktivieren der Gruppierung)",
        "scale": "Skalierung",
        "scale_help": "Legen Sie den Skalierungsfaktor fest, um das Bild zu vergrößern und mehr Details zu erfassen.",
        
        # Colors
        "line_color": "Linienfarbe",
        "line_color_help": "Wählen Sie die Farbe für die Markierung der Gefäße.",
        "color_green": "Grün",
        "color_red": "Rot",
        "color_blue": "Blau",
        "color_yellow": "Gelb",
        "color_white": "Weiß",
        
        # Preset management
        "preset_management": "⚙️ Parametervorgaben verwalten",
        "preset_name": "Name der Vorgabe",
        "preset_name_placeholder": "Name der Vorgabe eingeben...",
        "preset_name_warning": "Bitte geben Sie einen Namen für die Vorgabe ein",
        "save_params": "💾 Aktuelle Parameter speichern",
        "saved_presets": "### Gespeicherte Vorgaben",
        "load_preset": "📥 Laden",
        "delete_preset": "🗑️ Löschen",
        
        # Processing
        "start_processing": "Messung starten",
        "processing": "Verarbeitung...",
        "processing_spinner": "Bilder werden verarbeitet...",
        
        # Results
        "results_title": "## Ergebnisse",
        "confirm_results": "Messungen bestätigen",
        "results_confirmed": "✓ Messungen bestätigt",
        "download_images": "📥 Alle verarbeiteten Bilder herunterladen",
        "download_images_help": "Klicken Sie hier, um alle verarbeiteten Bilder als ZIP-Datei herunterzuladen.",
        "download_excel": "📊 Excel-Ergebnisse herunterladen",
        "download_excel_help": "Messergebnisse im Excel-Format herunterladen",
        "download_disabled_help": "Bitte bestätigen Sie zuerst die Messungen",
        "select_measurement": "Messung auswählen",
        "selected_measurement": "Ausgewählte Messung: {:.2f} mm",
        "no_vessel_detected": "In diesem Bild wurden keine Gefäße erkannt",
        "processing_failed": "Verarbeitung fehlgeschlagen: {}",
        "no_results": "Keine Ergebnisse zum Anzeigen.",
        "generating_report": "Bericht wird erstellt...",
        "processed_image": "Verarbeitetes Bild"
    },
    "ar": {
        # Page and general
        "page_title": "🩺 أداة قياس الأوعية الدموية v0.2",
        "app_title": "🩺 أداة قياس الأوعية الدموية",
        "app_description": "🔍 تقوم هذه الأداة تلقائياً بتحديد وقياس أطوال الأوعية الدموية في الصور.",
        
        # Steps
        "step1_title": "## الخطوة 1: تحميل الصور",
        "step2_title": "## الخطوة 2: تعيين معايير القياس",
        
        # Progress stages
        "progress_loading": "جاري تحميل الصور",
        "progress_inference": "تحليل الذكاء الاصطناعي",
        "progress_drawing": "رسم خطوط القياس",
        
        # File operations
        "clear_results": "🗑️ مسح النتائج",
        "clear_results_help": "مسح جميع نتائج المعالجة",
        "upload_images": "تحميل صور متعددة للقياس (الصيغ المدعومة: JPG, PNG)",
        "upload_warning": "⚠️ يرجى تحميل صورة واحدة على الأقل.",
        
        # Parameters
        "basic_params": "### المعايير الأساسية",
        "display_settings": "### إعدادات العرض",
        "num_lines": "عدد الخطوط العمودية",
        "num_lines_help": "تعيين عدد الخطوط العمودية لقياس الأوعية الدموية.",
        "line_width": "عرض الخط",
        "line_width_help": "تعيين عرض خطوط الأوعية الدموية.",
        "min_length": "الحد الأدنى لطول الخط (مم)",
        "min_length_help": "تعيين الحد الأدنى لطول خطوط الأوعية الدموية (بالمليمتر).",
        "max_length": "الحد الأقصى لطول الخط (مم)",
        "max_length_help": "تعيين الحد الأقصى لطول خطوط الأوعية الدموية (بالمليمتر).",
        "depth": "العمق (سم)",
        "depth_help": "تعيين عمق الأوعية الدموية (بالسنتيمتر).",
        "line_length_weight": "وزن طول الخط",
        "line_length_weight_help": "ضبط وزن طول الخط في القياسات.",
        "deviation_threshold": "عتبة الانحراف (%)",
        "deviation_threshold_help": "تعيين نسبة الانحراف المقبولة. سيتم تصفية القياسات خارج هذا النطاق. (0 لتعطيل التصفية)",
        "deviation_percent": "نسبة تجميع الانحرافات (%)",
        "deviation_percent_help": "تعيين النسبة المئوية لتجميع القياسات المتشابهة. (0 لتعطيل التجميع)",
        "scale": "مقياس",
        "scale_help": "قم بتعيين عامل مقياس الصورة لتكبيرها والحصول على مزيد من التفاصيل.",

        
        # Colors
        "line_color": "لون الخط",
        "line_color_help": "اختيار لون لتمييز الأوعية الدموية.",
        "color_green": "أخضر",
        "color_red": "أحمر",
        "color_blue": "أزرق",
        "color_yellow": "أصفر",
        "color_white": "أبيض",
        
        # Preset management
        "preset_management": "⚙️ إدارة الإعدادات المسبقة",
        "preset_name": "اسم الإعداد المسبق",
        "preset_name_placeholder": "أدخل اسم الإعداد المسبق...",
        "preset_name_warning": "يرجى إدخال اسم للإعداد المسبق",
        "save_params": "💾 حفظ المعايير الحالية",
        "saved_presets": "### الإعدادات المسبقة المحفوظة",
        "load_preset": "📥 تحميل",
        "delete_preset": "🗑️ حذف",
        
        # Processing
        "start_processing": "بدء القياس",
        "processing": "جاري المعالجة...",
        "processing_spinner": "جاري معالجة الصور...",
        
        # Results
        "results_title": "## النتائج",
        "confirm_results": "تأكيد القياسات",
        "results_confirmed": "✓ تم تأكيد القياسات",
        "download_images": "📥 تحميل جميع الصور المعالجة",
        "download_images_help": "انقر لتحميل جميع الصور المعالجة كملف ZIP.",
        "download_excel": "📊 تحميل نتائج Excel",
        "download_excel_help": "تحميل نتائج القياسات بتنسيق Excel",
        "download_disabled_help": "يرجى تأكيد القياسات أولاً",
        "select_measurement": "اختيار القياس",
        "selected_measurement": "القياس المحدد: {:.2f} مم",
        "no_vessel_detected": "لم يتم اكتشاف أوعية دموية في هذه الصورة",
        "processing_failed": "فشلت المعالجة: {}",
        "no_results": "لا توجد نتائج للعرض.",
        "generating_report": "جاري إنشاء التقرير...",
        "processed_image": "الصورة المعالجة"
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