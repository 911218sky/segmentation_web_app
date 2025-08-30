from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import math

import cv2
import numpy as np

from config import * 
from utils.line_extractor import LineExtractor
from utils.canvas import convert_original_xywh_to_resized
from utils.ffmpeg_pipe import FFmpegPipe
from utils.image import batch_uniform_resize_cuda
from utils.stability_filter import SlidingStabilityFilter, StabilityConfig
from utils.visualizer import Visualizer
from utils.yolo_predictor import YOLOPredictor

@dataclass
class IntervalStat:
    """儲存單一時間區間的統計結果。"""
    start_s: float               # 區間起點（秒）
    end_s: float                 # 區間終點（秒）
    frame_count: int             # 此區間實際採樣並處理的幀數
    mean_of_means_mm: float      # 逐幀平均值（mm）再取平均 → 區間「平均值」
    max_of_means_mm: float       # 逐幀平均值（mm）中的最大值 → 區間「最大值」
    max_at_s: Optional[float]    # 最大值所對應的影片時間點（秒）；若無有效值則為 None
    file_path: Path              # 輸出影片路徑


def mm_mean_from_lines(lines, pixel_size_mm: float) -> float:
    """計算該幀所有垂直線長度（mm）的平均。"""
    if not lines:
        return 0.0
    lengths_px = [abs(y2 - y1) for _, y1, y2 in lines]
    return float(np.mean(lengths_px) * pixel_size_mm)


