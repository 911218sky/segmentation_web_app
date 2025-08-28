from collections import deque
from dataclasses import dataclass
from typing import Optional, Deque, List
import numpy as np

@dataclass
class StabilityConfig:
    """
    控制跨幀穩定度判斷的參數：
      - init_window：建立前段「穩定基線」所需的幀數
      - init_cv_max：前段變異係數(std/mean)上限，低於才視為穩定
      - win_size：時間滑動視窗大小，用於rolling median/MAD
      - z_thresh：以rolling MAD計算的魯棒z-score門檻
      - rel_tol：相對基線允許的相對變動幅度 (±20% → 0.20)
      - roc_abs_max：相鄰幀允許的絕對變化量（mm/幀）
      - consec_bad_stop：連續異常幀數達到此值就提前停止
      - require_baseline：是否必須先建立基線才開始嚴格判斷
    """
    init_window: int = 20
    init_cv_max: float = 0.08
    win_size: int = 15
    z_thresh: float = 3.5
    rel_tol: float = 0.20
    roc_abs_max: float = 3.0
    consec_bad_stop: int = 10
    require_baseline: bool = True


class SlidingStabilityFilter:
    """
    使用rolling median + MAD的魯棒檢測，搭配：
      - 對「前段穩定區」建立基線
      - 相對基線的允許變動範圍
      - 相鄰幀變化率限制
      - 連續異常提早停止
    """
    def __init__(self, cfg: StabilityConfig = StabilityConfig()):
        self.cfg = cfg
        self.buffer: Deque[float] = deque(maxlen=cfg.win_size)
        self.warmup: List[float] = []
        self.baseline: Optional[float] = None
        self.baseline_mad: Optional[float] = None
        self.last_valid: Optional[float] = None
        self.consec_bad = 0
        self.stopped = False

    @staticmethod
    def _mad(x: np.ndarray) -> float:
        med = np.median(x)
        return float(np.median(np.abs(x - med))) if x.size else 0.0

    def _try_build_baseline(self) -> None:
        if len(self.warmup) < self.cfg.init_window:
            return
        arr = np.asarray(self.warmup, dtype=float)
        m = np.mean(arr)
        s = np.std(arr)
        if m > 0 and (s / m) <= self.cfg.init_cv_max:
            self.baseline = float(np.median(arr))
            self.baseline_mad = self._mad(arr)
        # 無論是否建立成功，都避免暖身被後段拉歪
        self.warmup = self.warmup[-self.cfg.win_size:]

    def add(self, value_mm: float) -> bool:
        """
        回傳：
            True  -> 接受此幀（合理）
            False -> 拒絕此幀（不合理；若連續達上限會設 stopped=True）
        """
        if self.stopped:
            return False

        # 尚未有基線：先累積暖身以判定是否穩定
        if self.baseline is None:
            self.warmup.append(value_mm)
            self._try_build_baseline()
            if self.cfg.require_baseline:
                # 未建立基線前不嚴格剔除，但維持buffer及last_valid跟上
                self.buffer.append(value_mm)
                self.last_valid = value_mm
                return True
            # 若不強制基線，則直接落入後續檢查

        # 更新滑動緩衝
        self.buffer.append(value_mm)
        buf = np.asarray(self.buffer, dtype=float)
        roll_med = float(np.median(buf))
        roll_mad = self._mad(buf)
        robust_sigma = max(1.4826 * roll_mad, 1e-6)  # 防止除零

        # 魯棒 z-score
        z = abs(value_mm - roll_med) / robust_sigma
        if z > self.cfg.z_thresh:
            self.consec_bad += 1
            if self.consec_bad >= self.cfg.consec_bad_stop:
                self.stopped = True
            return False

        # 相對「基線」的範圍（須先建立基線）
        if self.baseline is not None:
            lo = self.baseline * (1 - self.cfg.rel_tol)
            hi = self.baseline * (1 + self.cfg.rel_tol)
            if not (lo <= value_mm <= hi):
                self.consec_bad += 1
                if self.consec_bad >= self.cfg.consec_bad_stop:
                    self.stopped = True
                return False

        # 相鄰幀變化率（mm/幀）
        if self.last_valid is not None:
            if abs(value_mm - self.last_valid) > self.cfg.roc_abs_max:
                self.consec_bad += 1
                if self.consec_bad >= self.cfg.consec_bad_stop:
                    self.stopped = True
                return False

        # 通過所有檢查
        self.consec_bad = 0
        self.last_valid = value_mm
        return True