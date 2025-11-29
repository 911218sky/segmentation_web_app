import gc
import os
import sys
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union

import cv2
import numpy as np
import torch
from PIL import Image

# 添加父目錄到路徑
current_dir = Path(__file__).resolve().parent.parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

from yolov13.ultralytics import YOLO

class YOLOPredictor:
    """YOLO預測器類別"""
    
    def __init__(self, weights_path: Path):
        """
        初始化YOLO預測器
        
        Args:
            weights_path: 模型權重文件路徑
        """
        self.model = YOLO(str(weights_path), task="segment")
    
    def clear_cache(self):
        if torch.cuda.is_available():
            torch.cuda.synchronize()
            torch.cuda.empty_cache()
        gc.collect()
        
    def predict(
      self,
      source: Union[Path, str, np.ndarray, list],
      task: str = "segment",
      to_cpu: bool = True,
      **kwargs
    ) -> List[Any]:
        def to_model_input(x):
            # 保留 path/str 原樣（模型會讀取檔案路徑）
            if isinstance(x, (Path, os.PathLike, str)):
                return str(x)
            # np.ndarray 直接回傳
            if isinstance(x, np.ndarray):
                return x
            # PIL Image -> 轉成 BGR np.ndarray（若你的 model 需要 BGR）
            if isinstance(x, Image.Image):
                return cv2.cvtColor(np.array(x), cv2.COLOR_RGB2BGR)
            raise TypeError(f"Unsupported list element type: {type(x)}")

        if isinstance(source, list):
            src_arg = [to_model_input(x) for x in source]
        elif isinstance(source, (Path, os.PathLike)):
            src_arg = str(source)
        elif isinstance(source, str):
            src_arg = source
        elif isinstance(source, np.ndarray):
            src_arg = source
        else:
            raise TypeError(f"Unsupported type for source: {type(source)}. Expect Path, str, np.ndarray, or list[...]")

        with torch.inference_mode():
            results_iter = self.model.predict(
                task=task, source=src_arg, **kwargs
            )
            res = results_iter
            if isinstance(res, (list, tuple)):
                res = list(res)
            else:
                res = [res]
            if to_cpu:
                res = [r.cpu() if hasattr(r, "cpu") else r for r in res]
            return res
        
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
            # print("沒有檢測到任何物體")
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