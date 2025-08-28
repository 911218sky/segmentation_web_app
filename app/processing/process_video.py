from typing import Tuple, Union, Optional, Dict, List
from pathlib import Path

from utils.stability_filter import SlidingStabilityFilter, StabilityConfig
from config import (
    TARGET_FPS,
    OUTPUT_DIR,
    LINE_CONFIG,
    VISUALIZATION_CONFIG,
    YOLO_CONFIG,
)
from processing.line_extractor import LineExtractor
from processing.video_processor import VideoIntervalProcessor, IntervalStat
from visualizer import Visualizer
from yolo_predictor import YOLOPredictor

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
    stab = SlidingStabilityFilter(StabilityConfig(
        init_window=20,     # 前20幀用來建立穩定基線
        init_cv_max=0.08,   # 前段CV<8%算穩定
        win_size=15,
        z_thresh=3.5,
        rel_tol=0.20,       # 後段允許±20%相對基線
        roc_abs_max=3.0,    # 單幀跳動不可超過3 mm
        consec_bad_stop=10, # 連續10幀不合理就提前停止
        require_baseline=True
    ))
    
    processor = VideoIntervalProcessor(
        predictor=predictor,
        line_extractor=line_extractor,
        visualizer=visualizer,
        stability_filter=stab,
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