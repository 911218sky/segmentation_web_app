import sys
from pathlib import Path
from typing import Optional, Tuple, Any
import numpy as np

# 添加父目錄到路徑
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent.parent
sys.path.insert(0, str(parent_dir))

from yolov12.ultralytics import YOLO


class YOLOPredictor:
    """YOLO預測器類別"""
    
    def __init__(self, weights_path: Path):
        """
        初始化YOLO預測器
        
        Args:
            weights_path: 模型權重文件路徑
        """
        self.model = YOLO(str(weights_path), task="segment")
    
    def predict(self, source_dir: Path, **kwargs) -> Any:
        """
        執行預測
        
        Args:
            source_dir: 圖片源目錄
            **kwargs: YOLO預測參數
        
        Returns:
            預測結果
        """
        return self.model.predict(
            task="segment",
            source=str(source_dir),
            **kwargs
        )
    
    @staticmethod
    def extract_max_confidence_segment(result) -> Tuple[Optional[np.ndarray], Optional[float], Optional[np.ndarray]]:
        """
        從YOLO預測結果中提取最高信心度的檢測區域和分割遮罩
        
        Args:
            result: YOLO預測結果
        
        Returns:
            (邊界框, 信心度, 分割遮罩) 的元組
        """
        if len(result.boxes) == 0:
            print("沒有檢測到任何物體")
            return None, None, None
        
        # 提取邊界框和信心度分數
        boxes = result.boxes.xyxy.cpu().numpy()
        confidences = result.boxes.conf.cpu().numpy()
        
        # 找到最高信心度的索引
        max_conf_index = confidences.argmax()
        
        # 提取最高信心度的結果
        max_conf_box = boxes[max_conf_index]
        max_confidence = confidences[max_conf_index]
        
        # 提取對應的分割遮罩
        if hasattr(result, 'masks') and result.masks is not None:
            max_conf_mask = result.masks.data[max_conf_index].cpu().numpy()
        else:
            max_conf_mask = None
            print("沒有找到分割遮罩數據")
        
        return max_conf_box, max_confidence, max_conf_mask