from typing import Tuple, Union, Optional, Dict, List
from pathlib import Path

from utils.stability_filter import StabilityConfig
from config import (
    TARGET_FPS,
    OUTPUT_DIR,
    LINE_CONFIG,
    VISUALIZATION_CONFIG,
    YOLO_CONFIG,
)
from .video_Interval_processor import VideoIntervalProcessor, IntervalStat
from utils.line_extractor import LineExtractor
from utils.visualizer import Visualizer
from utils.yolo_predictor import YOLOPredictor

def process_video(
    predictor: YOLOPredictor,
    video_path: Path,
    pixel_size_mm: float = 0.30,
    conf_threshold: float = 0.25,
    target_fps: float = TARGET_FPS,
    output_dir: Path = OUTPUT_DIR,
    # (x, y, w, h)
    region: Optional[Tuple[int, int, int, int]] = None,
    line_config: Union[dict, None] = None,
    vis_config: Union[dict, None] = None,
    intervals: List[Tuple[float, float]] = [(75, 100)],
    draw_overlay: bool = True,
)-> Dict[str, IntervalStat]:
    """批次處理多張圖片"""
    if line_config is None:
        line_config = LINE_CONFIG.copy()
    if vis_config is None:
        vis_config = VISUALIZATION_CONFIG.copy()
    
    # 獲取 yolo 配置 並覆蓋 conf 參數
    yolo_config = YOLO_CONFIG.copy()
    yolo_config['conf'] = conf_threshold
    
    line_extractor = LineExtractor()
    visualizer = Visualizer()
    stab_config = StabilityConfig()
    
    processor = VideoIntervalProcessor(
        predictor=predictor,
        line_extractor=line_extractor,
        visualizer=visualizer,
        stability_filter_config=stab_config,
        pixel_size_mm=pixel_size_mm,
        yolo_config=yolo_config,
        visualization_config=vis_config,
        line_config=line_config,
        draw_overlay=draw_overlay,
    )
    
    stats = processor.process_video(
        video_path=video_path,
        target_fps=target_fps,
        output_dir=output_dir,
        intervals=intervals,
        region=region,
    )
    
    return stats