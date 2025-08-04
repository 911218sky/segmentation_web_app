import cv2
import numpy as np
import shutil
from typing import List, Tuple, Union
from PIL import Image

from utils.image_utils import batch_resize_with_cleanup, convert_pil_to_temp_files
from config import (
    BATCH_SIZE,
    TARGET_SIZE,
    LINE_EXTRACTION_CONFIG,
    VISUALIZATION_CONFIG,
    YOLO_CONFIG,
)
from line_extractor import LineExtractor
from visualizer import Visualizer
from yolo_predictor import YOLOPredictor


def process_batch_images(
    predictor: YOLOPredictor,
    images: List[Tuple[str, Image.Image]],
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
        image_files = []
        cleanup_temp_files = None
        cleanup_resize = None
        
        try:
            image_files_temp, cleanup_temp_files = convert_pil_to_temp_files(batch)
            
            # 統一大小
            image_files, info_list, cleanup_resize = batch_resize_with_cleanup(
                image_files_temp, 
                target_size=TARGET_SIZE
            )
            
            # 獲取資料夾路徑
            temp_dir = image_files[0].parent
            
            # 批次預測
            yolo_results = predictor.predict(
                temp_dir,
                **yolo_config,
            )
            yolo_results = [result for result in yolo_results if result is not None]
            
            # 處理批次結果
            for idx, image_file in enumerate(image_files):
                try:
                    if idx < len(yolo_results):
                        result = yolo_results[idx]
                        # 原始圖片檔名
                        filename = images[idx][0]
                        bbox, confidence, mask = predictor.extract_max_confidence_segment(result)
                        
                        if mask is not None:
                            img = cv2.imread(image_file)
                            
                            # 提取垂直線 - 使用配置參數
                            line_extractor = LineExtractor()
                            vertical_lines = line_extractor.extract_vertical_lines_from_mask(
                                img=img,
                                mask=mask,
                                sample_interval=line_config['sample_interval'],
                                gradient_search_top=line_config['gradient_search_top'],
                                gradient_search_bottom=line_config['gradient_search_bottom'],
                                keep_ratio=line_config['keep_ratio']
                            )
                            
                            # 視覺化 - 使用配置參數
                            visualizer = Visualizer()
                            final_image = visualizer.visualize_vertical_lines_with_mm(
                                img,
                                vertical_lines,
                                pixel_size_mm=pixel_size_mm,
                                line_color=vis_config['line_color'],
                                line_thickness=vis_config['line_thickness'],
                                line_alpha=vis_config['line_alpha'],
                                display_labels=vis_config['display_labels'],
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
                
        except Exception as e:
            # 如果整個批次失敗，為該批次的所有圖片添加錯誤結果
            for image_path in image_files_temp:
                results.append({
                    'filename': image_path.name,
                    'result': None,
                    'stats': {'error': f'批次處理錯誤: {str(e)}'},
                    'success': False
                })
        finally:
            if cleanup_temp_files is not None:
                try:
                    cleanup_temp_files()
                except Exception as e:
                    print(f"清理臨時檔案時發生錯誤: {e}")
            if cleanup_resize is not None:
                try:
                    cleanup_resize()
                except Exception as e:
                    print(f"清理臨時目錄時發生錯誤: {e}")
    
    return results