class VideoIntervalProcessor:
    """影片區間處理器：抽樣→批次推理→抽垂直線→時序穩定檢查→統計→輸出影片。"""

    def __init__(
        self,
        *,
        predictor: YOLOPredictor,
        line_extractor: LineExtractor,
        visualizer: Visualizer,
        stability_filter_config: Optional[StabilityConfig] = None,
        pixel_size_mm: float = 0.30,
        yolo_config: Optional[dict] = None,
        line_config: Optional[dict] = None,
        visualization_config: Optional[dict] = None,
        draw_overlay: bool = True,
        save_video: bool = True,
    ) -> None:
        """
        Args:
            predictor: YOLO 包裝器（需有 predict_frames / extract_max_confidence_segment）。
            line_extractor: 從分割遮罩中抽垂直線。
            visualizer: 視覺化工具（畫線與顯示均值）。
            stability_filter: 跨幀穩定度濾波器（可為 None）。
            pixel_size_mm: px→mm 的換算係數。
            yolo_config: YOLO 推論設定（device/half/conf/imgsz/batch 等）。
            line_config: 取線相關參數（sample_interval、gradient_*、keep_ratio）。
            visualization_config: 視覺化參數。
            draw_overlay: 是否在輸出影片上畫線與顯示均值。
        """
        self.predictor = predictor
        self.line_extractor = line_extractor
        self.visualizer = visualizer
        self.stability_filter_config = stability_filter_config
        self.pixel_size_mm = pixel_size_mm
        self.yolo_config = yolo_config
        self.line_config = line_config
        self.visualization_config = visualization_config
        self.draw_overlay = draw_overlay
        self.save_video = save_video
        self.batch_size: int = int(
            self.yolo_config.get("batch", BATCH_SIZE)
        )

        self.pixel_size_mm = float(pixel_size_mm)
        self.yolo_config = (yolo_config or {}).copy()

        # 強制 img size 與 TARGET_SIZE 一致（Ultralytics 接受list of np arrays）
        if "imgsz" not in self.yolo_config and "img_size" not in self.yolo_config:
            self.yolo_config["imgsz"] = max(TARGET_SIZE)

    # 單幀後處理：從 YOLO 結果取遮罩 → 抽垂直線 → 算 mm → （可選）畫在影像上
    def _frame_postprocess(
        self,
        frame: np.ndarray,
        result,
        region_resized: Optional[Tuple[int, int, int, int]] = None,
        stab: Optional[SlidingStabilityFilter] = None,
    ) -> Tuple[Optional[float], np.ndarray]:
        """
        注意：這裡的 frame 是 **已 letterbox 到 TARGET_SIZE 的影格**，
        region_resized 也應該在同一座標系（即 resize 後座標）。

        Returns:
            mean_mm: 該幀所有垂直線長度（mm）的平均；偵測不到時為 None
            frame_out: 可視化後影格（或原影格）
        """
        # 從 YOLO 結果中擷取「最高信心」的分割遮罩；假設遮罩與 frame 尺寸對齊
        _, _, mask = self.predictor.extract_max_confidence_segment(result)
        if mask is None:
            return None, frame

        lines = self.line_extractor.extract_vertical_lines_from_mask(
            img=frame,
            mask=mask,
            region=region_resized,
            sample_interval=self.line_config.get("sample_interval", LINE_CONFIG["sample_interval"]),
            gradient_search_top=self.line_config.get("gradient_search_top", LINE_CONFIG["gradient_search_top"]),
            gradient_search_bottom=self.line_config.get("gradient_search_bottom", LINE_CONFIG["gradient_search_bottom"]),
            keep_ratio=self.line_config.get("keep_ratio", LINE_CONFIG["keep_ratio"]) if region_resized is None else None,
        )
        if not lines:
            return None, frame

        # 跨幀穩定檢查
        mean_mm = mm_mean_from_lines(lines, pixel_size_mm=self.pixel_size_mm)
        if stab is not None and not stab.add(mean_mm):
            return None, frame

        # 視覺化
        if self.draw_overlay:
            frame_out = self.visualizer.visualize_vertical_lines_with_mm(
                frame,
                lines,
                pixel_size_mm=self.pixel_size_mm,
                line_color=self.visualization_config.get("line_color", VISUALIZATION_CONFIG["line_color"]),
                line_thickness=self.visualization_config.get("line_thickness", VISUALIZATION_CONFIG["line_thickness"]),
                line_alpha=self.visualization_config.get("line_alpha", VISUALIZATION_CONFIG["line_alpha"]),
                display_labels=self.visualization_config.get("display_labels", VISUALIZATION_CONFIG["display_labels"]),
            )
        else:
            frame_out = frame

        return mean_mm, frame_out

    # 依來源/目標 FPS 產生抽樣幀索引
    def _choose_sampled_indices(
        self,
        start_f: int,
        end_f: int,
        src_fps: float,
        target_fps: float
    ) -> List[int]:
        if target_fps <= 0:
            target_fps = src_fps
        if src_fps <= 0:
            src_fps = target_fps

        ratio = src_fps / target_fps
        if ratio <= 1.05:
            return list(range(start_f, end_f + 1))

        n = max(1, int(math.floor((end_f - start_f + 1) / ratio)))
        idxs = [int(round(start_f + i * ratio)) for i in range(n)]
        
        # 過濾掉超出區間的幀
        return [i for i in idxs if start_f <= i <= end_f]

    def process_video(
        self,
        video_path: Path,
        intervals: List[Tuple[float, float]] = [],
        target_fps: float = TARGET_FPS,
        output_dir: Path = OUTPUT_DIR,
        region: Optional[Tuple[int, int, int, int]] = None,
    ) -> Dict[str, IntervalStat]:
        """
        Args:
            video_path: 輸入影片路徑
            intervals: 一系列 (start_s, end_s) 秒數區間
            target_fps: 抽樣/輸出FPS。<=0 代表沿用原FPS
            output_dir: 每個區間輸出的影片與統計JSON存放位置
            region: (x, y, w, h) 在原始座標中的ROI；會自動換算到resize座標
        Returns:
            stats：每個區間的 IntervalStat 統計
        """

        output_dir.mkdir(parents=True, exist_ok=True)
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise RuntimeError(f"無法開啟影片: {video_path}")

        src_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        src_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        src_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        base = video_path.stem

        # 若有指定ROI，換算到letterbox後的座標系
        region_resized = None
        if region is not None:
            region_resized = convert_original_xywh_to_resized(region, (src_w, src_h), TARGET_SIZE)

        stats: Dict[str, IntervalStat] = {}

        # 逐一處理每個時間區間
        for k, (start_s, end_s) in enumerate(intervals, start=1):
            start_s = max(0.0, float(start_s))
            end_s = max(start_s, float(end_s))
            start_f = min(int(round(start_s * src_fps)), max(total_frames - 1, 0))
            end_f = min(int(round(end_s * src_fps)), max(total_frames - 1, 0))

            sampled = self._choose_sampled_indices(start_f, end_f, src_fps, target_fps)
            
            if self.stability_filter_config is not None:
                stab = SlidingStabilityFilter(self.stability_filter_config)
            else:
                stab = None

            # 這段輸出的影片 writer（解析度為 TARGET_SIZE）
            out_fps = target_fps if target_fps > 0 else src_fps
            out_path = output_dir / f"{base}_seg_{k}_{int(start_s)}-{int(end_s)}_{int(round(out_fps))}fps.mp4"
            pipe = None
            if self.save_video:
                pipe = FFmpegPipe(
                    str(out_path),
                    TARGET_SIZE[0],
                    TARGET_SIZE[1],
                    fps=out_fps,
                    preset="ultrafast",
                    crf=23,
                    pixel_format="bgr24"
                )

            frame_means: List[Tuple[int, float]] = []
            batch_frames: List[np.ndarray] = []
            batch_indices: List[int] = []

            # 批次送入 YOLO 推理並後處理（先用 GPU 等比縮放到 TARGET_SIZE）
            def flush_batch() -> None:
                nonlocal batch_frames, batch_indices, frame_means
                if not batch_frames:
                    return

                resized_results = batch_uniform_resize_cuda(
                    batch_frames,
                    target_size=TARGET_SIZE,
                )

                resized_frames = [r.resized_image for r in resized_results]
                predict_results = self.predictor.predict(resized_frames, **self.yolo_config)

                # 逐幀後處理與寫出（frame 是 resize 後的）
                for frm_resized, res, idx in zip(resized_frames, predict_results, batch_indices):
                    mean_mm, frame_out = self._frame_postprocess(
                        frm_resized,
                        res,
                        region_resized,
                        stab,
                    )
                    if mean_mm is not None:
                        frame_means.append((idx, mean_mm))
                    if pipe is not None:
                        pipe.write_frame_rgb_array(frame_out)

                batch_frames.clear()
                batch_indices.clear()

            # 高效讀幀（只在起點 seek，之後連續解碼）
            sampled_iter = iter(sampled)
            next_needed = next(sampled_iter, None)

            # 設定起點幀
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_f)
            cur_f = start_f

            # 若需要在區間內「異常連續太多就停止」
            while cur_f <= end_f and next_needed is not None:
                if stab is not None and stab.stopped:
                    break

                ok, frame = cap.read()
                if not ok or frame is None:
                    break

                if cur_f == next_needed:
                    batch_frames.append(frame)
                    batch_indices.append(cur_f)
                    if len(batch_frames) >= self.batch_size:
                        flush_batch()
                    next_needed = next(sampled_iter, None)

                cur_f += 1

            # 殘留送推理
            flush_batch()
            if pipe is not None:
                pipe.close()

            # 區間統計
            if frame_means:
                means_only = [m for _, m in frame_means]
                mean_of_means = float(np.mean(means_only))
                max_pos = int(np.argmax(means_only))
                max_of_means = float(means_only[max_pos])
                max_at_frame = frame_means[max_pos][0]
                max_at_s = float(max_at_frame / src_fps)
            else:
                mean_of_means = -1
                max_of_means = -1
                max_at_s = -1

            stats[f"interval_{k:02d}"] = IntervalStat(
                start_s=start_s,
                end_s=end_s,
                frame_count=len(sampled),
                mean_of_means_mm=mean_of_means,
                max_of_means_mm=max_of_means,
                max_at_s=max_at_s,
                file_path=out_path,
            )

        cap.release()
        return stats