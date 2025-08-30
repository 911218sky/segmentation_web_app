from typing import List, Tuple, Optional
import numpy as np
import cv2
from config import LINE_CONFIG

class LineExtractor:
    """
    從血管分割遮罩產生垂直線，
    並利用原始影像的灰階梯度，讓線貼齊血管壁。
    支援區域限制功能。
    """
    clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(16, 16))
    
    def extract_vertical_lines_from_mask(
        self,
        img: np.ndarray,
        mask: np.ndarray,
        sample_interval: int = 5,
        gradient_search_top: int = 5,
        gradient_search_bottom: int = 5,
        keep_ratio: Optional[float] = 0.3,
        region: Optional[Tuple[int, int, int, int]] = None,
        apply_smoothing: bool = True,
        smooth_window_size: int = LINE_CONFIG['window_size'],
        smooth_threshold: float = LINE_CONFIG['threshold']
    ) -> List[Tuple[int, int, int]]:
        """
        從血管分割遮罩產生垂直線（x, top_y, bottom_y），並用原圖灰階的垂直梯度 (|dI/dy|) 使端點貼齊血管壁。
        此版本會在回傳前可選擇性地套用 _filter_with_smoothing 以移除高度突變的異常線。
        
        Args:
            img: 原始影像（BGR 或灰階）np.ndarray。
            mask: 與 img 同尺寸的二值或浮點遮罩（值域 0/1 或 0-255）。
            sample_interval: x 軸採樣間隔（整數 > 0）。
            gradient_search_top: 在粗略 top 向上/向內搜尋梯度強度的步數範圍（正整數）。
            gradient_search_bottom: 在粗略 bottom 向下/向內搜尋梯度強度的步數範圍（正整數）。
            keep_ratio: 若給定且 region 為 None，則只在寬度中間保留該比例區域進行抽樣。
            region: 可選 (x0, y0, w, h) 來處理局部 ROI（若提供，輸入會被裁切，輸出會轉回原始座標）。
            apply_smoothing: 是否在回傳前呼叫 _filter_with_smoothing 移除高度異常線。
            smooth_window_size: 套用平滑時的視窗大小（傳給 _filter_with_smoothing）。
            smooth_threshold: 平滑時的相對差門檻（傳給 _filter_with_smoothing）。

        Returns:
            List[Tuple[int, int, int]]: 每個元素為 (x, top_y, bottom_y)，座標為原始影像坐標（若有 region 則為全圖座標）。
        """
        if img is None or mask is None:
            return []

        # 若 region 提供，裁切 ROI（並記錄偏移）
        x0 = y0 = 0
        if region is not None:
            x0, y0, w_reg, h_reg = region
            img = img[y0:y0 + h_reg, x0:x0 + w_reg]
            mask = mask[y0:y0 + h_reg, x0:x0 + w_reg]

        # 灰階／CLAHE
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img.copy()
        gray = self.clahe.apply(gray)

        H, W = gray.shape[:2]

        # 二值化遮罩（支援 0/1 或 0-255）
        if mask.dtype == np.bool_:
            binm = mask.astype(np.uint8)
        else:
            binm = (mask > 127) if mask.max() > 1 else (mask > 0.5)
            binm = binm.astype(np.uint8)

        # 決定抽樣 x 範圍
        if keep_ratio is not None and region is None:
            border = int((1.0 - float(keep_ratio)) / 2.0 * W)
            xs = np.arange(border, W - border, sample_interval, dtype=np.int32)
        else:
            xs = np.arange(0, W, sample_interval, dtype=np.int32)

        if xs.size == 0:
            return []

        # 取出每個被抽樣列的遮罩（H x M）
        cols = binm[:, xs]
        has_mask = cols.any(axis=0)
        if not np.any(has_mask):
            return []

        xs = xs[has_mask]
        top0 = np.argmax(cols, axis=0)[has_mask]
        bot0 = H - 1 - np.argmax(np.flipud(cols), axis=0)[has_mask]

        # 計算垂直梯度的絕對值 |dI/dy|
        gy = cv2.Sobel(gray, cv2.CV_32F, dx=0, dy=1, ksize=3)
        gy = np.abs(gy)

        # 在每列的局部 window 中找最大梯度對應的 y（向量化）
        def best_y_around(y0s: np.ndarray, win: int, direction: int) -> np.ndarray:
            win = max(1, int(win))
            k = np.arange(0, win, dtype=np.int32)[None, :]
            offsets = (k if direction > 0 else -k)
            ys = y0s[:, None] + offsets
            ys = np.clip(ys, 0, H - 1)
            xs_mat = np.broadcast_to(xs[:, None], ys.shape)
            vals = gy[ys, xs_mat]
            idx = np.argmax(vals, axis=1)
            return ys[np.arange(ys.shape[0]), idx]

        top = best_y_around(top0.astype(np.int32), gradient_search_top, +1).astype(np.int32)
        bot = best_y_around(bot0.astype(np.int32), gradient_search_bottom, -1).astype(np.int32)

        # 合併成 (x, top, bot) 並將 region 偏移加回去（若有）
        lines_arr = np.stack([xs.astype(np.int32),
                            top.astype(np.int32),
                            bot.astype(np.int32)], axis=1)

        if region is not None:
            lines_arr[:, 0] += x0
            lines_arr[:, 1] += y0
            lines_arr[:, 2] += y0

        lines: List[Tuple[int, int, int]] = [tuple(map(int, row)) for row in lines_arr.tolist()]

        # 在這裡套用平滑過濾
        if apply_smoothing and len(lines) > 0:
            lines = LineExtractor._filter_with_smoothing(
                lines,
                window_size=smooth_window_size,
                threshold=smooth_threshold
            )
          
        return lines

    @staticmethod
    def _filter_with_smoothing(
        lines: List[Tuple[int, int, int]],
        window_size: int = 5,
        threshold: float = 0.2
    ) -> List[Tuple[int, int, int]]:
        """
        使用滑動視窗（moving average）來平滑並濾除異常線段。
        支援奇/偶 window_size；O(N) 前綴和實作。
        """
        if not lines or window_size <= 1:
            return list(lines)

        # (N, 3)
        arr = np.asarray(lines, dtype=np.int32)
        heights = (arr[:, 2] - arr[:, 1]).astype(np.float32)
        N = heights.size
        w = int(window_size)

        if N <= w:
            # 視窗 >= 資料長度時，不做過濾
            return [tuple(row) for row in arr.tolist()]

        # 移動平均（長度 N - w + 1）
        cumsum = np.cumsum(np.insert(heights, 0, 0.0))
        # shape: (N - w + 1,)
        ma = (cumsum[w:] - cumsum[:-w]) / float(w)

        # 不對稱 pad，確保中段長度與 ma 一致
        pad_left = w // 2
        # 奇數時與左邊相等；偶數時右邊少 1
        pad_right = w - pad_left - 1

        smoothed = np.empty_like(heights)
        smoothed[:pad_left] = ma[0]
        # 長度 = N - w + 1
        smoothed[pad_left: N - pad_right] = ma
        smoothed[N - pad_right:] = ma[-1]

        # 相對差距過濾
        denom = np.maximum(smoothed, 1e-6)
        rel_diff = np.abs(heights - smoothed) / denom
        keep_mask = rel_diff <= float(threshold)
        filtered = arr[keep_mask]

        return [tuple(map(int, row)) for row in filtered.tolist()]