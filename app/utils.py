import cv2
import numpy as np
import tempfile
from pathlib import Path
from typing import Union
from PIL import Image

from config import *
from line_extractor import LineExtractor
from visualizer import Visualizer
from yolo_predictor import YOLOPredictor

def process_batch_images(
    predictor: YOLOPredictor,
    images,
    pixel_size_mm: float = 0.30,
    conf_threshold: float = 0.25, 
    line_config: Union[dict, None] = None,
    vis_config: Union[dict, None] = None):
    """批次處理多張圖片"""
    if line_config is None:
        line_config = LINE_EXTRACTION_CONFIG.copy()
    if vis_config is None:
        vis_config = VISUALIZATION_CONFIG.copy()
    
    results = []
    batch_size = BATCH_SIZE
    
    # 獲取 yolo 配置 並覆蓋 conf 參數
    yolo_config = YOLO_CONFIG.copy()
    yolo_config['conf'] = conf_threshold
    
    # 將圖片分批處理
    for i in range(0, len(images), batch_size):
        batch = images[i:i+batch_size]
        batch_temp_paths = []
        
        try:
            # 準備批次圖片的臨時檔案
            for j, (filename, image) in enumerate(batch):
                # 將 PIL 圖片轉換為 OpenCV 格式
                if isinstance(image, Image.Image):
                    image_array = np.array(image)
                    if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                        image_cv = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
                    else:
                        image_cv = image_array
                
                # 創建臨時檔案
                tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
                cv2.imwrite(tmp_file.name, image_cv)
                batch_temp_paths.append((tmp_file.name, filename, image, image_cv))
            
            # 批次預測
            temp_paths = [path for path, _, _, _ in batch_temp_paths]
            if len(temp_paths) == 1:
                yolo_results = predictor.predict(
                    temp_paths[0],
                    **yolo_config,
                )
            else:
                # 處理多個檔案
                yolo_results = []
                for temp_path in temp_paths:
                    result = predictor.predict(
                        temp_path,
                        **yolo_config,
                    )
                    yolo_results.extend(result if isinstance(result, list) else [result])
            
            # 處理批次結果
            for idx, (temp_path, filename, original_image, image_cv) in enumerate(batch_temp_paths):
                try:
                    if idx < len(yolo_results):
                        result = yolo_results[idx]
                        bbox, confidence, mask = predictor.extract_max_confidence_segment(result)
                        
                        if mask is not None:
                            # 提取垂直線 - 使用配置參數
                            line_extractor = LineExtractor()
                            vertical_lines = line_extractor.extract_vertical_lines_from_mask(
                                img=image_cv,
                                mask=mask,
                                sample_interval=line_config['sample_interval'],
                                gradient_search_top=line_config['gradient_search_top'],
                                gradient_search_bottom=line_config['gradient_search_bottom'],
                                keep_ratio=line_config['keep_ratio']
                            )
                            
                            # 視覺化 - 使用配置參數
                            visualizer = Visualizer()
                            final_image = visualizer.visualize_vertical_lines_with_mm(
                                image_cv,
                                vertical_lines,
                                pixel_size_mm=pixel_size_mm,
                                line_color=vis_config['line_color'],
                                line_thickness=vis_config['line_thickness'],
                                line_alpha=vis_config['line_alpha'],
                            )
                            
                            # 計算統計數據
                            lengths_mm = [abs(y2 - y1) * pixel_size_mm for _, y1, y2 in vertical_lines]
                            stats = {
                                'confidence': confidence,
                                'num_lines': len(vertical_lines),
                                'mean_length': np.mean(lengths_mm) if lengths_mm else 0,
                                'std_length': np.std(lengths_mm) if lengths_mm else 0,
                                'max_length': np.max(lengths_mm) if lengths_mm else 0,
                                'min_length': np.min(lengths_mm) if lengths_mm else 0
                            }
                            
                            # 轉換回 PIL 格式
                            result_image_rgb = cv2.cvtColor(final_image, cv2.COLOR_BGR2RGB)
                            result_pil = Image.fromarray(result_image_rgb)
                            
                            results.append({
                                'filename': filename,
                                'result': result_pil,
                                'stats': stats,
                                'success': True
                            })
                        else:
                            results.append({
                                'filename': filename,
                                'result': None,
                                'stats': {'error': '未檢測到分割遮罩'},
                                'success': False
                            })
                    else:
                        results.append({
                            'filename': filename,
                            'result': None,
                            'stats': {'error': '預測失敗'},
                            'success': False
                        })
                        
                except Exception as e:
                    results.append({
                        'filename': filename,
                        'result': None,
                        'stats': {'error': f'處理錯誤: {str(e)}'},
                        'success': False
                    })
                
        finally:
            # 清理臨時檔案
            for temp_path, _, _, _ in batch_temp_paths:
                try:
                    Path(temp_path).unlink()
                except:
                    pass
    
    return results