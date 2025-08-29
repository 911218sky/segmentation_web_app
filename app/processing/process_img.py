import cv2
import numpy as np
from typing import List, Tuple, Union, Optional, Dict, Any
from PIL import Image
import math

from utils.image import batch_uniform_resize
from utils.canvas import convert_original_xywh_to_resized
from config import (
    BATCH_SIZE,
    TARGET_SIZE,
    LINE_CONFIG,
    VISUALIZATION_CONFIG,
    YOLO_CONFIG,
)
from utils.line_extractor import LineExtractor
from utils.visualizer import Visualizer
from utils.yolo_predictor import YOLOPredictor

def process_batch_images(
    predictor: YOLOPredictor,
    images: List[Tuple[str, Image.Image]],
    pixel_size_mm: float = 0.30,
    conf_threshold: float = 0.25,
    # (x, y, w, h)
    region: Optional[Tuple[int, int, int, int]] = None,
    line_config: Union[dict, None] = None,
    vis_config: Union[dict, None] = None):
    """批次處理多張圖片"""
    if line_config is None:
        line_config = LINE_CONFIG.copy()
    if vis_config is None:
        vis_config = VISUALIZATION_CONFIG.copy()
     
    extractor = LineExtractor()
    visualizer = Visualizer()
    
    results = []
    
    # 獲取 yolo 配置 並覆蓋 conf 參數
    yolo_config = YOLO_CONFIG.copy()
    yolo_config['conf'] = conf_threshold
    
    results: List[Dict[str, Any]] = []
    
    n = len(images)
    total_batches = math.ceil(n / BATCH_SIZE)
    

    # 如果提供了 region（原始座標系），先轉到 resized 座標系
    if region is not None:
        # 假設所有圖都一樣大小，取第一張原始尺寸
        orig_w, orig_h = images[0][1].size
        region = convert_original_xywh_to_resized(region, (orig_w, orig_h), TARGET_SIZE)

    # 分批處理
    for batch_idx in range(total_batches):
        start = batch_idx * BATCH_SIZE
        batch = images[start : start + BATCH_SIZE]

        # 轉 PIL -> np.ndarray
        batch_arrays = [np.array(pil.convert("RGB")) for _, pil in batch]

        # 等比縮放 + 黑邊填充 (僅在記憶體中)
        resized_results = batch_uniform_resize(
            batch_arrays,
            target_size=TARGET_SIZE,
            
        )
        resized_images = [r.resized_image for r in resized_results]

        # YOLO 預測
        yolo_outputs = predictor.predict(resized_images, **yolo_config)

        # 逐張分析
        for idx_in_batch, (filename, _) in enumerate(batch):
            # 若 YOLO 回傳少於預期，補上 None
            yolo_out = yolo_outputs[idx_in_batch] if idx_in_batch < len(yolo_outputs) else None

            if yolo_out is None:
                results.append({
                    'filename': filename,
                    'result': None,
                    'stats': {'error': '預測失敗'},
                    'success': False
                })
                continue

            # 取最高信心的分割 mask
            _, confidence, mask = predictor.extract_max_confidence_segment(yolo_out)
            if mask is None:
                results.append({
                    'filename': filename,
                    'result': None,
                    'stats': {'error': '未檢測到分割遮罩'},
                    'success': False
                })
                continue

            # 在 resized 圖上提取直線
            resized_img = resized_images[idx_in_batch]
            verticals = extractor.extract_vertical_lines_from_mask(
                img=resized_img,
                mask=mask,
                region=region,
                sample_interval=line_config['sample_interval'],
                gradient_search_top=line_config['gradient_search_top'],
                gradient_search_bottom=line_config['gradient_search_bottom'],
                keep_ratio=(None if region else line_config['keep_ratio'])
            )

            # 視覺化直線
            vis_img = visualizer.visualize_vertical_lines_with_mm(
                resized_img,
                verticals,
                pixel_size_mm=pixel_size_mm,
                line_color=vis_config['line_color'],
                line_thickness=vis_config['line_thickness'],
                line_alpha=vis_config['line_alpha'],
                display_labels=vis_config['display_labels']
            )

            # 計算長度統計 (mm)
            lengths = [abs(y2 - y1) * pixel_size_mm for _, y1, y2 in verticals]
            stats = {
                'confidence': float(confidence),
                'num_lines': len(verticals),
                'mean_length': float(np.mean(lengths)) if lengths else 0.0,
                'std_length':   float(np.std(lengths)) if lengths else 0.0,
                'max_length':   float(np.max(lengths)) if lengths else 0.0,
                'min_length':   float(np.min(lengths)) if lengths else 0.0,
            }

            # 轉回 PIL Image
            vis_img = Image.fromarray(vis_img)
            
            results.append({
                'filename': filename,
                'result': vis_img,
                'stats': stats,
                'success': True
            })

    return results