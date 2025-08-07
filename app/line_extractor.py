from typing import List, Tuple
import numpy as np
import cv2
from config import LINE_EXTRACTION_CONFIG

class LineExtractor:
    """
    從血管分割遮罩產生垂直線，
    並利用原始影像的灰階梯度，讓線貼齊血管壁。
    支援區域限制功能。
    """

    @staticmethod
    def extract_vertical_lines_from_mask(
        img: np.ndarray,
        mask: np.ndarray,
        sample_interval: int = LINE_EXTRACTION_CONFIG['sample_interval'],
        gradient_search_top: int = LINE_EXTRACTION_CONFIG['gradient_search_top'],
        gradient_search_bottom: int = LINE_EXTRACTION_CONFIG['gradient_search_bottom'],
        keep_ratio: float = LINE_EXTRACTION_CONFIG['keep_ratio'],
        region: Tuple[int, int, int, int] = None  # (left, top, right, bottom)
    ) -> List[Tuple[int, int, int]]:
        if img is None or mask is None:
            return []

        # 如果指定了區域，先裁切圖片和遮罩
        if region is not None:
            left, top, right, bottom = region
            img = img[top:bottom, left:right]
            mask = mask[top:bottom, left:right]

        # 轉灰階
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img.copy()

        # 對比度增強 (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(16,16))
        enhanced_gray = clahe.apply(gray)

        # 遮罩二值化
        binary = (mask > 127) if mask.max() > 1 else (mask > 0.5)
        _, w = binary.shape
        lines: List[Tuple[int, int, int]] = []

        # 計算 x 軸採樣範圍
        border = int((1.0 - keep_ratio) / 2 * w)
        x_start, x_end = border, w - border

        for x in range(x_start, x_end, sample_interval):
            # 獲取二值化圖片中 x 軸的 y 座標
            ys = np.where(binary[:, x])[0]
            if ys.size == 0:
                continue

            rough_min, rough_max = ys.min(), ys.max()

            # 向上搜索
            top_y = LineExtractor._search_max_contrast(
                enhanced_gray, x, rough_min, +1, gradient_search_top
            )
            # 向下搜索
            bottom_y = LineExtractor._search_max_contrast(
                enhanced_gray, x, rough_max, -1, gradient_search_bottom
            )

            if top_y is None:
                top_y = rough_min
            if bottom_y is None:
                bottom_y = rough_max

            # 如果指定了區域，需要調整座標回原始圖片座標系
            if region is not None:
                left, top, _, _ = region
                lines.append((x + left, int(top_y) + top, int(bottom_y) + top))
            else:
                lines.append((x, int(top_y), int(bottom_y)))

        # 平滑過濾
        lines = LineExtractor._filter_with_smoothing(lines,
                                                    window_size=LINE_EXTRACTION_CONFIG['window_size'], 
                                                    threshold=LINE_EXTRACTION_CONFIG['threshold'])
        return lines

    @staticmethod
    def _search_max_contrast(
        gray: np.ndarray,
        x: int,
        start_y: int,
        direction: int,
        max_step: int
    ) -> int:
        h = gray.shape[0]
        prev_val = gray[start_y, x]
        best_y, best_diff = None, 0

        for step in range(1, max_step + 1):
            y = start_y + direction * step
            if y < 0 or y >= h:
                break
            diff = abs(int(gray[y, x]) - int(prev_val))
            if diff > best_diff:
                best_diff = diff
                best_y = y
            prev_val = gray[y, x]

        return best_y if best_y is not None else start_y
  
    @staticmethod
    def _filter_with_smoothing(
        lines: List[Tuple[int, int, int]], 
        window_size: int = 5, 
        threshold: float = 0.2
    ) -> List[Tuple[int, int, int]]:
        """
        使用滑動視窗平滑過濾
        """
        if len(lines) <= window_size:
            return lines

        # 提取高度序列
        heights = [bottom - top for _, top, bottom in lines]
        
        # 計算滑動平均
        smoothed_heights = []
        half_window = window_size // 2
        
        for i in range(len(heights)):
            start_idx = max(0, i - half_window)
            end_idx = min(len(heights), i + half_window + 1)
            window_heights = heights[start_idx:end_idx]
            smoothed_heights.append(np.mean(window_heights))

        # 過濾偏差過大的線條
        filtered_lines = []
        for i, (line, original_height, smooth_height) in enumerate(zip(lines, heights, smoothed_heights)):
            relative_diff = abs(original_height - smooth_height) / smooth_height
            if relative_diff <= threshold:
                filtered_lines.append(line)

        return filtered_lines