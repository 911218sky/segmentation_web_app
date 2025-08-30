from collections import deque
from dataclasses import dataclass
from typing import Optional, Deque, List
import bisect
import math

@dataclass
class StabilityConfig:
    """
    參數說明
    ----------
    init_window : int = 10
        暖身幀數（建立「穩定基線」用）。稍微縮短，讓早期就能開始判斷。
    init_cv_max : float = 0.15
        暖身期的變異係數上限（CV=std/mean）。放寬到 15%，較容易建立基線。
    win_size : int = 9
        滾動視窗大小（幀）。略小一點，反應更靈敏、不會過度平滑。
    z_thresh : float = 3.5
        魯棒 z-score 門檻。提高到 5，較不易把正常波動當成離群。
    rel_tol : float = 0.2
        相對基線允許 ±20% 波動，放寬不易誤殺。
    roc_abs_max : float = 3.0
        相鄰兩幀最大變化量（mm/幀）。預設放大；若你有「每秒 mm」概念，建議在程式中依有效 FPS 改寫：
        roc_abs_max = 12.0 / eff_fps  # 例如允許每秒 12 mm
    consec_bad_stop : int = 1000000000
        連續異常幀達此值才停機。預設極大，避免誤停（外層可改成「軟濾波」不中斷）。
    require_baseline : bool = True
        必須先建立基線才開始嚴格判斷；暖身期基本不剔除。
    """
    init_window: int = 10
    init_cv_max: float = 0.08
    win_size: int = 9
    z_thresh: float = 3.5
    rel_tol: float = 0.2
    roc_abs_max: float = 3.0
    consec_bad_stop: int = 1_000_000_000
    require_baseline: bool = True

class SlidingStabilityFilter:
    """
    快速版穩定度濾波：
      - 視窗中位數：deque + 排序列表（插入/刪除 O(log w)，取中位 O(1)）
      - 視窗 MAD：每幀對長度 w 的小列表重算一次（w 默認 15，成本極低）
      - 暖身基線：Welford（O(1) 更新），CV 判定是否建立基線
      - 其餘規則：魯棒 z-score、相對基線容忍、相鄰幀 ROC、連續異常停
    與原介面相容：add(value_mm)->bool, attrs: baseline/last_valid/stopped...
    """

    def __init__(self, cfg: StabilityConfig = StabilityConfig()):
        self.cfg = cfg
        self.win: int = max(3, int(cfg.win_size))

        # 視窗資料
        self._dq: Deque[float] = deque(maxlen=self.win)
        self._sorted: List[float] = []  # 維持排序，用於 O(1) 取中位

        # 暖身（Welford）
        self._warm_n = 0
        self._warm_mean = 0.0
        self._warm_M2 = 0.0  # 累積平方和差，用於 var

        # 基線
        self.baseline: Optional[float] = None
        self.baseline_mad: Optional[float] = None

        # 其他狀態
        self.last_valid: Optional[float] = None
        self.consec_bad = 0
        self.stopped = False

    @staticmethod
    def _median_from_sorted(arr: List[float]) -> float:
        n = len(arr)
        mid = n // 2
        if n % 2:
            return float(arr[mid])
        return 0.5 * (arr[mid - 1] + arr[mid])

    @staticmethod
    def _mad_from_window(vals: List[float], median: float) -> float:
        # w 很小（~15），直接排序 deviations 即可
        dev = [abs(v - median) for v in vals]
        dev.sort()
        n = len(dev)
        mid = n // 2
        return float(dev[mid] if n % 2 else 0.5 * (dev[mid - 1] + dev[mid]))

    def _insert_sorted(self, x: float):
        bisect.insort(self._sorted, x)

    def _remove_sorted(self, x: float):
        i = bisect.bisect_left(self._sorted, x)
        # 保守檢查（浮點可能有極微小誤差）
        if i < len(self._sorted) and abs(self._sorted[i] - x) <= 1e-12:
            self._sorted.pop(i)
        else:
            # 找最近值移除（極少發生）
            if self._sorted:
                self._sorted.pop(min(i, len(self._sorted) - 1))

    def _warm_update(self, x: float):
        # Welford O(1)
        self._warm_n += 1
        delta = x - self._warm_mean
        self._warm_mean += delta / self._warm_n
        self._warm_M2 += delta * (x - self._warm_mean)

    def _try_build_baseline(self):
        if self.baseline is not None:
            return
        if self._warm_n < self.cfg.init_window:
            return
        # CV 判定
        var = self._warm_M2 / max(self._warm_n - 1, 1)
        std = math.sqrt(max(var, 0.0))
        mean = self._warm_mean
        cv = std / mean if mean > 0 else float("inf")
        if mean > 0 and cv <= self.cfg.init_cv_max:
            # 用目前視窗的中位數/MAD 作為基線（更魯棒）
            if self._sorted:
                med = self._median_from_sorted(self._sorted)
                mad = self._mad_from_window(list(self._dq), med)
            else:
                med = mean
                mad = 0.0
            self.baseline = float(med)
            self.baseline_mad = float(mad)
        # 暖身結束即可，不再累積（行為與原版相當）
        # 保留最近 win 個值在 deque/sorted 即可

    def add(self, value_mm: float) -> bool:
        """
        回傳：
          True  -> 接受此幀（合理）
          False -> 拒絕此幀（不合理；若連續達上限會設 stopped=True）
        """
        if self.stopped:
            return False

        # 先維持視窗（需要先知道被擠掉誰）
        popped = None
        if len(self._dq) == self.win:
            popped = self._dq[0]  # 即將被擠掉的值
        self._dq.append(value_mm)
        self._insert_sorted(value_mm)
        if popped is not None:
            self._remove_sorted(popped)

        # 暖身
        if self.baseline is None:
            self._warm_update(value_mm)
            self._try_build_baseline()
            if self.cfg.require_baseline:
                # 暖身期不嚴格剔除；仍更新 last_valid 以便 ROC 判定
                self.last_valid = value_mm
                return True
            # 若不強制基線，落入後續檢查

        # 取得視窗中位數/MAD（w 很小，這裡成本極低）
        median = self._median_from_sorted(self._sorted)
        mad = self._mad_from_window(list(self._dq), median)
        robust_sigma = max(1.4826 * mad, 1e-6)  # 防止除零

        # 魯棒 z-score
        z = abs(value_mm - median) / robust_sigma
        if z > self.cfg.z_thresh:
            self.consec_bad += 1
            if self.consec_bad >= self.cfg.consec_bad_stop:
                self.stopped = True
            return False

        # 相對基線（若已建立）
        if self.baseline is not None:
            lo = self.baseline * (1.0 - self.cfg.rel_tol)
            hi = self.baseline * (1.0 + self.cfg.rel_tol)
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